import html
import json
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

# Coordinates for map embedding (lat, lon)
CITY_COORDS = {
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Paris": (48.8566, 2.3522),
    "Tokyo": (35.6762, 139.6503),
    "Dubai": (25.2048, 55.2708),
    "London": (51.5074, -0.1278),
    "Bangkok": (13.7563, 100.5018),
    "Singapore": (1.3521, 103.8198),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
}

# Amenity icon mapping using HTML entities
AMENITY_ICONS = {
    "WiFi": "&#128246;",       # antenna
    "wifi": "&#128246;",
    "Pool": "&#127946;",       # swimmer
    "pool": "&#127946;",
    "Gym": "&#127947;",        # weight lifter
    "gym": "&#127947;",
    "Spa": "&#9832;",          # hot springs
    "spa": "&#9832;",
    "Restaurant": "&#127860;", # fork and knife
    "restaurant": "&#127860;",
    "Bar": "&#127864;",        # cocktail
    "bar": "&#127864;",
    "Parking": "&#127359;",    # P button
    "parking": "&#127359;",
}

# Activity state icons using HTML entities
ACTIVITY_ICONS = {
    "ROUTING": "&#129504;",     # brain
    "SEARCHING": "&#128269;",   # magnifying glass
    "BOOKING": "&#127915;",     # ticket
    "RESPONDING": "&#10024;",   # sparkles
    "CLARIFYING": "&#10067;",   # question mark
    "IDLE": "&#9200;",          # clock
}


def _append_event(state: TravelState, message: str, activity: str, tool: Optional[str] = None, status: str = "IDLE") -> None:
    icon = ACTIVITY_ICONS.get(activity, "")
    event: ActivityEvent = {"state": activity, "message": message, "tool": tool, "status": status, "icon": icon}
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


def _extract_nights(query: str) -> Optional[int]:
    match = re.search(r"\b(\d{1,2})\s*(?:night|nights)\b", query, re.I)
    return int(match.group(1)) if match else None


def _wants_list_all(query: str) -> bool:
    text = query.lower()
    return any(phrase in text for phrase in ["list all", "show all", "all hotels", "all flights", "available hotels", "available flights"])


def _get_amenity_icon(amenity: str) -> str:
    return AMENITY_ICONS.get(amenity, AMENITY_ICONS.get(amenity.lower(), "&#8226;"))


