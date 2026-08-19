import os
import re
import math
import requests
import folium
from dotenv import load_dotenv
from datetime import datetime, timezone
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
AVIATION_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# ---------------------------------------------------------------------------
# Airport coordinates fallback database
# ---------------------------------------------------------------------------
AIRPORT_COORDS = {
    "DEL": (28.5665, 77.1031),  "BOM": (19.0896, 72.8656),
    "MAA": (12.9941, 80.1709),  "BLR": (13.1979, 77.7063),
    "HYD": (17.2403, 78.4294),  "CCU": (22.6520, 88.4463),
    "AMD": (23.0777, 72.6347),  "COK": (10.1520, 76.4019),
    "GOI": (15.3808, 73.8314),  "PNQ": (18.5822, 73.9197),
    "JAI": (26.8242, 75.8122),  "LKO": (26.7606, 80.8893),
    "ATQ": (31.7096, 74.7973),  "IXC": (30.6735, 76.7885),
    "SXR": (33.9871, 74.7742),  "DXB": (25.2532, 55.3657),
    "SIN": (1.3644, 103.9915),  "LHR": (51.4775, -0.4614),
    "JFK": (40.6413, -73.7781), "FCO": (41.8003, 12.2389),
    "BKK": (13.6811, 100.7472), "KUL": (2.7456, 101.7099),
    "HKG": (22.3080, 113.9185), "DOH": (25.2609, 51.6138),
    "AUH": (24.4330, 54.6511),  "FRA": (50.0379, 8.5622),
    "CDG": (49.0097, 2.5479),   "AMS": (52.3086, 4.7639),
    "IST": (41.2608, 28.7418),  "SYD": (-33.9399, 151.1753),
    "LAX": (33.9425, -118.4081),"ORD": (41.9742, -87.9073),
    "DFW": (32.8998, -97.0403), "NRT": (35.7720, 140.3929),
    "ICN": (37.4602, 126.4407), "PEK": (40.0799, 116.6031),
    "SVO": (55.9736, 37.4125),  "MUC": (48.3537, 11.7750),
    "ZRH": (47.4582, 8.5555),   "GVA": (46.2380, 6.1089),
}

# ---------------------------------------------------------------------------
# Helper — clean time format
# ---------------------------------------------------------------------------
def clean_time(t: str) -> str:
    """Convert ISO-8601 to human readable format"""
    if not t or t == 'N/A':
        return 'N/A'
    try:
        dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
        return dt.strftime("%d-%m-%Y %H:%M UTC")
    except:
        return str(t)[:16].replace('T', ' ')

# ---------------------------------------------------------------------------
# Core data fetchers
# ---------------------------------------------------------------------------
def get_flight_data(flight_number: str) -> dict:
    """Fetch live flight data from Aviationstack."""
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": AVIATION_KEY,
        "flight_iata": flight_number.upper()
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0]
        return None
    except Exception as e:
        print(f"AviationStack error: {e}")
        return None


def get_live_position(flight_number: str) -> dict:
    """Get live position from OpenSky Network."""
    try:
        callsign = flight_number.upper().replace(" ", "")
        url = "https://opensky-network.org/api/states/all"
        response = requests.get(url, timeout=15)
        data = response.json()
        if data and data.get("states"):
            for state in data["states"]:
                if not state[1]:
                    continue
                state_callsign = str(state[1]).strip().upper()
                if (callsign in state_callsign or
                        state_callsign in callsign or
                        callsign[:4] in state_callsign):
                    if state[6] and state[5]:
                        return {
                            "latitude": state[6],
                            "longitude": state[5],
                            "altitude": state[7] or "N/A",
                            "speed": state[9] or "N/A",
                            "direction": state[10] or "N/A",
                        }
        return {}
    except Exception as e:
        print(f"OpenSky error: {e}")
        return {}

# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------
def get_weather(lat: float, lon: float, label: str = "") -> dict:
    """Fetch current weather using Open-Meteo (free, no API key)."""
    WMO_CODES = {
        0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy",
        3: "Overcast", 45: "Fog", 48: "Icy Fog",
        51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle",
        61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
        71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
        80: "Light Showers", 81: "Showers", 82: "Heavy Showers",
        95: "Thunderstorm", 96: "Thunderstorm w/ Hail",
    }
    try:
        url = "http://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "relativehumidity_2m,windspeed_10m,visibility",
            "forecast_days": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"available": False}

        data = resp.json()
        cw = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        humidity = hourly.get("relativehumidity_2m", [None])[0]
        wind_kmh = hourly.get("windspeed_10m", [None])[0]
        visibility_m = hourly.get("visibility", [None])[0]
        wcode = int(cw.get("weathercode", 0))

        return {
            "available": True,
            "condition": WMO_CODES.get(wcode, f"Code {wcode}"),
            "temp_c": cw.get("temperature", "N/A"),
            "humidity_pct": humidity if humidity is not None else "N/A",
            "wind_kmh": wind_kmh if wind_kmh is not None else cw.get("windspeed", "N/A"),
            "visibility_km": round(visibility_m / 1000, 1) if visibility_m else "N/A",
        }
    except Exception as e:
        print(f"Weather error ({label}): {e}")
        return {"available": False}


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_flight_progress(dep_lat, dep_lon,
                               arr_lat, arr_lon,
                               live_lat, live_lon) -> dict:
    """Calculate journey progress percentage."""
    try:
        total_km = _haversine_km(dep_lat, dep_lon, arr_lat, arr_lon)
        completed_km = _haversine_km(dep_lat, dep_lon, live_lat, live_lon)
        remaining_km = _haversine_km(live_lat, live_lon, arr_lat, arr_lon)
        pct = min(100.0, round((completed_km / total_km) * 100, 1)) if total_km > 0 else 0
        return {
            "available": True,
            "pct": pct,
            "completed_km": round(completed_km),
            "remaining_km": round(remaining_km),
            "total_km": round(total_km),
        }
    except Exception as e:
        print(f"Progress calc error: {e}")
        return {"available": False}


