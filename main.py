#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timedelta
from telegram import Bot
import asyncio

class CommutePredictor:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.tfl_key = self.config['tfl']['api_key']
        self.station_id = self.config['tfl']['home_station']
        self.line = self.config['tfl']['line']
        self.direction = self.config['tfl']['direction']
        self.work_station = self.config['tfl']['work_station']
        
        self.walking_mins = self.config['commute']['walking_minutes']
        self.work_start = self.config['commute']['work_start_time']
        self.buffer = self.config['commute']['buffer_minutes']
        
        # Get realistic journey time from TfL on startup
        self.journey_mins = self.get_journey_time()
        
        # Telegram setup (optional)
        try:
            self.bot = Bot(token=self.config['telegram']['bot_token'])
            self.chat_id = self.config['telegram']['chat_id']
            self.telegram_enabled = True
        except:
            self.telegram_enabled = False
        
        self.last_alert_time = None
    
    def get_journey_time(self):
        """Get realistic journey time from TfL Journey Planner"""
        try:
            url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{self.station_id}/to/{self.config['tfl']['work_station']}"
            params = {"app_key": self.tfl_key}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'journeys' in data and len(data['journeys']) > 0:
                # Get the fastest journey
                journey = data['journeys'][0]
                duration_mins = journey['duration']
                
                print(f"📊 TfL Journey Planner: {duration_mins} mins total journey time")
                
                # Show journey breakdown
                if 'legs' in journey:
                    print(f"📍 Journey breakdown:")
                    for i, leg in enumerate(journey['legs'], 1):
                        mode = leg.get('mode', {}).get('name', 'Unknown')
                        duration = leg.get('duration', 0)
                        if 'departurePoint' in leg and 'arrivalPoint' in leg:
                            from_stop = leg['departurePoint'].get('commonName', 'Unknown')
                            to_stop = leg['arrivalPoint'].get('commonName', 'Unknown')
                            print(f"   {i}. {from_stop} → {to_stop}")
                            print(f"      {mode}, {duration} mins")
                
                print()
                return duration_mins
            else:
                # Fallback to config
                fallback = self.config['tfl'].get('journey_time_minutes', 18)
                print(f"⚠️  Couldn't get journey time from TfL, using config: {fallback} mins\n")
                return fallback
                
        except Exception as e:
            fallback = self.config['tfl'].get('journey_time_minutes', 18)
            print(f"⚠️  Journey planner error: {e}")
            print(f"   Using config fallback: {fallback} mins\n")
            return fallback
        
    def get_next_trains(self):
        """Get next trains from TfL API"""
        url = f"https://api.tfl.gov.uk/StopPoint/{self.station_id}/Arrivals"
        params = {"app_key": self.tfl_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            arrivals = response.json()
            
            # Filter by LINE and direction, then sort by time
            filtered = [a for a in arrivals 
                        if a.get('lineName', '').lower() == self.line.lower() 
                        and self.direction in a.get('direction', '').lower()]
            sorted_trains = sorted(filtered, key=lambda x: x['timeToStation'])
            
            trains = []
            for train in sorted_trains[:5]:
                mins = train['timeToStation'] // 60
                secs = train['timeToStation']
                destination = train['destinationName']
                platform = train.get('platformName', 'Unknown')
                
                trains.append({
                    'destination': destination,
                    'platform': platform,
                    'minutes': mins,
                    'seconds': secs
                })
            
            return trains
            
        except Exception as e:
            print(f"❌ Error getting trains: {e}")
            return []
    
    def calculate_best_train(self, trains):
        """Find the best train to catch and when to leave"""
        if not trains:
            return None
        
        # Get work start time
        work_hour, work_min = map(int, self.work_start.split(':'))
        work_time = datetime.now().replace(hour=work_hour, minute=work_min, second=0)
        
        # If work time has passed, use tomorrow
        if datetime.now() > work_time:
            work_time += timedelta(days=1)
        
        for train in trains:
            # When does this train depart?
            train_depart_time = datetime.now() + timedelta(seconds=train['seconds'])
            
            # When do you arrive at work? (train depart + journey time)
            arrival_at_work = train_depart_time + timedelta(minutes=self.journey_mins)
            
            # Does this get you there on time?
            if arrival_at_work <= work_time:
                # When should you leave home?
                leave_home_time = train_depart_time - timedelta(minutes=self.walking_mins + self.buffer)
                
                # How long until you need to leave?
                time_until_leave = (leave_home_time - datetime.now()).total_seconds()
                
                return {
                    'train': train,
                    'train_departs': train_depart_time,
                    'leave_time': leave_home_time,
                    'countdown_seconds': int(time_until_leave),
                    'countdown_minutes': int(time_until_leave // 60),
                    'arrival_at_work': arrival_at_work
                }
        
        # No suitable train found (all too late)
        return None
    
    async def send_notification(self, message):
        """Send Telegram notification"""
        if not self.telegram_enabled:
            return
            
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            print(f"📱 Notification sent")
        except Exception as e:
            print(f"⚠️  Notification error: {e}")
    
    async def run(self):
        """Main loop - runs continuously"""
        print("🚇 Commute Predictor")
        print(f"📍 From: {self.station_id}")
        print(f"📍 To: {self.work_station}")
        print(f"🚶 Walking: {self.walking_mins} mins")
        print(f"🚇 Journey: {self.journey_mins} mins")
        print(f"🏢 Work start: {self.work_start}")
        print("=" * 60)
        print()
        
        while True:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                
                # Get next trains
                trains = self.get_next_trains()
                
                if not trains:
                    print(f"[{current_time}] ⚠️  No {self.line} line trains - checking in 30s...")
                    time.sleep(30)
                    continue
                
                # Find best train to catch
                best = self.calculate_best_train(trains)
                
                # Display status
                print(f"\n{'='*60}")
                print(f"[{current_time}] {self.line.upper()} LINE - Next Trains:")
                print(f"{'='*60}")
                
                for i, train in enumerate(trains[:3], 1):
                    dest_short = train['destination'].replace(' Underground Station', '')
                    marker = "🎯" if best and i == 1 else "  "
                    print(f"{marker} {dest_short}")
                    print(f"   Departs: {train['minutes']} min | Platform: {train['platform']}")
                
                if best:
                    print(f"\n{'─'*60}")
                    
                    mins = best['countdown_minutes']
                    secs = best['countdown_seconds'] % 60
                    
                    if best['countdown_seconds'] <= 0:
                        # TIME TO GO!
                        print(f"🚨 LEAVE NOW! 🚨")
                        print(f"")
                        print(f"Train departs:  {best['train_departs'].strftime('%H:%M')}")
                        print(f"Arrive at work: {best['arrival_at_work'].strftime('%H:%M')}")
                        
                        # Send alert (only once per minute)
                        current_minute = now.strftime("%H:%M")
                        if self.last_alert_time != current_minute:
                            # Compact one-line notification
                            message = f"🚶 LEAVE NOW! Train {best['train_departs'].strftime('%H:%M')} → Arrive {best['arrival_at_work'].strftime('%H:%M')}"
                            
                            await self.send_notification(message)
                            self.last_alert_time = current_minute
                    
                    elif mins <= 15:
                        # Show countdown
                        print(f"⏳ LEAVE IN: {mins}m {secs}s")
                        print(f"")
                        print(f"Catch train at:  {best['train_departs'].strftime('%H:%M')}")
                        print(f"Arrive at work:  {best['arrival_at_work'].strftime('%H:%M')}")
                    
                    else:
                        # Plenty of time
                        print(f"✅ {mins} minutes until you should leave")
                        print(f"   Train: {best['train_departs'].strftime('%H:%M')} → Arrive: {best['arrival_at_work'].strftime('%H:%M')}")
                
                else:
                    print(f"\n⚠️  No trains get you to work by {self.work_start}")
                    print(f"   All trains arrive after your start time")
                
                # Wait 30 seconds before checking again
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n\n👋 Stopping...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Retrying in 30 seconds...")
                time.sleep(30)

if __name__ == "__main__":
    import sys
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    print(f"📁 Config: {config_file}\n")
    
    predictor = CommutePredictor(config_file)
    asyncio.run(predictor.run())