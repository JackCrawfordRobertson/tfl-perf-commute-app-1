#!/usr/bin/env python3

import requests
import json

API_KEY = "757133d0bd9646cf8e96b4e9377795e5"

def search_station(search_term):
    """Search for tube stations and get detailed stop points"""
    # First get the hub
    url = f"https://api.tfl.gov.uk/StopPoint/Search/{search_term}"
    params = {"modes": "tube", "app_key": API_KEY}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "matches" in data and len(data['matches']) > 0:
        station = data["matches"][0]
        station_id = station['id']
        
        print(f"\nFound: {station['name']}")
        print(f"Hub ID: {station_id}\n")
        
        # Now get the actual stop points (platforms)
        detail_url = f"https://api.tfl.gov.uk/StopPoint/{station_id}"
        detail_params = {"app_key": API_KEY}
        
        detail_response = requests.get(detail_url, params=detail_params)
        detail_data = detail_response.json()
        
        if 'children' in detail_data:
            print("Stop Points (Platforms):")
            print("=" * 60)
            for child in detail_data['children']:
                # Only show tube platforms
                if child['id'].startswith('940GZZLU'):
                    lines = ', '.join([line['name'] for line in child.get('lines', [])])
                    print(f"\nID: {child['id']}")
                    print(f"Name: {child.get('commonName', 'Unknown')}")
                    print(f"Lines: {lines}")
                    print(f"Indicator: {child.get('indicator', 'N/A')}")
                    print("-" * 60)
        else:
            print("No platform details found")
    else:
        print("No stations found")

if __name__ == "__main__":
    search = input("Enter your tube station name: ")
    search_station(search)