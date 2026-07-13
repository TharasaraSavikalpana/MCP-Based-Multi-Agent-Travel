import re
from typing import Any, Dict, List, Optional

from agents.entity import ActivityEvent, TravelState
from agents.llm import get_chat_model
from agents.mcp_client import safe_call_mcp_tool


KNOWN_CITIES = [
    "Colombo",
    "Kandy",
    "Paris",
    "Tokyo",
    "Dubai",
    "London",
    "Bangkok",
    "Singapore",
    "Mumbai",
    "Delhi",
]
CITY_CODES = {
    "CMB": "Colombo",
    "BOM": "Mumbai",
    "DEL": "Delhi",
    "BKK": "Bangkok",
    "SIN": "Singapore",
    "DXB": "Dubai",
    "LHR": "London",
    "CDG": "Paris",
    "NRT": "Tokyo",
    "HND": "Tokyo",
}


def _append_event(state: TravelState, message: str, activity: str, tool: Optional[str] = None, status: str = "IDLE") -> None:
    event: ActivityEvent = {"state": activity, "message": message, "tool": tool, "status": status}
    state.setdefault("events", []).append(event)
    state["activity"] = activity
    state["tool_status"] = status
    state["selected_tool"] = tool


def _extract_city(query: str) -> Optional[str]:
    query_lower = query.lower()
    for city in KNOWN_CITIES:
        if city.lower() in query_lower:
            return city
    return None


def _extract_route(query: str) -> Dict[str, Optional[str]]:
    cities = [city for city in KNOWN_CITIES if city.lower() in query.lower()]
    codes = [code for code in CITY_CODES if re.search(rf"\b{code}\b", query, re.I)]
    origin = None
    destination = None

    from_match = re.search(r"from\s+([A-Za-z ]+?)\s+(?:to|into|towards)\s+([A-Za-z ]+)", query, re.I)
    code_match = re.search(r"\b([A-Z]{3})\b\s+(?:to|into|towards|->)\s+\b([A-Z]{3})\b", query, re.I)
    if from_match:
        origin = _normalise_city(from_match.group(1))
        destination = _normalise_city(from_match.group(2))
    elif code_match:
        origin = _normalise_city(code_match.group(1))
        destination = _normalise_city(code_match.group(2))
    elif len(cities) >= 2:
        origin, destination = cities[0], cities[1]
    elif len(codes) >= 2:
        origin, destination = CITY_CODES[codes[0].upper()], CITY_CODES[codes[1].upper()]
    elif len(cities) == 1:
        destination = cities[0]
    elif len(codes) == 1:
        destination = CITY_CODES[codes[0].upper()]

    return {"origin": origin, "destination": destination}


def _normalise_city(text: str) -> Optional[str]:
    cleaned = re.sub(r"[^A-Za-z ]", "", text).strip().lower()
    if cleaned.upper() in CITY_CODES:
        return CITY_CODES[cleaned.upper()]
    for city in KNOWN_CITIES:
        if city.lower() in cleaned or cleaned in city.lower():
            return city
    return None


def _extract_budget(query: str) -> Optional[int]:
    match = re.search(r"(?:under|below|less than|max|budget)\s*\$?\s*(\d{2,5})", query, re.I)
    if not match:
        match = re.search(r"\$\s*(\d{2,5})", query)
    return int(match.group(1)) if match else None


def _extract_name(query: str) -> Optional[str]:
    match = re.search(r"(?:for|name is|under)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", query)
    return match.group(1) if match else None


def _extract_date(query: str) -> Optional[str]:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", query)
    return match.group(1) if match else None


def _wants_list_all(query: str) -> bool:
    text = query.lower()
    return any(phrase in text for phrase in ["list all", "show all", "all hotels", "all flights", "available hotels", "available flights"])


