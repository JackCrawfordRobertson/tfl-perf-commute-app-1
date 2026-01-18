# Commute App

A Raspberry Pi application that monitors TfL train times and tells you when to leave home to catch your train on time. Sends alerts via Telegram and exposes an API for iPhone widgets.

## Project Structure

```
commute-app/
├── main.py              # Main commute predictor app
├── api.py               # HTTP API server for iPhone widget (port 5000)
├── config.json          # Main configuration
├── .env                 # Environment variables (API keys - not in git)
├── .env.example         # Template for environment variables
├── .gitignore           # Git ignore rules
│
├── ios/
│   └── scriptable-widget.js    # iPhone Scriptable widget code
│
├── tools/
│   ├── debug_trains.py         # Debug utility for train arrivals
│   └── find_station.py         # Utility to find TfL station IDs
│
└── testing/
    ├── testit-api.py           # Test API server (port 5001, always active)
    └── config.test.json        # Test configuration (all days/hours)
```

## Setup

### 1. Install Dependencies

```bash
sudo apt install python3-flask python3-dotenv python3-telegram-bot
```

### 2. Configure Environment Variables

Copy the example env file and add your API keys:

```bash
cp .env.example .env
nano .env
```

Required variables:
- `TFL_API_KEY` - Get from https://api-portal.tfl.gov.uk/
- `TELEGRAM_BOT_TOKEN` - Create via @BotFather on Telegram
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

### 3. Configure Your Commute

Edit `config.json`:

```json
{
  "tfl": {
    "home_station": "940GZZLUHWY",      // Your home station ID
    "line": "piccadilly",                // Tube line
    "direction": "inbound",              // inbound or outbound
    "work_station": "940GZZLUBNK",       // Your work station ID
    "journey_time_minutes": 18           // Fallback journey time
  },
  "commute": {
    "walking_minutes": 9,                // Walk time to station
    "work_start_time": "08:30",          // When you need to arrive
    "buffer_minutes": 3,                 // Extra buffer time
    "check_interval_seconds": 5          // How often to check
  },
  "schedule": {
    "active_days": ["tuesday", "wednesday"],
    "active_window_start": "07:45",
    "active_window_end": "08:30"
  }
}
```

Use `tools/find_station.py` to find station IDs.

## Usage

### Run the Main App

```bash
python3 /home/pi/commute-app/main.py
```

This will:
- Monitor train arrivals at your home station
- Calculate when you need to leave
- Send Telegram alerts when it's time to go

### Run the API Server

```bash
python3 /home/pi/commute-app/api.py
```

API endpoints:
- `GET /` - Health check
- `GET /status` - Current commute status (JSON)

Example response:
```json
{
  "active": true,
  "line": "Piccadilly",
  "trains": [...],
  "best_train": {
    "train_departs": "08:15",
    "leave_time": "08:03",
    "countdown_minutes": 5,
    "arrival_at_work": "08:28"
  }
}
```

### Testing API (Always Active)

For testing outside your normal commute schedule:

```bash
python3 /home/pi/commute-app/testing/testit-api.py
```

Runs on port 5001 with no schedule restrictions.

## iPhone Widget Setup

1. Install **Scriptable** from the App Store
2. Create a new script and paste the code from `ios/scriptable-widget.js`
3. Update the API_URL to your Pi's IP address:
   ```javascript
   const API_URL = "http://192.168.1.163:5000/status";
   ```
4. Run the script to test
5. Add a Scriptable widget to your home screen and select the script

**Note:** iOS widgets refresh every 5-15 minutes (Apple limitation). Tap the widget to force refresh.

## Running on Boot (systemd)

Install the service:

```bash
sudo cp /home/pi/commute-app/commute-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable commute-api
sudo systemctl start commute-api
```

### Service Management Commands

```bash
sudo systemctl status commute-api   # Check if running
sudo systemctl start commute-api    # Start the service
sudo systemctl stop commute-api     # Stop the service
sudo systemctl restart commute-api  # Restart (after code changes)
journalctl -u commute-api -f        # View live logs
```

## API Servers Summary

| Server | Config | Port | Schedule |
|--------|--------|------|----------|
| `api.py` | `config.json` | 5000 | Tue/Wed 07:45-08:30 |
| `testing/testit-api.py` | `testing/config.test.json` | 5001 | Always active |
