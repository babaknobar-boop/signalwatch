# SignalWatch × TradingView

AI-powered multi-timeframe trading dashboard.
- **Frontend**: Plain HTML + TradingView embeds → deployed on **Vercel** (free)
- **Backend**: Python FastAPI + Claude AI → deployed on **Railway** (free tier)
- **Data**: TradingView official embed widgets (no API key needed)
- **AI**: Claude Sonnet via Anthropic API

---

## Project Structure

```
signalwatch/
├── frontend/
│   ├── index.html       ← Your entire dashboard UI
│   └── vercel.json      ← Vercel deployment config
├── backend/
│   ├── main.py          ← FastAPI app + Claude AI analysis
│   ├── requirements.txt
│   ├── Procfile         ← Railway start command
│   └── .env.example     ← Copy to .env for local dev
├── .gitignore
└── README.md
```

---

## Step 1 — Get your Anthropic API Key

1. Go to https://console.anthropic.com
2. Create an account or log in
3. Navigate to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`) — save it, you'll need it in Step 3

---

## Step 2 — Push to GitHub

```bash
# From the signalwatch/ folder:
git init
git add .
git commit -m "Initial SignalWatch dashboard"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/signalwatch.git
git branch -M main
git push -u origin main
```

---

## Step 3 — Deploy Backend to Railway

1. Go to https://railway.app and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `signalwatch` repo
4. Railway will detect the `backend/` folder. Set the **Root Directory** to `backend`
5. Click **Variables** → **Add Variable**:
   ```
   ANTHROPIC_API_KEY = sk-ant-your-key-here
   ALLOWED_ORIGINS   = https://signalwatch.vercel.app  ← set after step 4
   ```
6. Click **Deploy**
7. Once deployed, go to **Settings** → **Networking** → **Generate Domain**
8. Copy your Railway URL — looks like: `https://signalwatch-production.up.railway.app`

---

## Step 4 — Deploy Frontend to Vercel

1. Go to https://vercel.com and sign in with GitHub
2. Click **Add New Project** → import your `signalwatch` repo
3. Set **Root Directory** to `frontend`
4. Click **Deploy**
5. Copy your Vercel URL — looks like: `https://signalwatch.vercel.app`

---

## Step 5 — Connect Frontend to Backend

Open `frontend/index.html` and find this line near the top of the `<script>`:

```javascript
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://YOUR-RAILWAY-APP.up.railway.app'; // ← replace this
```

Replace `YOUR-RAILWAY-APP.up.railway.app` with your actual Railway URL.

Then go back to Railway → your project → **Variables** and update:
```
ALLOWED_ORIGINS = https://signalwatch.vercel.app
```

Commit and push — both Vercel and Railway auto-redeploy on push.

---

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Option A: VS Code Live Server extension (recommended)
# Right-click index.html → Open with Live Server

# Option B: Python simple server
python -m http.server 5500
# Then open http://localhost:5500
```

The frontend auto-detects localhost and points to `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint    | Description                        |
|--------|-------------|------------------------------------|
| GET    | `/`         | Health check                       |
| GET    | `/health`   | Health check with timestamp        |
| POST   | `/analyze`  | Analyze symbols with AI            |

### POST /analyze

Request:
```json
{
  "symbols": ["TSLA", "SPY", "BTC", "GLD"]
}
```

Response:
```json
{
  "results": [
    {
      "symbol": "TSLA",
      "assetType": "Stock",
      "timeframes": {
        "1m": "Bullish",
        "5m": "Bullish",
        "15m": "Neutral",
        "30m": "Bullish",
        "1h": "Bullish",
        "4h": "Mixed",
        "1D": "Neutral",
        "1W": "Bullish",
        "1M": "Neutral"
      },
      "score": 68,
      "signal": "Buy",
      "risk": "Medium",
      "shortTerm": "Bullish",
      "intraday": "Bullish",
      "swing": "Mixed",
      "longTerm": "Neutral",
      "currentTrend": "Bullish",
      "bestTF": "15m / 1h",
      "horizon": "1-3 days",
      "note": "TSLA shows short-term bullish momentum with EMA 10/20 aligned on the 1h chart. However, daily resistance is approaching — better entries may come after a pullback toward the 4h EMA 50.",
      "alerts": [
        "RSI approaching overbought on 1h",
        "15m and 1h aligned Bullish — entry window open"
      ]
    }
  ],
  "analyzed_at": "2026-05-27T12:00:00Z",
  "symbols_requested": ["TSLA", "SPY", "BTC", "GLD"],
  "count": 4
}
```

---

## Scoring System

| Score  | Signal Label    | Badge Color  |
|--------|-----------------|--------------|
| 80–100 | Strong Buy/Sell | Bright green/red |
| 60–79  | Buy / Sell      | Green/red    |
| 40–59  | Neutral/Mixed   | Yellow       |
| 0–39   | Weak/Risky      | Dim red      |

---

## TradingView Widgets Used

All widgets load from TradingView's official CDN — no API key required:

- **Technical Analysis widget** — shows Buy/Sell/Neutral gauge with RSI, MACD, MA signals
- **Advanced Chart widget** — full interactive chart with all indicators

Both are [officially documented](https://www.tradingview.com/widget-docs/) and free to embed.

---

## Supported Symbols

The dashboard supports any symbol TradingView supports. Common mappings included:

| You type | TradingView symbol  |
|----------|---------------------|
| BTC      | BITSTAMP:BTCUSD     |
| ETH      | BITSTAMP:ETHUSD     |
| GOLD     | XAUUSD              |
| SILVER   | XAGUSD              |
| OIL      | TVC:USOIL           |
| GLD      | AMEX:GLD            |
| SPY      | AMEX:SPY            |
| QQQ      | NASDAQ:QQQ          |
| TSLA     | NASDAQ:TSLA         |
| UBER     | NYSE:UBER           |

Add more mappings in the `TV_SYM` object in `frontend/index.html`.

---

## Disclaimer

This dashboard is for **educational and informational purposes only**. It does not constitute financial advice. All AI-generated signals are estimates based on typical technical patterns and should not be used as the sole basis for trading decisions. Always conduct your own research.
