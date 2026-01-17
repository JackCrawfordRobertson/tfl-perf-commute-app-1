import requests
from datetime import datetime

print("✅ Python works!")
print(f"📅 Current time: {datetime.now()}")

# Test internet connection
try:
    response = requests.get("https://api.tfl.gov.uk/")
    print(f"✅ Internet works! TfL API is reachable (status: {response.status_code})")
except Exception as e:
    print(f"❌ Error: {e}")
