from typing import Any, Dict, List, Literal, Optional, TypedDict


Intent = Literal["general", "hotel", "flight", "combined", "ambiguous"]
Activity = Literal["ROUTING", "SEARCHING", "BOOKING", "RESPONDING", "CLARIFYING"]
ToolStatus = Literal["IDLE", "INVOKED", "SUCCEEDED", "FAILED"]


class ActivityEvent(TypedDict, total=False):
    state: Activity
    message: str
    tool: Optional[str]
    status: ToolStatus


class TravelState(TypedDict, total=False):
    user_query: str
    history: List[Dict[str, str]]
    route: Intent
    activity: Activity
    tool_status: ToolStatus
    selected_tool: Optional[str]
    hotel_results: List[Dict[str, Any]]
    flight_results: List[Dict[str, Any]]
    booking: Optional[Dict[str, Any]]
    response: str
    errors: List[str]
    events: List[ActivityEvent]
    missing_fields: List[str]
    extracted: Dict[str, Any]
