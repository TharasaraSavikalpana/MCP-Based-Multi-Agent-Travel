from agents.entity import TravelState
from agents.nodes import (
    finalizer_node,
    flight_agent_node,
    general_agent_node,
    hotel_agent_node,
    route_after_router,
    router_node,
)


class FallbackTravelGraph:
    """Small fallback runner used only if LangGraph is unavailable locally."""

    async def ainvoke(self, state: TravelState) -> TravelState:
        state = await router_node(state)
        route = state.get("route", "general")
        if route == "hotel":
            state = await hotel_agent_node(state)
        elif route == "flight":
            state = await flight_agent_node(state)
        elif route == "combined":
            state = await hotel_agent_node(state)
            if not state.get("response"):
                state = await flight_agent_node(state)
        else:
            state = await general_agent_node(state)
        return await finalizer_node(state)


def build_graph():
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return FallbackTravelGraph()

    graph = StateGraph(TravelState)
    graph.add_node("router", router_node)
    graph.add_node("hotel_agent", hotel_agent_node)
    graph.add_node("flight_agent", flight_agent_node)
    graph.add_node("general_agent", general_agent_node)
    graph.add_node("finalizer", finalizer_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "hotel": "hotel_agent",
            "flight": "flight_agent",
            "general": "general_agent",
            "combined": "hotel_agent",
            "ambiguous": "general_agent",
        },
    )
    graph.add_conditional_edges(
        "hotel_agent",
        lambda state: "finalizer" if state.get("route") != "combined" or state.get("response") else "flight_agent",
        {"flight_agent": "flight_agent", "finalizer": "finalizer"},
    )
    graph.add_edge("flight_agent", "finalizer")
    graph.add_edge("general_agent", "finalizer")
    graph.add_edge("finalizer", END)
    return graph.compile()


travel_graph = build_graph()