def _format_hotels(hotels: List[Dict[str, Any]]) -> str:
    if not hotels:
        return (
            "<div class='tw-empty-state'>"
            "<div class='tw-empty-icon'>&#128269;</div>"
            "<div class='tw-empty-text'>No matching hotels found from the MCP hotel service.</div>"
            "<div class='tw-empty-hint'>Try a different city or adjust your budget.</div>"
            "</div>"
        )

    display_hotels = hotels[:6]
    parts = [
        '<div class="tw-section-header">'
        '<span class="tw-section-icon">&#127976;</span>'
        '<span class="tw-section-title">Hotel Options</span>'
        '<span class="tw-section-count">' + str(len(display_hotels)) + ' properties found</span>'
        '</div>',
        '<div class="tw-cards-grid">'
    ]

    for hotel in display_hotels:
        rating_val = hotel.get("rating", 0)
        stars_filled = int(round(rating_val))
        stars_html = ("&#9733;" * stars_filled) + ("&#9734;" * (5 - stars_filled))

        amenities = hotel.get("amenities", [])[:5]
        amenities_html = "".join(
            f"<span class='tw-amenity-chip'><span class='tw-amenity-icon'>{_get_amenity_icon(a)}</span>{_escape(a)}</span>"
            for a in amenities
        )

        name = _escape(hotel.get("name", "Unknown Hotel"))
        city = _escape(hotel.get("city", "Unknown"))
        country = _escape(hotel.get("country", ""))
        hotel_id = _escape(hotel.get("id", "N/A"))
        price = hotel.get("price_per_night_usd", 0)
        rooms = hotel.get("available_rooms", 0)

        # Availability badge color
        avail_class = "tw-avail-high" if rooms > 10 else "tw-avail-low" if rooms > 0 else "tw-avail-none"
        avail_text = f"{rooms} rooms available" if rooms > 0 else "Sold out"

        # Show only facts returned by the MCP service. Policy claims such as
        # cancellation and breakfast must come from the provider payload.
        extras = []
        if rating_val >= 4.0:
            extras.append("<span class='tw-info-tag tw-info-popular'>&#9733; Highly rated</span>")
        extras_html = "".join(extras)

        location_str = f"{city}, {country}" if country else city

        # Generate a gradient based on hotel name hash for visual placeholder
        name_hash = sum(ord(c) for c in name) % 360
        gradient_start = name_hash
        gradient_end = (name_hash + 40) % 360

        card = (
            f'<div class="tw-hotel-card">'
            f'  <div class="tw-card-image" style="background:linear-gradient(135deg, hsl({gradient_start},60%,65%), hsl({gradient_end},70%,55%));">'
            f'    <span class="tw-card-image-label">&#127976;</span>'
            f'  </div>'
            f'  <div class="tw-card-body">'
            f'    <div class="tw-hotel-header">'
            f'      <span class="tw-hotel-name">{name}</span>'
            f'      <span class="tw-hotel-rating" title="Rating: {rating_val}/5">{stars_html} <small>({rating_val})</small></span>'
            f'    </div>'
            f'    <div class="tw-hotel-location">&#128205; {location_str}</div>'
            f'    <div class="tw-hotel-amenities">{amenities_html}</div>'
            f'    <div class="tw-hotel-extras">{extras_html}</div>'
            f'    <div class="tw-hotel-footer">'
            f'      <div>'
            f'        <span class="tw-avail-badge {avail_class}">{avail_text}</span>'
            f'      </div>'
            f'      <div class="tw-hotel-price">'
            f'        <span class="tw-price-value">${price}</span>'
            f'        <span class="tw-price-unit">/night</span>'
            f'      </div>'
            f'    </div>'
            f'    <div class="tw-card-action-row">'
            f'      <span class="tw-hotel-id">Reference: <code>{hotel_id}</code></span>'
            f'      <span class="tw-select-btn">Select &#10132;</span>'
            f'    </div>'
            f'  </div>'
            f'</div>'
        )
        parts.append(card)

    parts.append('</div>')
    if len(hotels) > 6:
        parts.append(f'<div class="tw-more-results">+ {len(hotels) - 6} more hotels available. Refine your search for better results.</div>')
    return "\n".join(parts)


def _format_flights(flights: List[Dict[str, Any]]) -> str:
    if not flights:
        return (
            "<div class='tw-empty-state'>"
            "<div class='tw-empty-icon'>&#9992;</div>"
            "<div class='tw-empty-text'>No matching flights found from the MCP flight service.</div>"
            "<div class='tw-empty-hint'>Try different cities or dates.</div>"
            "</div>"
        )

    display_flights = flights[:6]
    parts = [
        '<div class="tw-section-header">'
        '<span class="tw-section-icon">&#9992;</span>'
        '<span class="tw-section-title">Flight Options</span>'
        '<span class="tw-section-count">' + str(len(display_flights)) + ' flights found</span>'
        '</div>',
        '<div class="tw-flight-list">'
    ]

    for flight in display_flights:
        origin_code = _escape(flight.get("origin_code") or flight.get("origin", "")[:3].upper())
        dest_code = _escape(flight.get("destination_code") or flight.get("destination", "")[:3].upper())
        airline = _escape(flight.get("airline", "Unknown Airline"))
        origin = _escape(flight.get("origin", "Unknown"))
        destination = _escape(flight.get("destination", "Unknown"))
        departure = _escape(flight.get("departure", "TBD"))
        arrival = _escape(flight.get("arrival", "TBD"))
        flight_id = _escape(flight.get("id", "N/A"))
        price = flight.get("price_usd", 0)
        seats = flight.get("seats_available", 0)

        seats_class = "tw-seats-high" if seats > 10 else "tw-seats-low" if seats > 0 else "tw-seats-none"

        stops = flight.get("stops")
        route_label = "Non-stop" if stops == 0 else f"{stops} stop(s)" if stops is not None else "Schedule details available"
        card = (
            f'<div class="tw-flight-card">'
            f'  <div class="tw-flight-top">'
            f'    <div class="tw-flight-airline-info">'
            f'      <span class="tw-airline-icon">&#9992;</span>'
            f'      <span class="tw-airline-name">{airline}</span>'
            f'    </div>'
            f'    <div class="tw-flight-price-tag">'
            f'      <span class="tw-price-amount">${price}</span>'
            f'      <span class="tw-price-label">per person</span>'
            f'    </div>'
            f'  </div>'
            f'  <div class="tw-flight-route">'
            f'    <div class="tw-route-origin">'
            f'      <div class="tw-airport-code">{origin_code}</div>'
            f'      <div class="tw-city-label">{origin}</div>'
            f'      <div class="tw-time-label">{departure}</div>'
            f'    </div>'
            f'    <div class="tw-route-connector">'
            f'      <div class="tw-route-line-visual">'
            f'        <span class="tw-dot"></span>'
            f'        <span class="tw-dash-line"></span>'
            f'        <span class="tw-plane-mid">&#9992;</span>'
            f'        <span class="tw-dash-line"></span>'
            f'        <span class="tw-dot"></span>'
            f'      </div>'
            f'      <div class="tw-route-type">{_escape(route_label)}</div>'
            f'    </div>'
            f'    <div class="tw-route-dest">'
            f'      <div class="tw-airport-code">{dest_code}</div>'
            f'      <div class="tw-city-label">{destination}</div>'
            f'      <div class="tw-time-label">{arrival}</div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="tw-flight-bottom">'
            f'    <span class="tw-seats-badge {seats_class}">&#127915; {seats} seats left</span>'
            f'    <span class="tw-flight-id">Reference: <code>{flight_id}</code></span>'
            f'    <span class="tw-select-btn">Select Flight &#10132;</span>'
            f'  </div>'
            f'</div>'
        )
        parts.append(card)

    parts.append('</div>')
    if len(flights) > 6:
        parts.append(f'<div class="tw-more-results">+ {len(flights) - 6} more flights available.</div>')
    return "\n".join(parts)


