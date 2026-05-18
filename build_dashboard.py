import json
import os
import urllib.request
from datetime import datetime
import yfinance as yf


def fetch_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=58.97&longitude=5.73&current=temperature_2m"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return f"{data['current']['temperature_2m']}°C"
    except Exception:
        return "N/A"


def fetch_ticker(symbol, is_index=False):
    """Henter siste lukkekurs og regner ut prosentvis endring fra i går."""
    try:
        ticker = yf.Ticker(symbol)
        # Henter historikk for de siste 2 handelsdagene
        hist = ticker.history(period="2d")

        if len(hist) >= 2:
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_percent = ((current_price - prev_close) / prev_close) * 100

            sign = "+" if change_percent >= 0 else ""
            color = "#10b981" if change_percent >= 0 else "#ef4444"

            unit = " poeng" if is_index else ""
            prefix = "$" if symbol == "BZ=F" else ""

            return (
                f"{prefix}{current_price:,.2f}{unit}".replace(",", " "),
                f"{sign}{change_percent:.2f}%",
                color,
            )
        return "N/A", "0.00%", "#9ca3af"
    except Exception:
        return "Feil ved henting", "0.00%", "#ef4444"


def generate_html():
    current_time = datetime.now().strftime("%d. %b %Y, %H:%M:%S")

    # Henter live-data fra markedet og vær
    weather_stavanger = fetch_weather()
    osebx_val, osebx_chg, osebx_col = fetch_ticker("^OSEBX", is_index=True)
    brent_val, brent_chg, brent_col = fetch_ticker("BZ=F")
    akerbp_val, akerbp_chg, akerbp_col = fetch_ticker("AKRBP.OL")
    varen_val, varen_chg, varen_col = fetch_ticker("VAR.OL")
    fro_val, fro_chg, fro_col = fetch_ticker("FRO.OL")

    html_content = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <title>risoy.io // Dashboard</title>
    <style>
        body {{
            background: #0b0f17;
            color: #f3f4f6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 40px 20px;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{ width: 100%; max-width: 650px; }}
        h1 {{ font-size: 1.8rem; margin: 0 0 5px 0; letter-spacing: -0.5px; }}
        .timestamp {{ color: #9ca3af; font-size: 0.8rem; margin-bottom: 30px; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            padding: 22px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card-title {{ color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .card-meta {{ display: flex; align-items: baseline; justify-content: space-between; margin-top: 12px; }}
        .card-value {{ font-size: 1.5rem; font-weight: bold; color: #ffffff; }}
        .card-change {{ font-size: 0.9rem; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>risoy.io // Dashboard</h1>
        <div class="timestamp">Sist oppdatert: {current_time} UTC (Automatisk)</div>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Oslo Børs Hovedindeks</div>
                <div class="card-meta">
                    <div class="card-value">{osebx_val}</div>
                    <div class="card-change" style="color: {osebx_col};">{osebx_chg}</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Nordsjøolje (Brent Crude)</div>
                <div class="card-meta">
                    <div class="card-value">{brent_val}</div>
                    <div class="card-change" style="color: {brent_col};">{brent_chg}</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Aker BP (AKRBP)</div>
                <div class="card-meta">
                    <div class="card-value">{akerbp_val} kr</div>
                    <div class="card-change" style="color: {akerbp_col};">{akerbp_chg}</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Vår Energi (VAR)</div>
                <div class="card-meta">
                    <div class="card-value">{varen_val} kr</div>
                    <div class="card-change" style="color: {varen_col};">{varen_chg}</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Frontline (FRO)</div>
                <div class="card-meta">
                    <div class="card-value">{fro_val} kr</div>
                    <div class="card-change" style="color: {fro_col};">{fro_chg}</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Været i Stavanger</div>
                <div class="card-meta">
                    <div class="card-value">{weather_stavanger}</div>
                    <div class="card-change" style="color: #3b82f6;">Live</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    generate_html()
