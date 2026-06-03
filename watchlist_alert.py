import os
import requests
import yfinance as yf
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def load_watchlist(path: str = "watchlist.txt") -> list:
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]

WATCHLIST = load_watchlist()

ALERT_DAYS_AHEAD = 14
VOLUME_SPIKE_MULTIPLIER = 2.0


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})


def check_earnings() -> list:
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

    return alerts


def check_volume() -> list:
    alerts = []

    for symbol in WATCHLIST:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="3mo")

            if len(hist) < 21:
                continue

            last_vol = hist["Volume"].iloc[-1]
            avg_vol = hist["Volume"].iloc[-21:-1].mean()

            if avg_vol > 0 and last_vol >= avg_vol * VOLUME_SPIKE_MULTIPLIER:
                ratio = last_vol / avg_vol
                last_date = hist.index[-1].date()
                alerts.append(
                    f"🔥 *{symbol}* volume spike on {last_date.strftime('%b %d')}: "
                    f"*{ratio:.1f}x* avg ({last_vol:,.0f} vs avg {avg_vol:,.0f})"
                )
        except Exception as e:
            print(f"Error checking volume for {symbol}: {e}")

    return alerts


if __name__ == "__main__":
    today = datetime.now().date()
    sections = []

    earnings_alerts = check_earnings()
    if earnings_alerts:
        sections.append("🔔 *Upcoming Earnings* (next 14 days)\n\n" + "\n".join(earnings_alerts))

    volume_alerts = check_volume()
    if volume_alerts:
        sections.append("📈 *Unusual Volume* (≥2x avg)\n\n" + "\n".join(volume_alerts))

    if sections:
        header = f"*Watchlist Alert* — {today.strftime('%b %d, %Y')}\n\n"
        send_telegram(header + "\n\n".join(sections))
        print(f"Sent: {len(earnings_alerts)} earnings, {len(volume_alerts)} volume alert(s)")
    else:
        print("Nothing to report today.")