def _format_hotels(hotels: List[Dict[str, Any]]) -> str:
    if not hotels:
        return "I could not find matching hotels from the MCP hotel service."
    lines = ["### Hotel Options"]
    for index, hotel in enumerate(hotels, start=1):
        amenities = ", ".join(hotel.get("amenities", [])[:4])
        lines.append(
            f"{index}. **{hotel['name']}** ({hotel['city']}, {hotel['country']}) - "
            f"${hotel['price_per_night_usd']}/night, {hotel['rating']} rating, "
            f"{hotel['available_rooms']} rooms available. Amenities: {amenities}. "
            f"`Hotel ID: {hotel['id']}`"
        )
    return "\n".join(lines)


def _format_flights(flights: List[Dict[str, Any]]) -> str:
    if not flights:
        return "I could not find matching flights from the MCP flight service."
    lines = ["### Flight Options"]
    for index, flight in enumerate(flights, start=1):
        lines.append(
            f"{index}. **{flight['airline']}** {flight['origin']} -> {flight['destination']} - "
            f"depart {flight['departure']}, arrive {flight['arrival']}, "
            f"${flight['price_usd']}, {flight['seats_available']} seats available. "
            f"`Flight ID: {flight['id']}`"
        )
    return "\n".join(lines)


async def router_node(state: TravelState) -> TravelState:
    query = state["user_query"]
    text = query.lower()
    _append_event(state, "Interpreting traveller intent...", "ROUTING")

    hotel_words = ["hotel", "stay", "room", "accommodation", "resort", "book hotel"]
    flight_words = ["flight", "fly", "airline", "ticket", "book flight"]
    wants_hotel = any(word in text for word in hotel_words)
    wants_flight = any(word in text for word in flight_words)

    if wants_hotel and wants_flight:
        route = "combined"
    elif wants_hotel:
        route = "hotel"
    elif wants_flight:
        route = "flight"
    else:
        route = "general"

    state["route"] = route
    state["extracted"] = {
        "city": _extract_city(query),
        "budget": _extract_budget(query),
        **_extract_route(query),
        "name": _extract_name(query),
        "date": _extract_date(query),
        "list_all": _wants_list_all(query),
    }
    return state


async def hotel_agent_node(state: TravelState) -> TravelState:
    query = state["user_query"]
    extracted = state.get("extracted", {})
    city = extracted.get("destination") if state.get("route") == "combined" else extracted.get("city") or extracted.get("destination")
    budget = extracted.get("budget")
    list_all = extracted.get("list_all")
    is_booking = "book" in query.lower() or "reserve" in query.lower()

    if is_booking:
        hotel_id = (
            _extract_id(query, "H-")
            or _select_previous_id(state.get("hotel_results", []), query)
            or _select_history_id(state, "H-", query)
        )
        guest_name = extracted.get("name")
        missing = []
        if not hotel_id:
            missing.append("which hotel you want to book, using the hotel ID or option number")
        if not guest_name:
            missing.append("guest name")
        if missing:
            state["missing_fields"] = missing
            _append_event(state, "A booking detail is missing.", "CLARIFYING")
            state["response"] = "To book the hotel, please tell me " + " and ".join(missing) + "."
            return state

        _append_event(state, "Booking hotel through MCP...", "BOOKING", "book_hotel", "INVOKED")
        result = await safe_call_mcp_tool("hotel", "book_hotel", {"hotel_id": hotel_id, "guest_name": guest_name})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Hotel booking failed gracefully.", "BOOKING", "book_hotel", "FAILED")
            state["response"] = f"I could not complete the hotel booking because the hotel service is unavailable. {result['error']}"
            return state
        state["booking"] = result["data"]
        _append_event(state, "Hotel booking confirmed.", "BOOKING", "book_hotel", "SUCCEEDED")
        return state

    if not city and not list_all:
        state["missing_fields"] = ["destination city"]
        _append_event(state, "Destination city is needed for hotel search.", "CLARIFYING")
        state["response"] = "Which city should I search hotels in?"
        return state

    tool_name = "list_hotels" if list_all and not city else "search_hotels"
    args = {"city": city} if city else {}
    if budget:
        args["max_price_usd"] = budget

    location_text = f"in {city}" if city else "from all destinations"
    _append_event(state, f"Searching hotels {location_text} through MCP...", "SEARCHING", tool_name, "INVOKED")
    result = await safe_call_mcp_tool("hotel", tool_name, args)
    if not result["ok"]:
        state.setdefault("errors", []).append(result["error"])
        _append_event(state, "Hotel MCP call failed gracefully.", "SEARCHING", tool_name, "FAILED")
        state["response"] = f"I could not search hotels right now because the hotel service is unavailable. {result['error']}"
        return state

    hotels = result["data"].get("hotels", [])
    state["hotel_results"] = hotels
    _append_event(state, f"Hotel MCP returned {len(hotels)} result(s).", "SEARCHING", tool_name, "SUCCEEDED")
    return state


