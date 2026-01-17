#!/usr/bin/env python3

import requests
import json

API_KEY = "757133d0bd9646cf8e96b4e9377795e5"
STATION = "940GZZLUHWY"
LINE = "piccadilly"

print("=" * 60)
print("CHECKING PICCADILLY LINE STATUS")
print("=" * 60)

# Check line status first
status_url = f"https://api.tfl.gov.uk/Line/{LINE}/Status"
status_params = {"app_key": API_KEY}

status_response = requests.get(status_url, params=status_params)
status_data = status_response.json()

for line in status_data:
    print(f"\nLine: {line['name']}")
    for status in line['lineStatuses']:
        print(f"Status: {status['statusSeverityDescription']}")
        if 'reason' in status:
            print(f"Reason: {status['reason']}")
        if 'disruption' in status:
            print(f"Disruption: {status['disruption']}")

print("\n" + "=" * 60)
print("CHECKING ARRIVALS AT HOLLOWAY ROAD")
print("=" * 60)

# Correct endpoint: /StopPoint/{id}/Arrivals
arrivals_url = f"https://api.tfl.gov.uk/StopPoint/{STATION}/Arrivals"
arrivals_params = {"app_key": API_KEY}

print(f"\nURL: {arrivals_url}\n")

arrivals_response = requests.get(arrivals_url, params=arrivals_params)
arrivals = arrivals_response.json()

print(f"Found {len(arrivals)} arrivals\n")

if len(arrivals) == 0:
    print("⚠️  NO TRAINS FOUND")
    print("\nPossible reasons:")
    print("- Engineering works (common on weekends)")
    print("- Reduced service on Saturday evenings")
    print("- Station closed")
    print("\nCheck TfL website: https://tfl.gov.uk/tube/status/")
else:
    print("=" * 60)
    for arrival in sorted(arrivals, key=lambda x: x['timeToStation'])[:10]:
        mins = arrival['timeToStation'] // 60
        direction = arrival.get('direction', 'Unknown')
        destination = arrival.get('destinationName', 'Unknown')
        platform = arrival.get('platformName', 'Unknown')
        towards = arrival.get('towards', 'Unknown')
        line_name = arrival.get('lineName', 'Unknown')
        
        print(f"\nLine: {line_name}")
        print(f"Destination: {destination}")
        print(f"Direction: {direction}")
        print(f"Towards: {towards}")
        print(f"Platform: {platform}")
        print(f"In: {mins} minutes")
        print("-" * 60)