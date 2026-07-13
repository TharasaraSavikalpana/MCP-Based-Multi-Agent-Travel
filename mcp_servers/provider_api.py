from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import requests


HOTEL_API_BASE = os.getenv("HOTEL_API_BASE", "https://standing-fish-574.convex.site/hotels").rstrip("/")
FLIGHT_API_BASE = os.getenv("FLIGHT_API_BASE", "https://standing-fish-574.convex.site/flights").rstrip("/")
PROVIDER_MODE = os.getenv("TRAVEL_PROVIDER_MODE", "live_with_fallback")


CITY_CODE_MAP = {
    "BOM": "Mumbai",
    "DEL": "Delhi",
    "CMB": "Colombo",
    "BKK": "Bangkok",
    "SIN": "Singapore",
    "DXB": "Dubai",
    "LHR": "London",
    "NRT": "Tokyo",
    "HND": "Tokyo",
    "CDG": "Paris",
}


def fetch_json(url: str, params: Optional[dict] = None) -> Optional[Any]:
    if PROVIDER_MODE == "offline":
        return None

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def extract_items(payload: Optional[Any], key: str) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get(key, payload.get("data", payload.get("items", [])))
        return value if isinstance(value, list) else []
    if isinstance(payload, list):
        return payload
    return []


def normalize_city(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("city") or value.get("airport") or value.get("code") or ""
    text = str(value or "").strip()
    return CITY_CODE_MAP.get(text.upper(), text)


def city_matches(candidate: Any, expected: Optional[str]) -> bool:
    if not expected:
        return True
    candidate_city = normalize_city(candidate).lower()
    expected_city = normalize_city(expected).lower()
    return candidate_city == expected_city or expected_city in candidate_city or candidate_city in expected_city


def code_or_city_matches(candidate: Any, expected: Optional[str]) -> bool:
    if not expected:
        return True
    if isinstance(candidate, dict):
        raw_values = [candidate.get("code"), candidate.get("airport"), candidate.get("city"), candidate.get("name")]
    else:
        raw_values = [candidate]
    raw_values = [str(item or "").strip().lower() for item in raw_values]
    normalized_expected = normalize_city(expected).lower()
    expected_lower = str(expected or "").strip().lower()
    return any(value in {expected_lower, normalized_expected} for value in raw_values) or any(
        normalize_city(value).lower() == normalized_expected for value in raw_values
    )


def first_value(item: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def normalize_hotel(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    city = normalize_city(first_value(item, ["city", "location"], "Unknown"))
    price = first_value(item, ["price_per_night_usd", "pricePerNight", "price", "nightlyPrice"], 0)
    try:
        price = int(float(price))
    except Exception:
        price = 0

    rating = first_value(item, ["rating", "stars", "starRating"], 0)
    try:
        rating = float(rating)
    except Exception:
        rating = 0.0

    available = first_value(item, ["available_rooms", "availableRooms", "available", "rooms"], 1)
    try:
        available = int(available)
    except Exception:
        available = 1

    amenities = first_value(item, ["amenities", "features"], [])
    if isinstance(amenities, str):
        amenities = [amenity.strip() for amenity in amenities.split(",") if amenity.strip()]

    return {
        "id": str(first_value(item, ["id", "_id", "hotelId"], f"H-LIVE-{index:03d}")).upper(),
        "name": str(first_value(item, ["name", "hotelName", "title"], "Unknown hotel")),
        "city": city,
        "country": str(first_value(item, ["country"], "Unknown")),
        "price_per_night_usd": price,
        "rating": rating,
        "available_rooms": available,
        "amenities": amenities or ["provider result"],
        "source": "live-provider",
    }


def normalize_flight(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    origin = normalize_city(first_value(item, ["origin", "from"], "Unknown"))
    destination = normalize_city(first_value(item, ["destination", "to"], "Unknown"))
    price = first_value(item, ["price_usd", "price", "fare"], 0)
    try:
        price = int(float(price))
    except Exception:
        price = 0

    seats = first_value(item, ["seats_available", "availableSeats", "available_seats", "seats"], 1)
    try:
        seats = int(seats)
    except Exception:
        seats = 1

    departure_date = first_value(item, ["flightDate", "date", "departure_date"], "")
    departure_time = first_value(item, ["departure", "departureTime", "departure_time"], "")
    arrival_time = first_value(item, ["arrival", "arrivalTime", "arrival_time"], "")
    departure = " ".join(part for part in [departure_date, departure_time] if part).strip() or "Time not provided"
    arrival = arrival_time or "Time not provided"

    return {
        "id": str(first_value(item, ["id", "_id", "flightId", "flightNumber", "flightNo"], f"F-LIVE-{index:03d}")).upper(),
        "airline": str(first_value(item, ["airline", "carrier"], "Unknown airline")),
        "origin": origin,
        "destination": destination,
        "origin_code": str(first_value(item, ["originCode", "origin_code"], "")),
        "destination_code": str(first_value(item, ["destinationCode", "destination_code"], "")),
        "departure": departure,
        "arrival": arrival,
        "price_usd": price,
        "seats_available": seats,
        "source": "live-provider",
    }