async def flight_agent_node(state: TravelState) -> TravelState:
    query = state["user_query"]
    extracted = state.get("extracted", {})
    origin = extracted.get("origin")
    destination = extracted.get("destination")
    budget = extracted.get("budget")
    date = extracted.get("date")
    list_all = extracted.get("list_all")
    is_booking = "book" in query.lower() or "reserve" in query.lower()

    if is_booking:
        flight_id = (
            _extract_id(query, "F-")
            or _select_previous_id(state.get("flight_results", []), query)
            or _select_history_id(state, "F-", query)
        )
        passenger_name = extracted.get("name")
        missing = []
        if not flight_id:
            missing.append("which flight you want to book, using the flight ID or option number")
        if not passenger_name:
            missing.append("passenger name")
        if missing:
            state["missing_fields"] = missing
            _append_event(state, "A booking detail is missing.", "CLARIFYING")
            state["response"] = "To book the flight, please tell me " + " and ".join(missing) + "."
            return state

        _append_event(state, "Booking flight through MCP...", "BOOKING", "book_flight", "INVOKED")
        result = await safe_call_mcp_tool("flight", "book_flight", {"flight_id": flight_id, "passenger_name": passenger_name})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Flight booking failed gracefully.", "BOOKING", "book_flight", "FAILED")
            state["response"] = f"I could not complete the flight booking because the flight service is unavailable. {result['error']}"
            return state
        state["booking"] = result["data"]
        _append_event(state, "Flight booking confirmed.", "BOOKING", "book_flight", "SUCCEEDED")
        return state

    if list_all and not origin and not destination:
        _append_event(state, "Listing available flights through MCP...", "SEARCHING", "list_flights", "INVOKED")
        result = await safe_call_mcp_tool("flight", "list_flights", {})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Flight MCP call failed gracefully.", "SEARCHING", "list_flights", "FAILED")
            state["response"] = f"I could not list flights right now because the flight service is unavailable. {result['error']}"
            return state
        flights = result["data"].get("flights", [])
        state["flight_results"] = flights
        _append_event(state, f"Flight MCP returned {len(flights)} result(s).", "SEARCHING", "list_flights", "SUCCEEDED")
        return state

    missing = []
    if not origin:
        missing.append("origin city")
    if not destination:
        missing.append("destination city")
    if missing:
        state["missing_fields"] = missing
        _append_event(state, "Route details are needed for flight search.", "CLARIFYING")
        state["response"] = "Please tell me the " + " and ".join(missing) + " for the flight search."
        return state

    args = {"origin": origin, "destination": destination}
    if budget:
        args["max_price_usd"] = budget
    if date:
        args["date"] = date

    _append_event(state, f"Searching flights from {origin} to {destination} through MCP...", "SEARCHING", "search_flights", "INVOKED")
    result = await safe_call_mcp_tool("flight", "search_flights", args)
    if not result["ok"]:
        state.setdefault("errors", []).append(result["error"])
        _append_event(state, "Flight MCP call failed gracefully.", "SEARCHING", "search_flights", "FAILED")
        state["response"] = f"I could not search flights right now because the flight service is unavailable. {result['error']}"
        return state

    flights = result["data"].get("flights", [])
    state["flight_results"] = flights
    _append_event(state, f"Flight MCP returned {len(flights)} result(s).", "SEARCHING", "search_flights", "SUCCEEDED")
    return state


