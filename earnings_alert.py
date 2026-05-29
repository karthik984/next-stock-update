import os
import requests
import yfinance as yf
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Edit this list with your stocks
WATCHLIST = [
    # Wave 1 — GPU / Compute (already played but still matters)
    "NVDA",
    
    # Wave 2 — HBM Memory (RIGHT NOW)
    "MU",       # Micron — you already own
    "AMKR",     # Amkor — advanced packaging
    
    # Wave 3 — Networking / Optical Interconnects (building)
    "MRVL",     # Marvell
    "AVGO",     # Broadcom
    "COHR",     # Coherent — optical
    
    # Wave 4 — Power & Energy Infrastructure (multi-year)
    "VST",      # Vistra — power gen
    "CEG",      # Constellation Energy — nuclear
    "ETN",      # Eaton — transformers
    "PWR",      # Quanta Services — grid buildout
    
    # Wave 5 — Liquid Cooling (emerging)
    "VRT",      # Vertiv
    
    # Wave 6 — Cloud Data Platforms (Snowflake moment)
    "SNOW",     # Snowflake — you just missed this one
    "PLTR",     # Palantir — enterprise AI
    
    # ARM / Custom Silicon
    "ARM",      # ARM Holdings — royalties on everything
    "TSM",      # TSMC — manufactures it all
    
    # Already in your portfolio
    "SMCI",     # SuperMicro — servers
]

ALERT_DAYS_AHEAD = 14


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})


def check_earnings():
    today = datetime.now().date()
    cutoff = today + timedelta(days=ALERT_DAYS_AHEAD)
    alerts = []

    for symbol in WATCHLIST:
        try:
            t = yf.Ticker(symbol)
            cal = t.calendar

            if not cal or "Earnings Date" not in cal:
                continue

            raw = cal["Earnings Date"]
            dates = raw if isinstance(raw, list) else [raw]
            for d in dates:
                if d is None:
                    continue
                earnings_date = d.date() if hasattr(d, "date") else d
                if today <= earnings_date <= cutoff:
                    days_away = (earnings_date - today).days
                    alerts.append(
                        f"📊 *{symbol}* earnings in *{days_away} day(s)* — {earnings_date.strftime('%b %d, %Y')}"
                    )
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    if alerts:
        header = f"🔔 *Upcoming Earnings Alert* ({today.strftime('%b %d')})\n\n"
        send_telegram(header + "\n".join(alerts))
        print(f"Sent {len(alerts)} alert(s)")
    else:
        print("No upcoming earnings within alert window.")


if __name__ == "__main__":
    check_earnings()