def _format_trip_summary(state: TravelState) -> str:
    """Generate a professional trip summary card for combined hotel+flight routes."""
    hotels = state.get("hotel_results", [])
    flights = state.get("flight_results", [])
    extracted = state.get("extracted", {})
    destination = extracted.get("destination", "Your Destination")
    origin = extracted.get("origin", "")
    budget = extracted.get("budget")

    best_hotel = hotels[0] if hotels else None
    best_flight = flights[0] if flights else None

    hotel_cost = best_hotel.get("price_per_night_usd", 0) if best_hotel else 0
    flight_cost = best_flight.get("price_usd", 0) if best_flight else 0
    nights = int(extracted.get("nights") or 3)

    # Map embed
    coords = CITY_COORDS.get(destination)
    map_html = ""
    if coords:
        lat, lon = coords
        map_html = (
            f'<div class="tw-map-container">'
            f'  <iframe src="https://www.openstreetmap.org/export/embed.html?bbox={lon-0.05},{lat-0.03},{lon+0.05},{lat+0.03}&layer=mapnik&marker={lat},{lon}" '
            f'    width="100%" height="200" style="border:none;border-radius:12px;" loading="lazy"></iframe>'
            f'</div>'
        )

    # Hotel summary row
    hotel_row = ""
    if best_hotel:
        h_name = _escape(best_hotel.get("name", "N/A"))
        h_rating = best_hotel.get("rating", 0)
        hotel_row = (
            f'<div class="tw-summary-row">'
            f'  <div class="tw-summary-label">&#127976; Recommended Hotel</div>'
            f'  <div class="tw-summary-value">{h_name}</div>'
            f'  <div class="tw-summary-meta">{("&#9733;" * int(h_rating))} &middot; ${hotel_cost}/night &middot; Est. {nights} nights = ${hotel_cost * nights}</div>'
            f'</div>'
        )

    # Flight summary row
    flight_row = ""
    if best_flight:
        f_airline = _escape(best_flight.get("airline", "N/A"))
        f_origin = _escape(best_flight.get("origin", ""))
        f_dest = _escape(best_flight.get("destination", ""))
        flight_row = (
            f'<div class="tw-summary-row">'
            f'  <div class="tw-summary-label">&#9992; Recommended Flight</div>'
            f'  <div class="tw-summary-value">{f_airline}</div>'
            f'  <div class="tw-summary-meta">{f_origin} &#10132; {f_dest} &middot; ${flight_cost}</div>'
            f'</div>'
        )

    est_total = (hotel_cost * nights) + flight_cost
    if budget:
        if est_total <= budget:
            budget_status = f'<span class="tw-budget-ok">&#10003; Within ${budget} budget</span>'
        else:
            budget_status = f'<span class="tw-budget-over">&#9888; ${est_total - budget} over ${budget} budget</span>'
    else:
        budget_status = ''
    readiness = "Ready to reserve" if best_hotel and best_flight else "More details needed"

    return (
        f'<div class="tw-trip-summary">'
        f'  <div class="tw-summary-header">'
        f'    <div class="tw-summary-title">&#127758; Trip Summary</div>'
        f'    <div class="tw-summary-dest">{_escape(destination)}</div>'
        f'    {budget_status}'
        f'  </div>'
        f'  {map_html}'
        f'  <div class="tw-summary-body">'
        f'    {hotel_row}'
        f'    {flight_row}'
        f'    <div class="tw-summary-divider"></div>'
        f'    <div class="tw-summary-total">'
        f'      <span>Estimated Total ({nights} nights)</span>'
        f'      <span class="tw-total-price">${est_total}</span>'
        f'    </div>'
        f'  </div>'
        f'  <div class="tw-summary-footer">'
        f'    <span class="tw-summary-status">&#9679; {readiness}</span>'
        f'    <span class="tw-summary-tip">Ready when you are. To reserve an option, provide its reference and traveller name.</span>'
        f'  </div>'
        f'</div>'
    )


