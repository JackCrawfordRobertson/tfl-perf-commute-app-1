#!/usr/bin/env python3
"""
TEST Commute API - always active for testing.
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
    with open('/home/pi/commute-app/testing/config.test.json', 'r') as f:
        return json.load(f)

def get_journey_time(config):
    """Get journey time from TfL Journey Planner"""
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
    return config['tfl'].get('journey_time_minutes', 15)

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

def calculate_target_train(config, journey_mins):
    """
    Calculate the ideal train to catch based on arrival target.
    Returns the train time and when to leave home.
    """
    # Get arrival target (e.g., 08:25)
    arrival_target = config['commute'].get('arrival_target', '08:25')
    target_h, target_m = map(int, arrival_target.split(':'))

    now = datetime.now()
    target_time = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)

    # If target already passed today, use tomorrow
    if now > target_time:
        target_time += timedelta(days=1)

    # Work backwards: when must the train depart to arrive by target?
    ideal_train_departure = target_time - timedelta(minutes=journey_mins)

    # When to leave home to arrive at platform with buffer?
    walking_mins = config['commute'].get('walking_minutes', 9)
    platform_buffer = config['commute'].get('platform_buffer_minutes', 2)

    # Leave home time = train_departure - walking_time - platform_buffer
    leave_home_time = ideal_train_departure - timedelta(minutes=walking_mins + platform_buffer)

    # Calculate countdowns
    seconds_until_leave = (leave_home_time - now).total_seconds()
    seconds_until_train = (ideal_train_departure - now).total_seconds()

    return {
        'arrival_target': arrival_target,
        'target_train': ideal_train_departure.strftime('%H:%M'),
        'leave_home': leave_home_time.strftime('%H:%M'),
        'walking_mins': walking_mins,
        'journey_mins': journey_mins,
        'seconds_until_leave': int(seconds_until_leave),
        'minutes_until_leave': int(seconds_until_leave // 60),
        'seconds_until_train': int(seconds_until_train),
        'minutes_until_train': int(seconds_until_train // 60),
        'should_have_left': seconds_until_leave <= 0,
        'train_departed': seconds_until_train <= 0
    }

@app.route('/')
def home():
    return jsonify({"status": "ok", "endpoint": "/status", "mode": "TEST"})

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

    # Get journey time and calculate target train
    journey_mins = get_journey_time(config)
    commute = calculate_target_train(config, journey_mins)

    response = {
        'active': True,
        'schedule_status': schedule_status,
        'timestamp': datetime.now().isoformat(),
        'line': config['tfl']['line'].title(),
        'commute': commute
    }

    return jsonify(response)

if __name__ == '__main__':
    print("Starting TEST Commute API server on port 5001...")
    print("Access at http://<your-pi-ip>:5001/status")
    app.run(host='0.0.0.0', port=5001)
