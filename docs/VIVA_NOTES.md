# Viva Notes

## MCP Layer

The hotel and flight services are separate MCP servers. Agents do not import the
hotel or flight data directly. They call `safe_call_mcp_tool`, which starts the
configured MCP server and invokes a named MCP tool through stdio transport.

Why this matters: a real hotel API can replace the demo hotel server by keeping
the same MCP tool contract and changing `HOTEL_MCP_COMMAND`.

## Intent Routing

The graph starts at `router_node`, extracts route signals from the user query,
and routes to:

- `hotel_agent_node`
- `flight_agent_node`
- `general_agent_node`
- both hotel and flight nodes for combined requests

The graph is not linear. It uses conditional edges, so a hotel-only request does
not waste time running the flight agent.

## Missing Inputs

Agents check required fields before calling tools:

- Hotel search needs a city.
- Flight search needs origin and destination.
- Booking needs an item ID or previous option plus passenger/guest name.

If fields are missing, the activity becomes `CLARIFYING` and the assistant asks
a follow-up question instead of guessing.

## Failure Handling

All MCP calls go through `safe_call_mcp_tool`. If a server is unavailable or a
tool errors, the agent stores the error in state and returns a friendly recovery
message. The API catches unexpected failures in the streaming endpoint and sends
a user-safe error event.

## Streaming and Activity

`/api/chat/stream` sends server-sent events:

- `activity` events for routing/searching/booking/responding
- `token` events for streamed final text
- `done` event with final metadata

The Gradio UI renders the activity events as status chips while the response
streams into the chat.