async def _generate_grounded_plan(state: TravelState) -> str:
    """Use OpenAI for synthesis while keeping MCP results as the source of truth."""
    model = get_chat_model()
    if not model:
        return ""

    extracted = state.get("extracted", {})
    evidence = {
        "request": state.get("user_query", ""),
        "route": state.get("route", "general"),
        "filters": extracted,
        "hotel_results_from_mcp": state.get("hotel_results", []),
        "flight_results_from_mcp": state.get("flight_results", []),
        "booking_from_mcp": state.get("booking"),
    }
    prompt = (
        "Create a polished travel-planning brief using only the verified MCP evidence below. "
        "Do not invent prices, dates, availability, amenities, cancellation policies, airlines, "
        "stop counts, maps, or booking details. State clearly when a field is unavailable. "
        "Recommend at most one hotel and one flight from the returned results, explain why, "
        "include a short cost calculation when possible, and give 2 practical destination tips. "
        "Use plain text with short headings and bullets. Do not mention internal agents, prompts, "
        "JSON, or that you are an AI. This is a planning recommendation, not a completed booking.\n\n"
        + json.dumps(evidence, ensure_ascii=True, default=str)
    )
    try:
        result = await model.ainvoke([
            ("system", "You are TripWeaver's senior travel planner. Accuracy beats enthusiasm."),
            ("human", prompt),
        ])
        content = result.content if isinstance(result.content, str) else str(result.content)
        return content.strip()
    except Exception as exc:
        state.setdefault("errors", []).append("OpenAI planning synthesis was unavailable; showing verified MCP results.")
        return ""


