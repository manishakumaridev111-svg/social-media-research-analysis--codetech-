# Social Media Reach Analysis — Task 4 (CodTech Internship)

A PyQt6 desktop dashboard that pulls **real, live data** from the YouTube Data API v3
and analyzes a channel's reach: views, likes, comments, engagement rate, and trends.

## Features
- Real API integration (no dummy data) — YouTube Data API v3
- Dark-themed dashboard UI (matches Task 3 styling)
- Overview cards: subscribers, total views, avg views/likes, engagement rate
- Sortable video table (last 25 uploads)
- Charts: views trend line + top-5 videos by views (matplotlib embedded)
- Export to CSV and a formatted PDF report
- Background thread for API calls — UI never freezes

## Project Structure
```
SocialMediaReachAnalysis/
├── main.py                    # entry point
├── requirements.txt
├── Backend/
│   ├── youtube_api.py          # YouTube Data API v3 calls (requests-based)
│   ├── analytics.py            # engagement rate, trends, top videos
│   └── export.py               # CSV + PDF export
├── Frontend/
│   ├── main_window.py          # PyQt6 UI, threaded fetch, charts
│   └── theme.py                # dark stylesheet
└── exports/                    # CSV/PDF reports saved here
```

## Setup

### 1. Get a free YouTube Data API v3 key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Go to **APIs & Services → Library**, search **"YouTube Data API v3"**, click **Enable**
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. Copy the generated key — this is what you paste into the app

*(Free tier: 10,000 quota units/day — more than enough for this project; each channel
analysis in this app uses roughly 5-10 units.)*

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python main.py
```

## How to use
1. Paste your API key into the first field
2. Enter a channel handle (e.g. `@MrBeast`) or a raw channel ID (starts with `UC...`)
3. Click **Analyze**
4. Explore the **Overview**, **Videos**, and **Charts** tabs
5. Use **Export CSV** / **Export PDF Report** to save results into the `exports/` folder

## Notes for submission
- All API logic lives in `Backend/youtube_api.py` — no API key is hardcoded anywhere
- Engagement rate formula: `(likes + comments) / views * 100`
- Reach classification thresholds are in `Backend/analytics.py` → `reach_classification()`
  and can be tuned if your evaluator expects different bands
