import json
import os
from typing import Dict, Generator, List, Tuple

import gradio as gr
import requests
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
if not BACKEND_URL.startswith(("http://", "https://")):
    BACKEND_URL = f"https://{BACKEND_URL}"


THEME_CSS = """
:root {
  --tw-ocean: #0f766e;
  --tw-sky: #0284c7;
  --tw-sun: #f59e0b;
  --tw-ink: #102a43;
}
.gradio-container {
  background:
    radial-gradient(circle at 12% 10%, rgba(20, 184, 166, .18), transparent 28%),
    radial-gradient(circle at 88% 8%, rgba(245, 158, 11, .18), transparent 24%),
    linear-gradient(135deg, #f8fbff 0%, #eefdf8 50%, #fff7ed 100%);
  color: var(--tw-ink);
}
#hero {
  padding: 24px;
  border-radius: 8px;
  color: white;
  background:
    linear-gradient(120deg, rgba(15, 118, 110, .94), rgba(2, 132, 199, .9)),
    url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80");
  background-size: cover;
  background-position: center;
  box-shadow: 0 18px 40px rgba(15, 42, 67, .18);
}
#hero h1 { font-size: 34px; margin: 0 0 8px; letter-spacing: 0; }
#hero p { max-width: 920px; margin: 0; font-size: 16px; }
#activity-panel {
  border: 1px solid rgba(15, 118, 110, .18);
  background: rgba(255, 255, 255, .78);
  border-radius: 8px;
  padding: 14px;
}
.activity-chip {
  display: inline-block;
  margin: 4px 6px 4px 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
  font-size: 13px;
  border: 1px solid #bae6fd;
}
.activity-chip.good { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.activity-chip.warn { background: #fef3c7; color: #92400e; border-color: #fde68a; }
.quick-row button { border-radius: 8px !important; }
footer { display: none !important; }
"""


def _history_for_api(chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return chat_history[-10:] if chat_history else []


def _parse_sse_line(line: str) -> Tuple[str, Dict[str, object]]:
    event_name = "message"
    payload: Dict[str, object] = {}
    if line.startswith("event:"):
        event_name = line.replace("event:", "", 1).strip()
    if "\ndata:" in line:
        raw = line.split("\ndata:", 1)[1].strip()
        payload = json.loads(raw)
    return event_name, payload


def _activity_html(events: List[Dict[str, object]]) -> str:
    if not events:
        return "<div id='activity-panel'><b>Agent activity</b><br><span class='activity-chip'>Ready</span></div>"

    chips = []
    for event in events[-8:]:
        status = event.get("status", "IDLE")
        css = "good" if status == "SUCCEEDED" else "warn" if status == "FAILED" else ""
        chips.append(f"<span class='activity-chip {css}'>{event.get('state')}: {event.get('message')}</span>")
    return "<div id='activity-panel'><b>Agent activity</b><br>" + "".join(chips) + "</div>"


def chat_with_tripweaver(message: str, chat_history: List[Dict[str, str]]) -> Generator:
    if not message.strip():
        yield chat_history, _activity_html([])
        return

    chat_history = chat_history + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
    events: List[Dict[str, object]] = [{"state": "ROUTING", "message": "Sending request to TripWeaver...", "status": "INVOKED"}]
    yield chat_history, _activity_html(events)

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/stream",
            json={"message": message, "history": _history_for_api(chat_history)},
            stream=True,
            timeout=90,
        )
        response.raise_for_status()

        current_event = ""
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line == "":
                continue
            if raw_line.startswith("event:"):
                current_event = raw_line.replace("event:", "", 1).strip()
                continue
            if not raw_line.startswith("data:"):
                continue

            data = json.loads(raw_line.replace("data:", "", 1).strip())
            if current_event == "activity":
                events.append(data)
            elif current_event == "token":
                chat_history[-1]["content"] += data.get("text", "")
            elif current_event == "error":
                events.append({"state": "RESPONDING", "message": data.get("message"), "status": "FAILED"})
                chat_history[-1]["content"] = data.get("message", "A backend error occurred.")
            elif current_event == "done":
                events.extend(data.get("events", [])[-2:])

            yield chat_history, _activity_html(events)
    except Exception as exc:
        events.append({"state": "RESPONDING", "message": "Backend is unreachable.", "status": "FAILED"})
        chat_history[-1]["content"] = (
            "I cannot reach the TripWeaver backend right now. "
            f"Check BACKEND_URL and make sure the API is running. Details: {exc}"
        )
        yield chat_history, _activity_html(events)


def use_example(example: str) -> str:
    return example


with gr.Blocks(title="TripWeaver") as demo:
    gr.HTML(
        """
        <section id="hero">
          <h1>TripWeaver</h1>
          <p>MCP-based multi-agent travel planning with intent routing, specialist hotel and flight agents, streaming responses, and graceful service failure handling.</p>
        </section>
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=560, buttons=["copy", "copy_all"], label="Travel planning chat")
            user_input = gr.Textbox(
                placeholder="Ask for hotels, flights, bookings, or general travel advice...",
                label="Your trip request",
                lines=2,
            )
            with gr.Row(elem_classes=["quick-row"]):
                search_hotels = gr.Button("Hotels in Paris under $200")
                search_flights = gr.Button("Flights from Colombo to Tokyo")
                combined = gr.Button("Plan hotel and flight for Colombo to Paris")
            send = gr.Button("Plan my trip", variant="primary")
        with gr.Column(scale=1):
            activity = gr.HTML(_activity_html([]), label="Agent activity")
            gr.Markdown(
                """
                **Try asking**

                - Search hotels in Tokyo under $180
                - Find flights from Colombo to Dubai
                - Book hotel H-CMB-001 for Thara
                - What should I pack for Paris in August?
                """
            )

    send.click(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    user_input.submit(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    search_hotels.click(lambda: "Search hotels in Paris under $200", None, user_input)
    search_flights.click(lambda: "Find flights from Colombo to Tokyo", None, user_input)
    combined.click(lambda: "Plan hotel and flight for Colombo to Paris under $900", None, user_input)


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.getenv("FRONTEND_HOST", "0.0.0.0"),
        server_port=int(os.getenv("PORT", os.getenv("FRONTEND_PORT", "7860"))),
        css=THEME_CSS,
    )
