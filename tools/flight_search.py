"""Mock flight search API — returns deterministic but varied results."""

import hashlib
import json

_AIRLINES = ["SkyWay Airlines", "Pacific Air", "Global Express", "Horizon Flights", "Atlas Airways"]
_BASE_PRICES = [320, 450, 580, 710, 890]
_DEPARTURE_HOURS = ["06:00", "09:30", "12:15", "15:45", "19:00"]
_DURATIONS = ["4h 20m", "6h 45m", "8h 10m", "10h 30m", "13h 15m"]


def _seed(text: str) -> int:
    """Create a stable integer seed from text."""
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights between two cities on a given date.

    Args:
        origin: Departure city (e.g. "New York").
        destination: Arrival city (e.g. "Tokyo").
        date: Travel date in YYYY-MM-DD format.

    Returns:
        JSON string with a list of flight options.
    """
    seed = _seed(f"{origin}-{destination}-{date}")
    count = (seed % 3) + 3  # 3-5 results

    flights = []
    for i in range(count):
        idx = (seed + i * 7) % len(_AIRLINES)
        price_jitter = ((seed + i * 13) % 200) - 100  # ±$100
        flights.append(
            {
                "airline": _AIRLINES[idx],
                "flight_no": f"{_AIRLINES[idx][:2].upper()}{100 + (seed + i) % 900}",
                "origin": origin,
                "destination": destination,
                "date": date,
                "departure": _DEPARTURE_HOURS[(idx + i) % len(_DEPARTURE_HOURS)],
                "duration": _DURATIONS[(idx + i * 3) % len(_DURATIONS)],
                "price_usd": max(150, _BASE_PRICES[idx] + price_jitter),
                "class": "Economy",
            }
        )

    # Sort by price
    flights.sort(key=lambda f: f["price_usd"])
    return json.dumps(flights, indent=2)
