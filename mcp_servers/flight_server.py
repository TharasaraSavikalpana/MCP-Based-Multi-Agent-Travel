import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mcp_servers.data import FLIGHTS


mcp = FastMCP("tripweaver-flight-service")


@mcp.tool()
def list_flights(origin: Optional[str] = None, destination: Optional[str] = None) -> str:
    """List available flights, optionally filtered by origin and destination."""
    flights = FLIGHTS
    if origin:
        flights = [flight for flight in flights if flight["origin"].lower() == origin.lower()]
    if destination:
        flights = [flight for flight in flights if flight["destination"].lower() == destination.lower()]
    return json.dumps({"flights": flights, "count": len(flights)})


@mcp.tool()
def search_flights(origin: str, destination: str, max_price_usd: Optional[int] = None) -> str:
    """Search flights by route and optional budget."""
    results = [
        flight
        for flight in FLIGHTS
        if flight["origin"].lower() == origin.lower()
        and flight["destination"].lower() == destination.lower()
    ]
    if max_price_usd is not None:
        results = [flight for flight in results if flight["price_usd"] <= max_price_usd]
    return json.dumps({"flights": results, "count": len(results)})


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str, seats: int = 1) -> str:
    """Book a flight and return a confirmation."""
    flight = next((item for item in FLIGHTS if item["id"] == flight_id), None)
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