async def general_agent_node(state: TravelState) -> TravelState:
    _append_event(state, "Preparing general travel guidance...", "RESPONDING")
    query = state["user_query"]
    model = get_chat_model()
    if model:
        try:
            result = await model.ainvoke(
                [
                    ("system", "You are TripWeaver, a concise and practical travel planning assistant."),
                    ("human", query),
                ]
            )
            state["response"] = result.content
            return state
        except Exception as exc:
            state.setdefault("errors", []).append(f"LLM failed: {exc}")

    state["response"] = (
        "I can help with destination advice, hotel searches, flight searches, and bookings. "
        "For live-style hotel or flight facts I will use the MCP specialist services instead of guessing."
    )
    return state


async def finalizer_node(state: TravelState) -> TravelState:
    if state.get("response"):
        _append_event(state, "Final answer ready.", "RESPONDING")
        return state

    route = state.get("route")
    parts = ["## TripWeaver Plan"]
    if not state.get("booking") and route in ("hotel", "combined"):
        parts.append(_format_hotels(state.get("hotel_results", [])))
    if not state.get("booking") and route in ("flight", "combined"):
        parts.append(_format_flights(state.get("flight_results", [])))
    if state.get("booking"):
        parts.append(_format_booking(state["booking"]))
    if state.get("errors"):
        parts.append("### Service Notice\n" + "\n".join(f"- {error}" for error in state["errors"]))

    state["response"] = "\n\n".join(parts)
    _append_event(state, "Final answer ready.", "RESPONDING")
    return state


def route_after_router(state: TravelState) -> str:
    return state.get("route", "general")


def _extract_id(query: str, prefix: str) -> Optional[str]:
    pattern = rf"{prefix}[A-Z]{{3}}-\d{{3}}|{prefix}[A-Z]{{3}}-[A-Z]{{3}}-\d{{3}}"
    match = re.search(pattern, query.upper())
    return match.group(0) if match else None


def _select_previous_id(results: List[Dict[str, Any]], query: str) -> Optional[str]:
    index_words = {"first": 0, "second": 1, "third": 2, "1": 0, "2": 1, "3": 2}
    query_lower = query.lower()
    for word, index in index_words.items():
        if word in query_lower and index < len(results):
            return results[index].get("id")
    return None


def _select_history_id(state: TravelState, prefix: str, query: str) -> Optional[str]:
    history_text = "\n".join(message.get("content", "") for message in state.get("history", []))
    pattern = rf"{prefix}[A-Z]{{3}}-\d{{3}}|{prefix}[A-Z]{{3}}-[A-Z]{{3}}-\d{{3}}"
    ids = re.findall(pattern, history_text.upper())
    if not ids:
        return None

    index_words = {"first": 0, "second": 1, "third": 2, "1": 0, "2": 1, "3": 2}
    query_lower = query.lower()
    for word, index in index_words.items():
        if word in query_lower and index < len(ids):
            return ids[index]
    if len(ids) == 1:
        return ids[0]
    return None


def _format_booking(booking: Dict[str, Any]) -> str:
    if booking.get("status") != "confirmed":
        return "### Booking\nThe booking was not confirmed: " + booking.get("reason", "Unknown reason.")
    return (
        "### Booking Confirmed\n"
        f"Confirmation: `{booking['confirmation_id']}`\n\n"
        f"Total: **${booking['total_usd']}**"
    )
