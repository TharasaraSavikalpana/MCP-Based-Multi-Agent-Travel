import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mcp_servers.data import HOTELS


mcp = FastMCP("tripweaver-hotel-service")


@mcp.tool()
def list_hotels(city: Optional[str] = None) -> str:
    """List available hotels, optionally filtered by city."""
    hotels = HOTELS
    if city:
        hotels = [hotel for hotel in hotels if hotel["city"].lower() == city.lower()]
    return json.dumps({"hotels": hotels, "count": len(hotels)})


@mcp.tool()
def search_hotels(city: str, max_price_usd: Optional[int] = None, min_rating: Optional[float] = None) -> str:
    """Search hotels by city, budget, and rating."""
    results = [hotel for hotel in HOTELS if hotel["city"].lower() == city.lower()]
    if max_price_usd is not None:
        results = [hotel for hotel in results if hotel["price_per_night_usd"] <= max_price_usd]
    if min_rating is not None:
        results = [hotel for hotel in results if hotel["rating"] >= min_rating]
    return json.dumps({"hotels": results, "count": len(results)})


@mcp.tool()
def book_hotel(hotel_id: str, guest_name: str, nights: int = 1, rooms: int = 1) -> str:
    """Book a hotel and return a confirmation."""
    hotel = next((item for item in HOTELS if item["id"] == hotel_id), None)
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
