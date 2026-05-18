import json
import os
import urllib.request
from datetime import datetime
import yfinance as yf


def fetch_weather(lat, lon):
    """Henter lufttemperatur fra Yr/Met-data via Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "risoy-dashboard/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return f"{data['current']['temperature_2m']}°C"
    except Exception:
        return "N/A"


def fetch_sea_temp():
    """Henter hav-/badetemperatur for sørvestkysten via Open-Meteo Marine API."""
    url = "https://marine-api.open-meteo.com/v1/marine?latitude=58.97&longitude=5.73&current=sea_surface_temperature"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "risoy-dashboard/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return f"{data['current']['sea_surface_temperature']}°C"
    except Exception:
        return "N/A"


def fetch_ticker(symbol, name, is_index=False):
    """Henter markedsdata og formaterer verdi og endring i prosent."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if len(hist) >= 2:
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_percent = ((current_price - prev_close) / prev_close) * 100

            sign = "+" if change_percent >= 0 else ""
            color = "#10b981" if change_percent >= 0 else "#ef4444"
            unit = "" if is_index else " kr"
            prefix = "$" if symbol == "BZ=F" else ""

            formatted_price = f"{prefix}{current_price:,.2f}{unit}".replace(
                ",", " "
            )
            return {
                "name": name,
                "value": formatted_price,
                "change": f"{sign}{change_percent:.2f}%",
                "color": color,
            }
    except Exception:
        pass
    return {
        "name": name,
        "value": "Feil ved henting",
        "change": "0.00%",
        "color": "#ef4444",
    }


def generate_html():
    current_time = datetime.now().strftime("%d. %b %Y, %H:%M:%S")

    # 1. Hent vær for de største byene + havtemperatur
    cities = {
        "Oslo": fetch_weather(59.91, 10.75),
        "Bergen": fetch_weather(60.39, 5.32),
        "Stavanger": fetch_weather(58.97, 5.73),
        "Trondheim": fetch_weather(63.43, 10.39),
    }
    sea_temp = fetch_sea_temp()

    # 2. Hent markedsdata (Indekser og de mest omsatte tungvekterne på Oslo Børs)
    tickers = [
        ("^OSEBX", "Oslo Børs Hovedindeks", True),
        ("BZ=F", "Nordsjøolje (Brent)", False),
        ("EQNR.OL", "Equinor (EQNR) - Mest omsatt", False),
        ("DNB.OL", "DNB Bank (DNB) - Mest omsatt", False),
        ("KOG.OL", "Kongsberg Gruppen (KOG)", False),
        ("AKRBP.OL", "Aker BP (AKRBP)", False),
        ("VAR.OL", "Vår Energi (VAR)", False),
        ("FRO.OL", "Frontline (FRO)", False),
    ]

    financial_data = []
    for symbol, name, is_index in tickers:
        financial_data.append(fetch_ticker(symbol, name, is_index))

    # Generer HTML-strukturen for aksjekortene dynamisk
    stock_cards_html = ""
    for stock in financial_data:
        stock_cards_html += f"""
            <div class="card">
                <div class="card-title">{stock['name']}</div>
                <div class="card-meta">
                    <div class="card-value">{stock['value']}</div>
                    <div class="card-change" style="color: {stock['color']};">{stock['change']}</div>
                </div>
            </div>"""

    # Generer HTML-strukturen for værkortene dynamisk
    weather_cards_html = ""
    for city, temp in cities.items():
        weather_cards_html += f"""
            <div class="card">
                <div class="card-title">Luft: {city}</div>
                <div class="card-meta">
                    <div class="card-value">{temp}</div>
                    <div class="card-change" style="color: #3b82f6;">Yr/Met</div>
                </div>
            </div>"""

    # Sleng på badetemperaturen på slutten av værkortene
    weather_cards_html += f"""
        <div class="card">
            <div class="card-title">🌊 Sjøtemp (Sørvestkysten)</div>
            <div class="card-meta">
                <div class="card-value">{sea_temp}</div>
                <div class="card-change" style="color: #06b6d4;">Yr/Marine</div>
            </div>
        </div>"""

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
        .container {{ width: 100%; max-width: 900px; }}
        h1 {{ font-size: 2rem; margin: 0 0 5px 0; letter-spacing: -0.5px; }}
        .timestamp {{ color: #9ca3af; font-size: 0.8rem; margin-bottom: 40px; }}
        
        h2 {{ font-size: 1.1rem; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px; margin-top: 40px; margin-bottom: 15px; border-bottom: 1px solid #1f2937; padding-bottom: 5px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 15px;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            padding: 18px;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card-title {{ color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .card-meta {{ display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px; }}
        .card-value {{ font-size: 1.3rem; font-weight: bold; color: #ffffff; }}
        .card-change {{ font-size: 0.85rem; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>risoy.io // Dashboard</h1>
        <div class="timestamp">Siste robotoppdatering: {current_time} UTC (Hver 6. time)</div>
        
        <h2>🕒 Verdensklokke (Live)</h2>
        <div class="grid">
            <div class="card">
                <div class="card-title">Norge (Oslo/Stavanger)</div>
                <div class="card-meta"><div class="card-value" id="tz-oslo">--:--:--</div></div>
            </div>
            <div class="card">
                <div class="card-title">London (GMT/BST)</div>
                <div class="card-meta"><div class="card-value" id="tz-london">--:--:--</div></div>
            </div>
            <div class="card">
                <div class="card-title">New York (EST/EDT)</div>
                <div class="card-meta"><div class="card-value" id="tz-ny">--:--:--</div></div>
            </div>
            <div class="card">
                <div class="card-title">Tokyo (JST)</div>
                <div class="card-meta"><div class="card-value" id="tz-tokyo">--:--:--</div></div>
            </div>
        </div>

        <h2>📈 Oslo Børs & Markedsdata</h2>
        <div class="grid">
            {stock_cards_html}
        </div>

        <h2>🌤️ Vær & Sjøtemperaturer</h2>
        <div class="grid">
            {weather_cards_html}
        </div>
    </div>

    <script>
        function updateClocks() {{
            const options = {{ hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }};
            document.getElementById('tz-oslo').textContent = new Date().toLocaleTimeString('no-NO', {{ ...options, timeZone: 'Europe/Oslo' }});
            document.getElementById('tz-london').textContent = new Date().toLocaleTimeString('no-NO', {{ ...options, timeZone: 'Europe/London' }});
            document.getElementById('tz-ny').textContent = new Date().toLocaleTimeString('no-NO', {{ ...options, timeZone: 'America/New_York' }});
            document.getElementById('tz-tokyo').textContent = new Date().toLocaleTimeString('no-NO', {{ ...options, timeZone: 'Asia/Tokyo' }});
        }}
        setInterval(updateClocks, 1000);
        updateClocks();
    </script>
</body>
</html>
"""

    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    generate_html()