async def router_node(state: TravelState) -> TravelState:
    query = state["user_query"]
    text = query.lower()
    _append_event(state, "Interpreting traveller intent...", "ROUTING")

    hotel_words = ["hotel", "stay", "room", "accommodation", "resort", "book hotel"]
    flight_words = ["flight", "fly", "airline", "ticket", "book flight"]
    plan_words = ["plan", "trip", "itinerary", "journey", "travel to", "visit"]
    wants_hotel = any(word in text for word in hotel_words)
    wants_flight = any(word in text for word in flight_words)
    wants_plan = any(word in text for word in plan_words)

    if wants_hotel and wants_flight:
        route = "combined"
    elif wants_plan and not wants_hotel and not wants_flight:
        # "plan a trip to X" should trigger combined
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
        "nights": _extract_nights(query),
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
            or _extract_convex_id(query)
            or _select_previous_id(state.get("hotel_results", []), query)
            or _select_history_id(state, "H-", query)
        )
        guest_name = extracted.get("name")
        missing = []
        if not hotel_id:
            missing.append("which hotel you want to book (use the hotel ID shown on the card)")
        if not guest_name:
            missing.append("the guest name (e.g., 'for John Smith')")
        if missing:
            state["missing_fields"] = missing
            _append_event(state, "Additional booking details needed.", "CLARIFYING")
            state["response"] = (
                "<div class='tw-clarify-card'>"
                "<div class='tw-clarify-title'>&#128221; Booking Details Required</div>"
                "<div class='tw-clarify-body'>Please provide " + " and ".join(missing) + ".</div>"
                "<div class='tw-clarify-example'>Example: <code>Book hotel H-SIN-001 for John Smith</code></div>"
                "</div>"
            )
            return state

        _append_event(state, "Booking hotel through MCP...", "BOOKING", "book_hotel", "INVOKED")
        result = await safe_call_mcp_tool("hotel", "book_hotel", {"hotel_id": hotel_id, "guest_name": guest_name})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Hotel booking failed.", "BOOKING", "book_hotel", "FAILED")
            state["response"] = f"<div class='tw-error-card'>&#9888; Hotel booking could not be completed. {_escape(result['error'])}</div>"
            return state
        state["booking"] = result["data"]
        _append_event(state, "Hotel booking confirmed!", "BOOKING", "book_hotel", "SUCCEEDED")
        return state

    if not city and not list_all:
        state["missing_fields"] = ["destination city"]
        _append_event(state, "Destination city needed for hotel search.", "CLARIFYING")
        state["response"] = (
            "<div class='tw-clarify-card'>"
            "<div class='tw-clarify-title'>&#127758; Destination Required</div>"
            "<div class='tw-clarify-body'>Which city should I search hotels in?</div>"
            "<div class='tw-clarify-example'>Try: <code>Hotels in Singapore</code> or <code>Available hotels in Bangkok</code></div>"
            "</div>"
        )
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
        _append_event(state, "Hotel MCP call failed.", "SEARCHING", tool_name, "FAILED")
        state["response"] = f"<div class='tw-error-card'>&#9888; Hotel service is currently unavailable. {_escape(result['error'])}</div>"
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
            or _extract_convex_id(query)
            or _select_previous_id(state.get("flight_results", []), query)
            or _select_history_id(state, "F-", query)
        )
        passenger_name = extracted.get("name")
        missing = []
        if not flight_id:
            missing.append("which flight you want to book (use the flight ID shown on the card)")
        if not passenger_name:
            missing.append("the passenger name (e.g., 'for John Smith')")
        if missing:
            state["missing_fields"] = missing
            _append_event(state, "Additional booking details needed.", "CLARIFYING")
            state["response"] = (
                "<div class='tw-clarify-card'>"
                "<div class='tw-clarify-title'>&#128221; Booking Details Required</div>"
                "<div class='tw-clarify-body'>Please provide " + " and ".join(missing) + ".</div>"
                "<div class='tw-clarify-example'>Example: <code>Book flight F-CMB-SIN-001 for John Smith</code></div>"
                "</div>"
            )
            return state

        _append_event(state, "Booking flight through MCP...", "BOOKING", "book_flight", "INVOKED")
        result = await safe_call_mcp_tool("flight", "book_flight", {"flight_id": flight_id, "passenger_name": passenger_name})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Flight booking failed.", "BOOKING", "book_flight", "FAILED")
            state["response"] = f"<div class='tw-error-card'>&#9888; Flight booking could not be completed. {_escape(result['error'])}</div>"
            return state
        state["booking"] = result["data"]
        _append_event(state, "Flight booking confirmed!", "BOOKING", "book_flight", "SUCCEEDED")
        return state

    if list_all and not origin and not destination:
        _append_event(state, "Listing available flights through MCP...", "SEARCHING", "list_flights", "INVOKED")
        result = await safe_call_mcp_tool("flight", "list_flights", {})
        if not result["ok"]:
            state.setdefault("errors", []).append(result["error"])
            _append_event(state, "Flight MCP call failed.", "SEARCHING", "list_flights", "FAILED")
            state["response"] = f"<div class='tw-error-card'>&#9888; Flight service is currently unavailable. {_escape(result['error'])}</div>"
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
        _append_event(state, "Route details needed for flight search.", "CLARIFYING")
        state["response"] = (
            "<div class='tw-clarify-card'>"
            "<div class='tw-clarify-title'>&#9992; Route Details Required</div>"
            "<div class='tw-clarify-body'>Please provide the " + " and ".join(missing) + " for your flight.</div>"
            "<div class='tw-clarify-example'>Try: <code>Flight from Colombo to Singapore</code> or <code>BOM to DEL</code></div>"
            "</div>"
        )
        return state

    args = {"origin": origin, "destination": destination}
    if budget:
        args["max_price_usd"] = budget
    if date:
        args["date"] = date

    _append_event(state, f"Searching flights {origin} to {destination} through MCP...", "SEARCHING", "search_flights", "INVOKED")
    result = await safe_call_mcp_tool("flight", "search_flights", args)
    if not result["ok"]:
        state.setdefault("errors", []).append(result["error"])
        _append_event(state, "Flight MCP call failed.", "SEARCHING", "search_flights", "FAILED")
        state["response"] = f"<div class='tw-error-card'>&#9888; Flight service is currently unavailable. {_escape(result['error'])}</div>"
        return state

    flights = result["data"].get("flights", [])
    state["flight_results"] = flights
    _append_event(state, f"Flight MCP returned {len(flights)} result(s).", "SEARCHING", "search_flights", "SUCCEEDED")
    return state


