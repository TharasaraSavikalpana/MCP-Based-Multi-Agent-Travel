import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mcp_servers.data import HOTELS
from mcp_servers.provider_api import (
    HOTEL_API_BASE,
    city_matches,
    extract_items,
    fetch_json,
    normalize_hotel,
)


mcp = FastMCP("tripweaver-hotel-service")


@mcp.tool()
def list_hotels(city: Optional[str] = None) -> str:
    """List available hotels, optionally filtered by city."""
    live_payload = fetch_json(HOTEL_API_BASE)
    live_hotels = [normalize_hotel(item, index) for index, item in enumerate(extract_items(live_payload, "hotels"), start=1)]

    hotels = live_hotels or HOTELS
    if city:
        hotels = [hotel for hotel in hotels if city_matches(hotel.get("city"), city)]
    return json.dumps({"hotels": hotels, "count": len(hotels), "source": "live" if live_hotels else "fallback"})


@mcp.tool()
def search_hotels(
    city: str,
    max_price_usd: Optional[int] = None,
    min_rating: Optional[float] = None,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
) -> str:
    """Search hotels by city, budget, and rating."""
    params = {"city": city}
    if check_in:
        params["checkIn"] = check_in
    if check_out:
        params["checkOut"] = check_out

    live_payload = fetch_json(f"{HOTEL_API_BASE}/search", params=params)
    live_hotels = [normalize_hotel(item, index) for index, item in enumerate(extract_items(live_payload, "hotels"), start=1)]
    results = live_hotels or [hotel for hotel in HOTELS if city_matches(hotel.get("city"), city)]

    if max_price_usd is not None:
        results = [hotel for hotel in results if hotel["price_per_night_usd"] <= max_price_usd]
    if min_rating is not None:
        results = [hotel for hotel in results if hotel["rating"] >= min_rating]
    return json.dumps({"hotels": results, "count": len(results), "source": "live" if live_hotels else "fallback"})


@mcp.tool()
def book_hotel(hotel_id: str, guest_name: str, nights: int = 1, rooms: int = 1) -> str:
    """Book a hotel and return a confirmation."""
    all_hotels_payload = fetch_json(HOTEL_API_BASE)
    live_hotels = [normalize_hotel(item, index) for index, item in enumerate(extract_items(all_hotels_payload, "hotels"), start=1)]
    hotels = live_hotels or HOTELS
    hotel = next((item for item in hotels if item["id"].upper() == hotel_id.upper()), None)
    if hotel is None:
        return json.dumps({"status": "rejected", "reason": "Hotel ID was not found."})
    if hotel["available_rooms"] < rooms:
        return json.dumps({"status": "rejected", "reason": "Not enough rooms are available."})

    total = hotel["price_per_night_usd"] * nights * rooms
    return json.dumps(
        {
            "status": "confirmed",
            "confirmation_id": f"TW-HOTEL-{hotel_id[-3:]}-{rooms}{nights}",
            "hotel": hotel,
            "guest_name": guest_name,
            "nights": nights,
            "rooms": rooms,
            "total_usd": total,
        }
    )


if __name__ == "__main__":
    mcp.run()
