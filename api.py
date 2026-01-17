#!/usr/bin/env python3
"""
Simple HTTP API server for commute data.
Run this alongside main.py to expose data for iPhone Scriptable widget.
"""

import os
from flask import Flask, jsonify
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('/home/pi/commute-app/.env')

app = Flask(__name__)

def load_config():
    with open('/home/pi/commute-app/config.json', 'r') as f:
        return json.load(f)

def get_journey_time(config):
    """Get journey time from TfL"""
    try:
        url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{config['tfl']['home_station']}/to/{config['tfl']['work_station']}"
        api_key = os.getenv('TFL_API_KEY', config['tfl'].get('api_key', ''))
        params = {"app_key": api_key}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'journeys' in data and len(data['journeys']) > 0:
            return data['journeys'][0]['duration']
    except:
        pass
    return config['tfl'].get('journey_time_minutes', 18)

def get_next_trains(config):
    """Get next trains from TfL API"""
    url = f"https://api.tfl.gov.uk/StopPoint/{config['tfl']['home_station']}/Arrivals"
    api_key = os.getenv('TFL_API_KEY', config['tfl'].get('api_key', ''))
    params = {"app_key": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        arrivals = response.json()

        line = config['tfl']['line']
        direction = config['tfl']['direction']

        filtered = [a for a in arrivals
                    if a.get('lineName', '').lower() == line.lower()
                    and direction in a.get('direction', '').lower()]
        sorted_trains = sorted(filtered, key=lambda x: x['timeToStation'])

        trains = []
        for train in sorted_trains[:5]:
            trains.append({
                'destination': train['destinationName'].replace(' Underground Station', ''),
                'platform': train.get('platformName', 'Unknown'),
                'minutes': train['timeToStation'] // 60,
                'seconds': train['timeToStation']
            })
        return trains
    except Exception as e:
        return []

def is_active_time(config):
    """Check if current time is within active schedule"""
    schedule = config.get('schedule', {})

    # Check day
    active_days = schedule.get('active_days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
    current_day = datetime.now().strftime('%A').lower()
    if current_day not in active_days:
        return False, f"Not a commute day ({current_day.title()})"

    # Check time window
    start_time = schedule.get('active_window_start', '07:00')
    end_time = schedule.get('active_window_end', '09:00')

    now = datetime.now()
    start_h, start_m = map(int, start_time.split(':'))
    end_h, end_m = map(int, end_time.split(':'))

    window_start = now.replace(hour=start_h, minute=start_m, second=0)
    window_end = now.replace(hour=end_h, minute=end_m, second=0)

    if now < window_start:
        return False, f"Before commute window (starts {start_time})"
    if now > window_end:
        return False, f"After commute window (ended {end_time})"

    return True, "Active"

def calculate_best_train(trains, config, journey_mins):
    """Find best train and when to leave"""
    if not trains:
        return None

    walking_mins = config['commute']['walking_minutes']
    buffer = config['commute']['buffer_minutes']
    work_start = config['commute']['work_start_time']

    work_hour, work_min = map(int, work_start.split(':'))
    work_time = datetime.now().replace(hour=work_hour, minute=work_min, second=0)

    if datetime.now() > work_time:
        work_time += timedelta(days=1)

    for train in trains:
        train_depart_time = datetime.now() + timedelta(seconds=train['seconds'])
        arrival_at_work = train_depart_time + timedelta(minutes=journey_mins)

        if arrival_at_work <= work_time:
            leave_home_time = train_depart_time - timedelta(minutes=walking_mins + buffer)
            time_until_leave = (leave_home_time - datetime.now()).total_seconds()

            return {
                'train': train,
                'train_departs': train_depart_time.strftime('%H:%M'),
                'leave_time': leave_home_time.strftime('%H:%M'),
                'countdown_seconds': int(time_until_leave),
                'countdown_minutes': int(time_until_leave // 60),
                'arrival_at_work': arrival_at_work.strftime('%H:%M')
            }

    return None

@app.route('/')
def home():
    return jsonify({"status": "ok", "endpoint": "/status"})

@app.route('/status')
def status():
    config = load_config()

    # Check if within active schedule
    is_active, schedule_status = is_active_time(config)

    if not is_active:
        return jsonify({
            'active': False,
            'schedule_status': schedule_status,
            'timestamp': datetime.now().isoformat()
        })

    # Get data
    journey_mins = get_journey_time(config)
    trains = get_next_trains(config)
    best = calculate_best_train(trains, config, journey_mins)

    response = {
        'active': True,
        'schedule_status': schedule_status,
        'timestamp': datetime.now().isoformat(),
        'line': config['tfl']['line'].title(),
        'work_start': config['commute']['work_start_time'],
        'journey_mins': journey_mins,
        'trains': trains[:3],
        'best_train': best
    }

    return jsonify(response)

if __name__ == '__main__':
    print("Starting Commute API server on port 5000...")
    print("Access at http://<your-pi-ip>:5000/status")
    app.run(host='0.0.0.0', port=5000)