async def general_agent_node(state: TravelState) -> TravelState:
    _append_event(state, "Preparing travel guidance...", "RESPONDING")
    query = state["user_query"]
    model = get_chat_model()
    if model:
        try:
            result = await model.ainvoke(
                [
                    ("system",
                     "You are TripWeaver, a professional travel planning AI assistant. "
                     "Provide helpful, concise travel advice. Format responses with clear sections. "
                     "When suggesting actions, reference TripWeaver's hotel search, flight search, and booking capabilities."),
                    ("human", query),
                ]
            )
            state["response"] = result.content
            return state
        except Exception as exc:
            state.setdefault("errors", []).append(f"LLM failed: {exc}")

    # Professional HTML fallback when LLM is unavailable
    state["response"] = (
        "<div class='tw-welcome-card'>"
        "  <div class='tw-welcome-header'>"
        "    <div class='tw-welcome-icon'>&#127758;</div>"
        "    <div class='tw-welcome-title'>TripWeaver Travel Assistant</div>"
        "    <div class='tw-welcome-subtitle'>Your AI-powered travel planning companion</div>"
        "  </div>"
        "  <div class='tw-welcome-body'>"
        "    <div class='tw-welcome-note'>My AI reasoning module is currently offline, but all travel services are <strong>fully operational</strong> via MCP.</div>"
        "    <div class='tw-capability-grid'>"
        "      <div class='tw-capability'>"
        "        <span class='tw-cap-icon'>&#127976;</span>"
        "        <span class='tw-cap-title'>Search Hotels</span>"
        "        <span class='tw-cap-example'>Hotels in Singapore</span>"
        "      </div>"
        "      <div class='tw-capability'>"
        "        <span class='tw-cap-icon'>&#9992;</span>"
        "        <span class='tw-cap-title'>Find Flights</span>"
        "        <span class='tw-cap-example'>Flight from Colombo to Bangkok</span>"
        "      </div>"
        "      <div class='tw-capability'>"
        "        <span class='tw-cap-icon'>&#127758;</span>"
        "        <span class='tw-cap-title'>Plan Full Trip</span>"
        "        <span class='tw-cap-example'>Plan hotel and flight to Dubai under $600</span>"
        "      </div>"
        "      <div class='tw-capability'>"
        "        <span class='tw-cap-icon'>&#128221;</span>"
        "        <span class='tw-cap-title'>Book Instantly</span>"
        "        <span class='tw-cap-example'>Book hotel H-SIN-001 for John Smith</span>"
        "      </div>"
        "    </div>"
        "  </div>"
        "</div>"
    )
    return state


async def finalizer_node(state: TravelState) -> TravelState:
    if state.get("response"):
        _append_event(state, "Final answer ready.", "RESPONDING")
        return state

    route = state.get("route")
    parts = []

    # OpenAI explains and prioritises the verified MCP results. The structured
    # cards below remain the authoritative display for IDs, prices and times.
    if (state.get("hotel_results") or state.get("flight_results")) and not state.get("booking"):
        grounded_plan = await _generate_grounded_plan(state)
        if grounded_plan:
            parts.append(
                "<div class='tw-ai-brief'>"
                "<div class='tw-ai-brief-title'>&#10024; TripWeaver Recommendation</div>"
                f"<div class='tw-ai-brief-body'>{_escape(grounded_plan).replace(chr(10), '<br>')}</div>"
                "</div>"
            )

    if not state.get("booking") and route in ("hotel", "combined"):
        parts.append(_format_hotels(state.get("hotel_results", [])))
    if not state.get("booking") and route in ("flight", "combined"):
        parts.append(_format_flights(state.get("flight_results", [])))

    # Add trip summary for combined routes
    if not state.get("booking") and route == "combined":
        parts.append(_format_trip_summary(state))

    if state.get("booking"):
        parts.append(_format_booking(state["booking"]))

    if state.get("errors"):
        error_items = "".join(f"<li>{_escape(e)}</li>" for e in state["errors"])
        parts.append(
            f"<div class='tw-notice-card'>"
            f"<div class='tw-notice-title'>&#9888; Service Notice</div>"
            f"<ul class='tw-notice-list'>{error_items}</ul>"
            f"</div>"
        )

    state["response"] = "\n\n".join(parts)
    _append_event(state, "Final answer ready.", "RESPONDING")
    return state


