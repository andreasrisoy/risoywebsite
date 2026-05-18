import json
import os
import urllib.request
import xml.etree.ElementTree as ET
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


def fetch_strompris():
    """Henter gjeldende times spotpris for prissone NO2 (Sørvest-Norge)."""
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    url = f"https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month_day}_NO2.json"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "risoy-dashboard/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            prices = json.loads(response.read().decode())
            current_hour = now.hour
            current_price_data = prices[current_hour]
            # Konverterer fra NOK/kWh til øre/kWh (inkluderer ikke nettleie/mva)
            price_ore = current_price_data["NOK"] * 100
            return f"{price_ore:.1f} øre"
    except Exception:
        return "N/A"


def fetch_ticker(symbol, name, unit=" kr", prefix=""):
    """Henter markedsdata (Aksjer, krypto, valuta) via Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if len(hist) >= 2:
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_percent = ((current_price - prev_close) / prev_close) * 100

            sign = "+" if change_percent >= 0 else ""
            color = "#10b981" if change_percent >= 0 else "#ef4444"

            if current_price > 1000:
                formatted_price = f"{prefix}{current_price:,.0f}{unit}".replace(
                    ",", " "
                )
            else:
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
        "value": "N/A",
        "change": "0.00%",
        "color": "#9ca3af",
    }


def fetch_nrk_news():
    """Henter og parser de 3 nyeste overskriftene fra NRK Toppsaker via RSS."""
    url = "https://www.nrk.no/toppsaker.rss"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "risoy-dashboard/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            news_items = []
            for item in root.findall(".//item")[:3]:
                title = item.find("title").text
                link = item.find("link").text
                news_items.append(
                    f"<li><a href='{link}' target='_blank'>{title}</a></li>"
                )
            return "".join(news_items)
    except Exception:
        return "<li>Kunne ikke laste nyheter akkurat nå.</li>"


def fetch_entur_departures():
    """Henter de neste 3 avgangene fra Stavanger S (NSR:StopPlace:59846) via Entur GraphQL."""
    url = "https://api.entur.io/journey-planner/v3/graphql"
    query = """
    {
      stopPlace(id: "NSR:StopPlace:59846") {
        name
        estimatedCalls(numberOfDepartures: 3) {
          expectedDepartureTime
          destinationDisplay { fontText }
          serviceJourney { journeyPattern { line { publicCode } } }
        }
      }
    }
    """
    data = json.dumps({"query": query}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "risoy-dashboard/1.0",
                "Content-Type": "application/json",
                "ET-Client-Name": "risoy-io-dashboard",
            },
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            calls = res_data["data"]["stopPlace"]["estimatedCalls"]
            items = []
            for call in calls:
                time_str = call["expectedDepartureTime"]
                dt = datetime.fromisoformat(time_str)
                time_formatted = dt.strftime("%H:%M")
                line = (
                    call["serviceJourney"]["journeyPattern"]["line"][
                        "publicCode"
                    ]
                    or ""
                )
                dest = call["destinationDisplay"]["frontText"]
                items.append(
                    f"<li><span class='line-badge'>{line}</span> {dest} — <b>{time_formatted}</b></li>"
                )
            return (
                "".join(items) if items else "<li>Ingen planlagte avganger</li>"
            )
    except Exception:
        return "<li>Klarte ikke å koble til Entur.</li>"


def fetch_space_people():
    """Henter antall mennesker i verdensrommet akkurat nå."""
    url = "http://api.open-notify.org/astros.json"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "risoy-dashboard/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return f"{data['number']} sjeler"
    except Exception:
        return "N/A"


def generate_html():
    current_time = datetime.now().strftime("%d. %b %Y, %H:%M:%S")

    # 1. Hent data fra alle moduler
    strom_now = fetch_strompris()
    space_now = fetch_space_people()
    nrk_html = fetch_nrk_news()
    entur_html = fetch_entur_departures()

    cities = {
        "Oslo": fetch_weather(59.91, 10.75),
        "Bergen": fetch_weather(60.39, 5.32),
        "Stavanger": fetch_weather(58.97, 5.73),
        "Trondheim": fetch_weather(63.43, 10.39),
    }
    sea_temp = fetch_sea_temp()

    # 2. Finans- og markedsdata grupper
    stocks_list = [
        ("^OSEBX", "Oslo Børs Hovedindeks", "", ""),
        ("BZ=F", "Nordsjøolje (Brent)", "", "$"),
        ("EQNR.OL", "Equinor (EQNR)", " kr", ""),
        ("DNB.OL", "DNB Bank (DNB)", " kr", ""),
        ("KOG.OL", "Kongsberg Gruppen (KOG)", " kr", ""),
        ("AKRBP.OL", "Aker BP (AKRBP)", " kr", ""),
        ("VAR.OL", "Vår Energi (VAR)", " kr", ""),
        ("FRO.OL", "Frontline (FRO)", " kr", ""),
    ]

    fx_crypto_list = [
        ("USDNOK=X", "USD / NOK", " kr", ""),
        ("EURNOK=X", "EUR / NOK", " kr", ""),
        ("BTC-USD", "Bitcoin (BTC)", "", "$"),
        ("ETH-USD", "Ethereum (ETH)", "", "$"),
    ]

    # Generer kortene dynamisk
    stock_cards_html = "".join(
        [
            f"""<div class="card"><div class="card-title">{s['name']}</div><div class="card-meta"><div class="card-value">{s['value']}</div><div class="card-change" style="color: {s['color']};">{s['change']}</div></div></div>"""
            for s in [fetch_ticker(*x) for x in stocks_list]
        ]
    )

    fx_cards_html = "".join(
        [
            f"""<div class="card"><div class="card-title">{s['name']}</div><div class="card-meta"><div class="card-value">{s['value']}</div><div class="card-change" style="color: {s['color']};">{s['change']}</div></div></div>"""
            for s in [fetch_ticker(*x) for x in fx_crypto_list]
        ]
    )

    weather_cards_html = "".join(
        [
            f"""<div class="card"><div class="card-title">Luft: {city}</div><div class="card-meta"><div class="card-value">{temp}</div><div class="card-change" style="color: #3b82f6;">Yr/Met</div></div></div>"""
            for city, temp in cities.items()
        ]
    )

    # Bygg hele den gigantiske HTML-malen
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
        .container {{ width: 100%; max-width: 1000px; }}
        h1 {{ font-size: 2.2rem; margin: 0 0 5px 0; letter-spacing: -0.5px; font-weight: 700; }}
        .timestamp {{ color: #9ca3af; font-size: 0.8rem; margin-bottom: 40px; }}
        
        h2 {{ font-size: 1.1rem; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px; margin-top: 40px; margin-bottom: 15px; border-bottom: 1px solid #1f2937; padding-bottom: 5px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 15px;
        }}
        .grid-wide {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
        }}
        @media (max-width: 500px) {{ .grid-wide {{ grid-template-columns: 1fr; }} }}

        .card {{
            background: #111827;
            border: 1px solid #1f2937;
            padding: 20px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card-title {{ color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .card-meta {{ display: flex; align-items: baseline; justify-content: space-between; margin-top: 10px; }}
        .card-value {{ font-size: 1.4rem; font-weight: bold; color: #ffffff; }}
        .card-change {{ font-size: 0.85rem; font-weight: 600; }}
        
        /* Spesial-lister for Nyheter og Buss */
        .card-list {{
            margin: 12px 0 0 0;
            padding-left: 0;
            list-style: none;
            font-size: 0.85rem;
        }}
        .card-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #1f2937;
            line-height: 1.4;
        }}
        .card-list li:last-child {{ border-bottom: none; }}
        .card-list a {{ color: #f3f4f6; text-decoration: none; transition: color 0.2s; }}
        .card-list a:hover {{ color: #3b82f6; }}
        
        .line-badge {{
            background: #1f2937;
            color: #3b82f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 5px;
            font-size: 0.75rem;
        }}
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

        <h2>💱 Valuta & Krypto</h2>
        <div class="grid">
            {fx_cards_html}
        </div>

        <h2>🌤️ Vær & Hjelpetjenester</h2>
        <div class="grid">
            {weather_cards_html}
            <div class="card">
                <div class="card-title">⚡ Strømpris nå (Prissone NO2)</div>
                <div class="card-meta">
                    <div class="card-value">{strom_now}</div>
                    <div class="card-change" style="color: #eab308;">Spotpris</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">🌊 Sjøtemp (Sørwestkysten)</div>
                <div class="card-meta">
                    <div class="card-value">{sea_temp}</div>
                    <div class="card-change" style="color: #06b6d4;">Yr/Marine</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">🚀 Mennesker i Verdensrommet</div>
                <div class="card-meta">
                    <div class="card-value">{space_now}</div>
                    <div class="card-change" style="color: #a855f7;">ISS Orbit</div>
                </div>
            </div>
        </div>

        <h2>📋 Informasjonsstrøm</h2>
        <div class="grid-wide">
            <div class="card">
                <div class="card-title">📰 Siste Toppsaker fra NRK</div>
                <ul class="card-list">
                    {nrk_html}
                </ul>
            </div>
            <div class="card">
                <div class="card-title">🚏 Sanntidsavganger (Stavanger S)</div>
                <ul class="card-list">
                    {entur_html}
                </ul>
            </div>
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
