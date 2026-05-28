"""
SignalWatch Backend — FastAPI + Claude AI
Deploy to Railway. Set ANTHROPIC_API_KEY as an environment variable.
"""

import os
import json
import re
from typing import List
from datetime import datetime

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── APP SETUP ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SignalWatch API",
    description="AI-powered multi-timeframe technical analysis for trading watchlists",
    version="1.0.0",
)

# CORS — allow your Vercel frontend + localhost dev
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ANTHROPIC CLIENT ─────────────────────────────────────────────────────────
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

client = anthropic.Anthropic(api_key=api_key)

# ─── MODELS ───────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    symbols: List[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# ─── PROMPT BUILDER ───────────────────────────────────────────────────────────
ANALYSIS_PROMPT = """You are a professional multi-timeframe technical analysis AI for a trading dashboard.
Today is {date}. You have deep knowledge of equities, ETFs, crypto, commodities, and their typical technical behavior.

Analyze the following symbols: {symbols}

Return ONLY a raw JSON array — no markdown, no code fences, no explanation, just the array.

Each object in the array must follow this exact schema:
{{
  "symbol": "SYMBOL",
  "assetType": "Stock|ETF|Crypto|Commodity|Index",
  "timeframes": {{
    "1m": "Bullish|Bearish|Neutral",
    "5m": "Bullish|Bearish|Neutral",
    "15m": "Bullish|Bearish|Neutral",
    "30m": "Bullish|Bearish|Neutral",
    "1h": "Bullish|Bearish|Neutral",
    "4h": "Bullish|Bearish|Neutral",
    "1D": "Bullish|Bearish|Neutral",
    "1W": "Bullish|Bearish|Neutral",
    "1M": "Bullish|Bearish|Neutral"
  }},
  "score": <integer 0-100>,
  "signal": "Strong Buy|Buy|Neutral|Sell|Strong Sell|Mixed",
  "risk": "Low|Medium|High",
  "shortTerm": "Bullish|Bearish|Neutral|Mixed",
  "intraday": "Bullish|Bearish|Neutral|Mixed",
  "swing": "Bullish|Bearish|Neutral|Mixed",
  "longTerm": "Bullish|Bearish|Neutral|Mixed",
  "currentTrend": "Bullish|Bearish|Neutral|Mixed",
  "bestTF": "e.g. 15m / 1h",
  "horizon": "e.g. 1-5 days",
  "note": "Two-sentence nuanced analysis. Use language like: Bullish but extended, Bearish trend, Mixed signal, Good only for short-term scalp, Better to wait for confirmation, Bullish with pullback risk. Never promise returns or use the word guaranteed.",
  "alerts": ["concise specific alert string", ...]
}}

Scoring rules:
- 80-100: Strong directional conviction across multiple timeframes
- 60-79: Buy or Sell — moderate confidence
- 40-59: Neutral or Mixed — conflicting signals
- Below 40: Weak, wait for confirmation

Timeframe interpretation:
- 1m/5m: Minutes to a few hours (scalping)
- 15m/30m: Half day to 2 days (intraday)
- 1h/4h: 1 day to 2 weeks (swing)
- 1D/1W: 1 month to 1 year (position)
- 1M: 1 year+ (macro)

Alert triggers to check:
- RSI overbought (>70) or oversold (<30) on any timeframe
- MACD crossover detected
- Price near EMA 50, EMA 200, or key support/resistance
- Volume divergence
- Multi-timeframe alignment (e.g. 15m + 1h both Bullish)
- Short-term vs long-term conflict

Be realistic and thoughtful. Vary signals meaningfully between symbols based on their actual market behavior and asset class characteristics. Include 0-3 specific alerts per symbol."""

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/", response_model=HealthResponse)
def root():
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.symbols:
        raise HTTPException(status_code=400, detail="No symbols provided.")
    if len(req.symbols) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 symbols per request.")

    # Sanitize symbols
    clean_symbols = []
    for s in req.symbols:
        s = re.sub(r'[^A-Z0-9.]', '', s.upper())
        if s and len(s) <= 10:
            clean_symbols.append(s)

    if not clean_symbols:
        raise HTTPException(status_code=400, detail="No valid symbols after sanitization.")

    prompt = ANALYSIS_PROMPT.format(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        symbols=", ".join(clean_symbols)
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    raw = "".join(block.text for block in message.content if hasattr(block, "text"))

    # Parse JSON — strip any accidental markdown fences
    raw_clean = re.sub(r"```json|```", "", raw).strip()
    try:
        results = json.loads(raw_clean)
    except json.JSONDecodeError:
        # Try to extract array with regex as fallback
        match = re.search(r"\[[\s\S]*\]", raw_clean)
        if match:
            try:
                results = json.loads(match.group())
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON.")
        else:
            raise HTTPException(status_code=500, detail="AI response did not contain valid JSON.")

    if not isinstance(results, list):
        raise HTTPException(status_code=500, detail="AI response was not a JSON array.")

    return {
        "results": results,
        "analyzed_at": datetime.utcnow().isoformat() + "Z",
        "symbols_requested": clean_symbols,
        "count": len(results)
    }
