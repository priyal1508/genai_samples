"""Mock weather API — returns deterministic but varied forecasts."""

import hashlib
import json

_CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Rainy", "Thunderstorms", "Snowy", "Foggy"]
_WIND_DESCRIPTIONS = ["Calm", "Light Breeze", "Moderate Wind", "Windy", "Strong Gusts"]


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def get_weather(city: str, date: str) -> str:
    """Get the weather forecast for a city on a given date.

    Args:
        city: City name (e.g. "Tokyo").
        date: Date in YYYY-MM-DD format.

    Returns:
        JSON string with weather forecast details.
    """
    seed = _seed(f"{city}-{date}")

    temp_base = (seed % 30) + 5  # 5-34°C range
    humidity = 30 + (seed % 60)  # 30-89%
    condition = _CONDITIONS[seed % len(_CONDITIONS)]
    wind = _WIND_DESCRIPTIONS[(seed // 7) % len(_WIND_DESCRIPTIONS)]
    wind_speed_kmh = 5 + (seed % 40)

    forecast = {
        "city": city,
        "date": date,
        "temperature_celsius": temp_base,
        "temperature_fahrenheit": round(temp_base * 9 / 5 + 32),
        "condition": condition,
        "humidity_percent": humidity,
        "wind": wind,
        "wind_speed_kmh": wind_speed_kmh,
    }
    return json.dumps(forecast, indent=2)