def route_after_router(state: TravelState) -> str:
    return state.get("route", "general")


def _extract_id(query: str, prefix: str) -> Optional[str]:
    pattern = rf"{prefix}[A-Z]{{3}}-\d{{3}}|{prefix}[A-Z]{{3}}-[A-Z]{{3}}-\d{{3}}"
    match = re.search(pattern, query.upper())
    return match.group(0) if match else None


def _extract_convex_id(query: str) -> Optional[str]:
    """Extract long Convex-style IDs like KH75K7F6B18MPG904GB8X8WBAX7RCF9P."""
    match = re.search(r'\b[A-Z0-9]{20,40}\b', query)
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
        # Also try Convex IDs
        ids = re.findall(r'\b[A-Z0-9]{20,40}\b', history_text)
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
        reason = _escape(booking.get("reason", "Unknown reason."))
        return (
            "<div class='tw-booking-result tw-booking-failed'>"
            "  <div class='tw-booking-icon'>&#10060;</div>"
            "  <div class='tw-booking-status-title'>Booking Failed</div>"
            f"  <div class='tw-booking-reason'>{reason}</div>"
            "</div>"
        )

    is_hotel = "hotel" in booking
    conf_id = _escape(booking.get("confirmation_id", "N/A"))
    total = booking.get("total_usd", 0)

    if is_hotel:
        hotel = booking["hotel"]
        item_html = (
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>&#127976; Hotel</span>"
            f"  <span class='tw-receipt-value'>{_escape(hotel.get('name', 'N/A'))}</span>"
            f"</div>"
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>Guest</span>"
            f"  <span class='tw-receipt-value'>{_escape(booking.get('guest_name', 'N/A'))}</span>"
            f"</div>"
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>Stay</span>"
            f"  <span class='tw-receipt-value'>{booking.get('rooms', 1)} room(s), {booking.get('nights', 1)} night(s)</span>"
            f"</div>"
        )
    else:
        flight = booking["flight"]
        item_html = (
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>&#9992; Flight</span>"
            f"  <span class='tw-receipt-value'>{_escape(flight.get('airline', 'N/A'))}</span>"
            f"</div>"
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>Route</span>"
            f"  <span class='tw-receipt-value'>{_escape(flight.get('origin', ''))} &#10132; {_escape(flight.get('destination', ''))}</span>"
            f"</div>"
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>Passenger</span>"
            f"  <span class='tw-receipt-value'>{_escape(booking.get('passenger_name', 'N/A'))}</span>"
            f"</div>"
            f"<div class='tw-receipt-row'>"
            f"  <span class='tw-receipt-label'>Seats</span>"
            f"  <span class='tw-receipt-value'>{booking.get('seats', 1)}</span>"
            f"</div>"
        )

    return (
        f"<div class='tw-booking-result tw-booking-success'>"
        f"  <div class='tw-booking-icon'>&#10004;</div>"
        f"  <div class='tw-booking-status-title'>Booking Confirmed</div>"
        f"  <div class='tw-confirmation-box'>"
        f"    <span class='tw-conf-label'>Confirmation Code</span>"
        f"    <span class='tw-conf-code'>{conf_id}</span>"
        f"  </div>"
        f"  <div class='tw-receipt-body'>"
        f"    {item_html}"
        f"  </div>"
        f"  <div class='tw-receipt-total'>"
        f"    <span>Total Charged</span>"
        f"    <span class='tw-total-amount'>${total}</span>"
        f"  </div>"
        f"</div>"
    )


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)