def calculate_delay(scheduled_str: str, actual_str: str):
    """Return delay in minutes. Positive = late."""
    fmt_options = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S"
    ]
    def parse(s):
        if not s:
            return None
        s = s.strip()
        for fmt in fmt_options:
            try:
                dt = datetime.strptime(s, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        return None

    sched = parse(scheduled_str)
    actual = parse(actual_str)
    if sched and actual:
        return int((actual - sched).total_seconds() / 60)
    return None


def calculate_countdown(arr_estimated_str: str) -> dict:
    """Calculate time remaining until estimated arrival."""
    fmt_options = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S"
    ]
    def parse(s):
        if not s:
            return None
        s = s.strip()
        for fmt in fmt_options:
            try:
                dt = datetime.strptime(s, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        return None

    eta = parse(arr_estimated_str)
    if not eta:
        return {"available": False}
    now = datetime.now(timezone.utc)
    diff = eta - now
    total_mins = int(diff.total_seconds() / 60)
    if total_mins < 0:
        return {
            "available": True,
            "landed_or_past": True,
            "total_mins": total_mins
        }
    return {
        "available": True,
        "landed_or_past": False,
        "hours": total_mins // 60,
        "minutes": total_mins % 60,
        "total_mins": total_mins,
    }


def extract_aircraft_details(flight_data: dict) -> dict:
    """Extract aircraft details."""
    aircraft = flight_data.get("aircraft") or {}
    return {
        "registration": aircraft.get("registration", "N/A"),
        "iata": aircraft.get("iata", "N/A"),
        "icao": aircraft.get("icao", "N/A"),
        "icao24": aircraft.get("icao24", "N/A"),
    }


def extract_airport_details(endpoint: dict) -> dict:
    """Extract full airport details."""
    return {
        "name": endpoint.get("airport", "N/A"),
        "iata": endpoint.get("iata", "N/A"),
        "icao": endpoint.get("icao", "N/A"),
        "terminal": endpoint.get("terminal", "N/A"),
        "gate": endpoint.get("gate", "N/A"),
        "timezone": endpoint.get("timezone", "N/A"),
        "scheduled": endpoint.get("scheduled", "N/A"),
        "estimated": endpoint.get("estimated", "N/A"),
        "actual": endpoint.get("actual", "N/A"),
        "delay": endpoint.get("delay", None),
    }


def generate_ai_summary(flight_data, progress,
                         dep_delay, arr_delay, countdown) -> str:
    """Generate AI summary of flight status."""
    dep = flight_data.get("departure") or {}
    arr = flight_data.get("arrival") or {}
    flight_info = flight_data.get("flight") or {}
    airline = flight_data.get("airline") or {}
    status = flight_data.get("flight_status", "unknown")

    progress_text = (
        f"The flight has completed {progress['pct']}% of its journey "
        f"({progress['completed_km']} km of {progress['total_km']} km)."
        if progress.get("available")
        else "Journey progress data is unavailable."
    )

    delay_text = ""
    if dep_delay is not None:
        delay_text += (f"Departure was "
                       f"{'delayed by' if dep_delay > 0 else 'early by'} "
                       f"{abs(dep_delay)} minutes. ")
    if arr_delay is not None:
        delay_text += (f"Arrival is estimated "
                       f"{'late by' if arr_delay > 0 else 'early by'} "
                       f"{abs(arr_delay)} minutes. ")
    if not delay_text:
        delay_text = "No delay information available."

    if countdown.get("available") and not countdown.get("landed_or_past"):
        eta_text = (f"Estimated time remaining: "
                    f"{countdown['hours']}h {countdown['minutes']}m.")
    elif countdown.get("landed_or_past"):
        eta_text = "The flight has already landed."
    else:
        eta_text = "ETA data is unavailable."

    prompt = f"""
    Write a concise, friendly 3-4 sentence summary for a traveler.

    Flight: {flight_info.get('iata', 'N/A')} by {airline.get('name', 'N/A')}
    From: {dep.get('airport', 'N/A')} → To: {arr.get('airport', 'N/A')}
    Status: {status.upper()}
    {progress_text}
    Delays: {delay_text}
    {eta_text}

    Keep it clear, factual and helpful.
    Respond in plain text, no markdown.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI summary error: {e}")
        return "AI summary could not be generated."

# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------
def create_flight_map(flight_data: dict) -> folium.Map:
    """Create interactive flight map."""
    departure = flight_data.get("departure") or {}
    arrival = flight_data.get("arrival") or {}
    live = flight_data.get("live") or {}

    dep_iata = departure.get("iata", "")
    arr_iata = arrival.get("iata", "")

    dep_coords = AIRPORT_COORDS.get(dep_iata, (28.5665, 77.1031))
    arr_coords = AIRPORT_COORDS.get(arr_iata, (19.0896, 72.8656))

    dep_lat = departure.get("latitude") or dep_coords[0]
    dep_lon = departure.get("longitude") or dep_coords[1]
    arr_lat = arrival.get("latitude") or arr_coords[0]
    arr_lon = arrival.get("longitude") or arr_coords[1]
    live_lat = live.get("latitude")
    live_lon = live.get("longitude")
    altitude = live.get("altitude", "N/A")
    speed = live.get("speed", "N/A")

    # Clean time format
    dep_time = clean_time(departure.get('scheduled', 'N/A'))
    arr_time = clean_time(arrival.get('scheduled', 'N/A'))

    # Center between departure and arrival
    center_lat = (dep_lat + arr_lat) / 2
    center_lon = (dep_lon + arr_lon) / 2

    # Zoom based on distance
    lat_diff = abs(dep_lat - arr_lat)
    lon_diff = abs(dep_lon - arr_lon)
    max_diff = max(lat_diff, lon_diff)

    if max_diff > 100:
        zoom = 2
    elif max_diff > 50:
        zoom = 3
    elif max_diff > 20:
        zoom = 4
    else:
        zoom = 5

    flight_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron"
    )

    # Departure marker
    dep_name = departure.get('airport', dep_iata or 'Departure Airport')
    folium.Marker(
        location=[dep_lat, dep_lon],
        popup=folium.Popup(f"""
            <div style="font-family:Arial; min-width:180px;">
            <b style="color:#00aa44;">🛫 DEPARTURE</b><br>
            <b>{dep_name}</b><br>
            <hr style="margin:4px 0;">
            IATA: <b>{dep_iata}</b><br>
            Scheduled: <b>{dep_time}</b><br>
            Coordinates: {round(dep_lat,2)}°, {round(dep_lon,2)}°
            </div>
        """, max_width=220),
        tooltip=f"🛫 {dep_iata} — Click for details",
        icon=folium.Icon(color="green", icon="plane", prefix="fa")
    ).add_to(flight_map)

    # Arrival marker
    arr_name = arrival.get('airport', arr_iata or 'Arrival Airport')
    folium.Marker(
        location=[arr_lat, arr_lon],
        popup=folium.Popup(f"""
            <div style="font-family:Arial; min-width:180px;">
            <b style="color:#cc2200;">🛬 ARRIVAL</b><br>
            <b>{arr_name}</b><br>
            <hr style="margin:4px 0;">
            IATA: <b>{arr_iata}</b><br>
            Scheduled: <b>{arr_time}</b><br>
            Coordinates: {round(arr_lat,2)}°, {round(arr_lon,2)}°
            </div>
        """, max_width=220),
        tooltip=f"🛬 {arr_iata} — Click for details",
        icon=folium.Icon(color="red", icon="plane", prefix="fa")
    ).add_to(flight_map)

    # Planned route (dashed orange)
    folium.PolyLine(
        locations=[[dep_lat, dep_lon], [arr_lat, arr_lon]],
        color="#FF6B35", weight=2, opacity=0.5,
        dash_array="10", tooltip="Planned Route"
    ).add_to(flight_map)

    if live_lat and live_lon:
        # Completed route (solid blue)
        folium.PolyLine(
            locations=[[dep_lat, dep_lon], [live_lat, live_lon]],
            color="#0066CC", weight=4, opacity=0.9,
            tooltip="Completed Route"
        ).add_to(flight_map)

        # Remaining route (dashed gray)
        folium.PolyLine(
            locations=[[live_lat, live_lon], [arr_lat, arr_lon]],
            color="#999999", weight=2, opacity=0.6,
            dash_array="8", tooltip="Remaining Route"
        ).add_to(flight_map)

        # Live airplane icon
        folium.Marker(
            location=[live_lat, live_lon],
            popup=folium.Popup(f"""
                <div style="font-family:Arial; min-width:180px;">
                <b style="color:#0066cc;">✈️ LIVE POSITION</b><br>
                <hr style="margin:4px 0;">
                Latitude: <b>{live_lat}°</b><br>
                Longitude: <b>{live_lon}°</b><br>
                Altitude: <b>{altitude} m</b><br>
                Speed: <b>{speed} km/h</b><br>
                <hr style="margin:4px 0;">
                <small>Updated in real-time</small>
                </div>
            """, max_width=220),
            tooltip=f"✈️ Live | Alt: {altitude}m | {speed}km/h",
            icon=folium.DivIcon(
                html='<div style="font-size:28px;transform:rotate(45deg);'
                     'filter:drop-shadow(2px 2px 2px rgba(0,0,0,0.5))">✈️</div>',
                icon_size=(40, 40),
                icon_anchor=(20, 20)
            )
        ).add_to(flight_map)

        # Pulsing circle
        folium.CircleMarker(
            location=[live_lat, live_lon],
            radius=15,
            color="#0066CC",
            fill=True,
            fill_color="#0066CC",
            fill_opacity=0.2,
            weight=2,
            tooltip="Current Position"
        ).add_to(flight_map)

    return flight_map

# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------
def run_flight_pipeline(user_query: str) -> tuple:
    """Main flight tracking pipeline."""
    print("\n" + "=" * 60)
    print("   FLIGHT TRACKING PIPELINE STARTED")
    print("=" * 60)

    # Step 1: Extract flight number
    print("\n🧠 Step 1: Extracting flight number...")
    extract_prompt = f"""
    Extract the flight number from this query.
    Query: {user_query}
    Reply with ONLY the flight number like: AI101, EK202, 6E456
    Nothing else. Just the flight number.
    If no flight number found, reply: UNKNOWN
    """
    extract_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": extract_prompt}]
    )
    flight_number = extract_response.choices[0].message.content.strip()
    print(f"✅ Flight number: {flight_number}")

    # Step 2: Fetch live data
    print("\n✈️  Step 2: Fetching live flight data...")
    flight_data = get_flight_data(flight_number)

    if not flight_data:
        print("⚠️ Live data not available — using AI analysis")
        ai_prompt = f"""
        You are a flight information assistant.
        Answer this flight query: {user_query}
        Note that live data is currently unavailable.
        Provide general information about this flight or airline.
        """
        ai_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": ai_prompt}]
        )
        return ai_response.choices[0].message.content.strip(), None, None

    print("✅ Live data fetched!")

    # Get actual flight number
    actual_flight_number = flight_number
    fi = flight_data.get("flight") or {}
    if fi.get("iata"):
        actual_flight_number = fi["iata"]

    # Step 3: Live position
    print(f"\n📍 Step 3: Fetching live position...")
    live_position = get_live_position(actual_flight_number)
    if live_position.get("latitude"):
        print("✅ Live position found!")
        flight_data["live"] = live_position
    else:
        print("⚠️ Live position not available")

    # Step 4: Build map
    print("\n🗺️  Step 4: Creating flight map...")
    flight_map = create_flight_map(flight_data)
    print("✅ Map created!")

    # Step 5: Enrich data
    print("\n🔍 Step 5: Enriching flight data...")
    dep = flight_data.get("departure") or {}
    arr = flight_data.get("arrival") or {}
    live = flight_data.get("live") or {}
    airline = flight_data.get("airline") or {}
    status = flight_data.get("flight_status", "unknown")

    dep_details = extract_airport_details(dep)
    arr_details = extract_airport_details(arr)
    aircraft = extract_aircraft_details(flight_data)

    dep_coords = AIRPORT_COORDS.get(dep_details["iata"], (28.5665, 77.1031))
    arr_coords = AIRPORT_COORDS.get(arr_details["iata"], (19.0896, 72.8656))
    dep_lat = dep.get("latitude") or dep_coords[0]
    dep_lon = dep.get("longitude") or dep_coords[1]
    arr_lat = arr.get("latitude") or arr_coords[0]
    arr_lon = arr.get("longitude") or arr_coords[1]
    live_lat = live.get("latitude")
    live_lon = live.get("longitude")

    # Progress
    progress = {"available": False}
    if live_lat and live_lon:
        progress = calculate_flight_progress(
            dep_lat, dep_lon, arr_lat, arr_lon, live_lat, live_lon
        )

    # Delays
    dep_delay = calculate_delay(
        dep.get("scheduled"), dep.get("actual") or dep.get("estimated")
    )
    arr_delay = calculate_delay(arr.get("scheduled"), arr.get("estimated"))

    # Countdown
    countdown = calculate_countdown(
        arr.get("estimated") or arr.get("scheduled")
    )

    # Weather
    dep_weather = get_weather(dep_lat, dep_lon, label="departure")
    arr_weather = get_weather(arr_lat, arr_lon, label="arrival")

    # Step 6: AI Summary
    print("\n🤖 Step 6: Generating AI summary...")
    ai_summary = generate_ai_summary(
        flight_data, progress, dep_delay, arr_delay, countdown
    )
    print("✅ AI summary ready!")

    # Enriched data
    enriched = {
        "flight_number": actual_flight_number,
        "airline": airline.get("name", "N/A"),
        "status": status,
        "flight_info": fi,
        "departure": dep_details,
        "arrival": arr_details,
        "aircraft": aircraft,
        "live": live,
        "progress": progress,
        "dep_delay": dep_delay,
        "arr_delay": arr_delay,
        "countdown": countdown,
        "dep_weather": dep_weather,
        "arr_weather": arr_weather,
        "ai_summary": ai_summary,
    }

    # Status label
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    status_label = {
        "active": "🟢 IN AIR",
        "scheduled": "🔵 SCHEDULED",
        "landed": "🟡 LANDED",
        "cancelled": "🔴 CANCELLED",
        "diverted": "🟣 DIVERTED",
        "delayed": "🟠 DELAYED",
    }.get(status.lower(), "⚪ UNKNOWN")

    report = (
        f"## ✈️ Flight Tracking Report\n"
        f"**Generated:** {now}\n\n"
        f"**Flight:** {actual_flight_number} | "
        f"**Airline:** {airline.get('name', 'N/A')} | "
        f"**Status:** {status_label}\n\n"
        f"**Route:** {dep_details['name']} → {arr_details['name']}\n\n"
        f"**AI Summary:** {ai_summary}"
    )

    return report, flight_map, enriched