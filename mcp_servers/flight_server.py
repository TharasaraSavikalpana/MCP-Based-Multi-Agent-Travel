import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mcp_servers.data import FLIGHTS
from mcp_servers.provider_api import (
    FLIGHT_API_BASE,
    code_or_city_matches,
    extract_items,
    fetch_json,
    normalize_flight,
)


mcp = FastMCP("tripweaver-flight-service")


@mcp.tool()
def list_flights(origin: Optional[str] = None, destination: Optional[str] = None) -> str:
    """List available flights, optionally filtered by origin and destination."""
    live_payload = fetch_json(FLIGHT_API_BASE)
    live_flights = [normalize_flight(item, index) for index, item in enumerate(extract_items(live_payload, "flights"), start=1)]

    flights = live_flights or FLIGHTS
    if origin:
        flights = [
            flight
            for flight in flights
            if code_or_city_matches(flight.get("origin"), origin) or code_or_city_matches(flight.get("origin_code"), origin)
        ]
    if destination:
        flights = [
            flight
            for flight in flights
            if code_or_city_matches(flight.get("destination"), destination)
            or code_or_city_matches(flight.get("destination_code"), destination)
        ]
    return json.dumps({"flights": flights, "count": len(flights), "source": "live" if live_flights else "fallback"})


@mcp.tool()
def search_flights(
    origin: str,
    destination: str,
    max_price_usd: Optional[int] = None,
    date: Optional[str] = None,
) -> str:
    """Search flights by route and optional budget."""
    params = {"origin": origin.upper() if len(origin) == 3 else origin, "destination": destination.upper() if len(destination) == 3 else destination}
    if date:
        params["date"] = date

    live_payload = fetch_json(f"{FLIGHT_API_BASE}/search", params=params)
    live_flights = [normalize_flight(item, index) for index, item in enumerate(extract_items(live_payload, "flights"), start=1)]
    results = [
        flight
        for flight in (live_flights or FLIGHTS)
        if (code_or_city_matches(flight.get("origin"), origin) or code_or_city_matches(flight.get("origin_code"), origin))
        and (
            code_or_city_matches(flight.get("destination"), destination)
            or code_or_city_matches(flight.get("destination_code"), destination)
        )
    ]
    if max_price_usd is not None:
        results = [flight for flight in results if flight["price_usd"] <= max_price_usd]
    return json.dumps({"flights": results, "count": len(results), "source": "live" if live_flights else "fallback"})


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str, seats: int = 1) -> str:
    """Book a flight and return a confirmation."""
    live_payload = fetch_json(FLIGHT_API_BASE)
    live_flights = [normalize_flight(item, index) for index, item in enumerate(extract_items(live_payload, "flights"), start=1)]
    flights = live_flights or FLIGHTS
    flight = next((item for item in flights if item["id"].upper() == flight_id.upper()), None)
    if flight is None:
        return json.dumps({"status": "rejected", "reason": "Flight ID was not found."})
    if flight["seats_available"] < seats:
        return json.dumps({"status": "rejected", "reason": "Not enough seats are available."})

    total = flight["price_usd"] * seats
    return json.dumps(
        {
            "status": "confirmed",
            "confirmation_id": f"TW-FLIGHT-{flight_id[-3:]}-{seats}",
            "flight": flight,
            "passenger_name": passenger_name,
            "seats": seats,
            "total_usd": total,
        }
    )


if __name__ == "__main__":
    mcp.run()
