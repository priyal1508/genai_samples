"""Mock hotel search API — returns deterministic but varied results."""

import hashlib
import json

_HOTEL_NAMES = [
    "Grand Plaza Hotel", "Sakura Inn", "The Metropolitan",
    "Harbor View Resort", "City Center Suites", "Sunset Lodge",
]
_AMENITIES_POOL = [
    "Free WiFi", "Pool", "Gym", "Spa", "Restaurant",
    "Airport Shuttle", "Breakfast Included", "Business Center",
    "Rooftop Bar", "Room Service",
]
_BASE_PRICES = [89, 120, 175, 210, 280, 350]
_RATINGS = [3.8, 4.0, 4.2, 4.5, 4.7, 4.9]


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def search_hotels(city: str, check_in: str, check_out: str) -> str:
    """Search for available hotels in a city for given dates.

    Args:
        city: Destination city (e.g. "Tokyo").
        check_in: Check-in date in YYYY-MM-DD format.
        check_out: Check-out date in YYYY-MM-DD format.

    Returns:
        JSON string with a list of hotel options.
    """
    seed = _seed(f"{city}-{check_in}-{check_out}")
    count = (seed % 3) + 3  # 3-5 results

    hotels = []
    for i in range(count):
        idx = (seed + i * 11) % len(_HOTEL_NAMES)
        price_jitter = ((seed + i * 17) % 80) - 40  # ±$40
        # Pick 3-5 amenities deterministically
        num_amenities = 3 + (seed + i) % 3
        amenities = [
            _AMENITIES_POOL[(seed + i + j * 3) % len(_AMENITIES_POOL)]
            for j in range(num_amenities)
        ]
        hotels.append(
            {
                "name": _HOTEL_NAMES[idx],
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "price_per_night_usd": max(60, _BASE_PRICES[idx] + price_jitter),
                "rating": _RATINGS[(idx + i) % len(_RATINGS)],
                "amenities": list(set(amenities)),  # deduplicate
            }
        )

    hotels.sort(key=lambda h: -h["rating"])
    return json.dumps(hotels, indent=2)
