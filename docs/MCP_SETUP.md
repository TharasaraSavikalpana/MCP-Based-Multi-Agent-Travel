# TripWeaver MCP Server Setup

TripWeaver keeps hotel and flight service logic outside the agent graph. The
agents call MCP tools through `agents/mcp_client.py`; the provider-specific
logic lives in standalone MCP servers under `mcp_servers/`.

The MCP servers use these external service links by default:

```text
https://standing-fish-574.convex.site/hotels
https://standing-fish-574.convex.site/flights
```

If the live provider is unavailable, the MCP servers fall back to local demo data
so the conversation and viva demo keep working.

## MCP Tools

Hotel MCP server: `mcp_servers/hotel_server.py`

- `list_hotels(city: Optional[str])`
- `search_hotels(city: str, max_price_usd: Optional[int], min_rating: Optional[float])`
- `book_hotel(hotel_id: str, guest_name: str, nights: int, rooms: int)`

Flight MCP server: `mcp_servers/flight_server.py`

- `list_flights(origin: Optional[str], destination: Optional[str])`
- `search_flights(origin: str, destination: str, max_price_usd: Optional[int])`
- `book_flight(flight_id: str, passenger_name: str, seats: int)`

Each tool returns structured JSON as a string so the MCP client can decode it
reliably into the shared agent state.

## Local Commands

The backend starts MCP servers as stdio subprocesses when a tool is needed.
Defaults:

```bash
python mcp_servers/hotel_server.py
python mcp_servers/flight_server.py
```

Optional `.env` overrides:

```bash
HOTEL_MCP_COMMAND="python mcp_servers/hotel_server.py"
FLIGHT_MCP_COMMAND="python mcp_servers/flight_server.py"
HOTEL_API_BASE="https://standing-fish-574.convex.site/hotels"
FLIGHT_API_BASE="https://standing-fish-574.convex.site/flights"
TRAVEL_PROVIDER_MODE="live_with_fallback"
```

## Swapping Providers

To replace demo data with a real provider:

1. Keep the same tool names and JSON output shape.
2. Put API keys in deployment secrets, not source code.
3. Update `HOTEL_MCP_COMMAND` or `FLIGHT_MCP_COMMAND` to launch the new server.
4. Do not edit `agents/nodes.py` or `agents/graph.py`.

That proves the MCP bridge decouples external services from the agent workflow.
