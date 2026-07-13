import html
import json
import os
from typing import Any, Dict, Generator, List

import gradio as gr
import requests
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
if not BACKEND_URL.startswith(("http://", "https://")):
    BACKEND_URL = f"https://{BACKEND_URL}"


THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&display=swap');

:root {
  --tw-font: 'Plus Jakarta Sans', sans-serif;
  --tw-ink: #0f172a;
  --tw-muted: #64748b;
  --tw-card: rgba(255, 255, 255, 0.85);
  --tw-border: rgba(15, 23, 42, 0.08);
  --tw-ocean: #0ea5e9;
  --tw-sky: #0284c7;
  --tw-mint: #10b981;
  --tw-coral: #f97316;
  --tw-gold: #f59e0b;
  --tw-bg-grad: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0fdf4 100%);
  --tw-hero-grad: linear-gradient(135deg, #0369a1 0%, #0284c7 40%, #0e7490 100%);
}

body, .gradio-container {
  font-family: var(--tw-font) !important;
  min-height: 100vh;
  background: var(--tw-bg-grad) !important;
  color: var(--tw-ink);
}

.main {
  max-width: 1400px !important;
  margin: 0 auto;
  padding: 20px 0;
}

#hero {
  position: relative;
  overflow: hidden;
  padding: 40px;
  border-radius: 20px;
  color: white;
  background: var(--tw-hero-grad);
  box-shadow: 0 20px 40px rgba(2, 132, 199, 0.15);
  margin-bottom: 25px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

#hero h1 {
  font-size: 52px;
  font-weight: 800;
  margin: 0 0 10px;
  letter-spacing: -1px;
  background: linear-gradient(to right, #ffffff, #e0f2fe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

#hero p {
  max-width: 750px;
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: #e0f2fe;
}

#hero .badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}

#hero .stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 25px;
}

#hero .stat {
  padding: 8px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
}

.panel {
  border-radius: 20px !important;
  border: 1px solid var(--tw-border) !important;
  background: var(--tw-card) !important;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.05) !important;
  backdrop-filter: blur(20px);
  padding: 20px !important;
}

#activity-panel {
  min-height: 200px;
  border: 1px solid rgba(14, 165, 233, 0.15);
  background: rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 10px 25px rgba(14, 165, 233, 0.05);
  backdrop-filter: blur(10px);
}

#activity-panel b {
  display: block;
  margin-bottom: 12px;
  color: var(--tw-ink);
  font-size: 16px;
  font-weight: 700;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  padding-bottom: 8px;
}

.activity-chip {
  display: flex;
  align-items: center;
  margin: 10px 0;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f0f9ff;
  color: #0369a1;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #bae6fd;
  transition: all 0.2s ease;
}

.activity-chip.good { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
.activity-chip.warn { background: #fff7ed; color: #c2410c; border-color: #ffedd5; }
.activity-chip.run {
  background: #fefce8;
  color: #a16207;
  border-color: #fef08a;
  animation: pulse-border 1.5s infinite;
}

@keyframes pulse-border {
  0% { border-color: #fef08a; box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.2); }
  70% { border-color: #eab308; box-shadow: 0 0 0 6px rgba(234, 179, 8, 0); }
  100% { border-color: #fef08a; box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); }
}

.quick-row button {
  border-radius: 12px !important;
  min-height: 48px !important;
  font-weight: 700 !important;
  border: 1px solid rgba(15, 23, 42, 0.08) !important;
  background: #ffffff !important;
  color: var(--tw-ink) !important;
  box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
  transition: all 0.2s ease !important;
}

.quick-row button:hover {
  transform: translateY(-2px) !important;
  border-color: var(--tw-ocean) !important;
  box-shadow: 0 6px 12px rgba(14, 165, 233, 0.1) !important;
}

button.primary, #send-btn {
  min-height: 50px !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
  border: none !important;
  color: #ffffff !important;
  font-weight: 750 !important;
  font-size: 15px !important;
  box-shadow: 0 10px 20px rgba(2, 132, 199, 0.2) !important;
  transition: all 0.2s ease !important;
}

button.primary:hover, #send-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 24px rgba(2, 132, 199, 0.3) !important;
}

textarea, input {
  border-radius: 12px !important;
  border: 1px solid rgba(15, 23, 42, 0.1) !important;
  padding: 12px !important;
  font-size: 14px !important;
}

textarea:focus, input:focus {
  border-color: var(--tw-ocean) !important;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
}

.pro-note {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--tw-border);
  color: var(--tw-muted);
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 8px 20px rgba(0,0,0,0.02);
  margin-top: 20px;
}

.pro-note b {
  color: var(--tw-ink);
  font-size: 15px;
  display: block;
  margin-bottom: 8px;
}

/* RESULTS LAYOUT STYLES */
.tw-results-title {
  font-size: 18px;
  font-weight: 850;
  color: var(--tw-ink);
  margin: 20px 0 10px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--tw-ocean);
  display: inline-block;
}

.tw-no-results {
  color: var(--tw-muted);
  font-style: italic;
  padding: 15px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px dashed rgba(0,0,0,0.05);
}

.tw-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 10px;
}

/* Hotel Card */
.tw-hotel-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  padding: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.tw-hotel-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.tw-hotel-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--tw-mint);
}

.tw-hotel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.tw-hotel-name {
  font-size: 15px;
  font-weight: 750;
  color: var(--tw-ink);
  line-height: 1.3;
}

.tw-hotel-rating {
  font-size: 12px;
  color: #f59e0b;
  font-weight: 700;
  white-space: nowrap;
}

.tw-hotel-location {
  font-size: 13px;
  color: var(--tw-muted);
  margin-bottom: 12px;
}

.tw-hotel-amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.tw-amenity-badge {
  font-size: 11px;
  background: #f1f5f9;
  color: #475569;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.tw-hotel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  border-top: 1px solid rgba(0,0,0,0.04);
  padding-top: 12px;
}

.tw-hotel-rooms {
  font-size: 12px;
  color: #059669;
  font-weight: 600;
}

.tw-hotel-price {
  text-align: right;
}

.tw-price-value {
  font-size: 18px;
  font-weight: 800;
  color: var(--tw-ink);
}

.tw-price-unit {
  font-size: 12px;
  color: var(--tw-muted);
}

.tw-hotel-id, .tw-flight-id {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 8px;
  text-align: right;
}

.tw-hotel-id code, .tw-flight-id code {
  background: #f8fafc;
  padding: 2px 4px;
  border-radius: 4px;
  color: #64748b;
  font-weight: 600;
}

/* Flight Card */
.tw-flight-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  padding: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.tw-flight-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  border-color: rgba(14, 165, 233, 0.2);
}

.tw-flight-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--tw-ocean);
}

.tw-flight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tw-flight-airline {
  font-size: 14px;
  font-weight: 750;
  color: var(--tw-ink);
}

.tw-flight-price {
  font-size: 18px;
  font-weight: 800;
  color: var(--tw-ocean);
}

.tw-flight-route {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 12px;
}

.tw-route-point {
  display: flex;
  flex-direction: column;
}

.tw-airport-code {
  font-size: 18px;
  font-weight: 800;
  color: var(--tw-ink);
  letter-spacing: 0.5px;
}

.tw-city-name {
  font-size: 11px;
  color: var(--tw-muted);
  margin-top: 2px;
}

.tw-route-line {
  flex-grow: 1;
  text-align: center;
  position: relative;
  margin: 0 10px;
}

.tw-line-arrow {
  font-size: 16px;
  color: #94a3b8;
}

.tw-flight-times {
  font-size: 12px;
  color: #475569;
  margin-bottom: 12px;
}

.tw-time-row {
  display: flex;
  justify-content: space-between;
  margin: 4px 0;
}

.tw-time-row span {
  color: var(--tw-muted);
}

.tw-flight-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid rgba(0,0,0,0.04);
  padding-top: 10px;
  margin-top: auto;
}

.tw-flight-seats {
  font-size: 11px;
  color: #d97706;
  font-weight: 600;
  background: #fffbeb;
  padding: 3px 8px;
  border-radius: 6px;
}

/* Booking Card */
.tw-booking-card {
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.05);
  margin: 15px 0;
  max-width: 480px;
}

.tw-booking-card.success {
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  border-left: 5px solid var(--tw-mint);
}

.tw-booking-card.error {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
  border-left: 5px solid #ef4444;
}

.tw-booking-header {
  font-size: 18px;
  font-weight: 800;
  color: #065f46;
  margin-bottom: 15px;
}

.tw-booking-confirmation {
  background: #ffffff;
  border: 1px solid #d1fae5;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 15px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.01);
}

.tw-booking-label {
  font-size: 11px;
  color: var(--tw-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
}

.tw-booking-code {
  font-size: 20px;
  font-weight: 850;
  color: #047857;
  letter-spacing: 1px;
  margin-top: 4px;
}

.tw-booking-details {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  padding: 12px 0;
  border-top: 1px solid rgba(0,0,0,0.04);
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.tw-booking-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.tw-booking-total span {
  font-size: 13px;
  font-weight: 700;
  color: var(--tw-muted);
}

.tw-total-value {
  font-size: 22px;
  font-weight: 850;
  color: #047857;
}

footer { display: none !important; }
"""


def _message_content(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("text", value.get("content", ""))
    if isinstance(value, list):
        value = " ".join(_message_content(item) for item in value)
    return str(value or "").strip()


def _history_for_api(chat_history: Any) -> List[Dict[str, str]]:
    clean_history: List[Dict[str, str]] = []
    if not isinstance(chat_history, list):
        return clean_history

    for item in chat_history[-12:]:
        role = None
        content = None
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
        elif hasattr(item, "role") and hasattr(item, "content"):
            role = item.role
            content = item.content
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            for r, c in [("user", item[0]), ("assistant", item[1])]:
                text = _message_content(c)
                if text:
                    clean_history.append({"role": r, "content": text})
            continue
        else:
            continue

        if role and content:
            role_str = str(role).strip().lower()
            content_str = _message_content(content)
            if role_str in {"user", "assistant", "system"} and content_str:
                clean_history.append({"role": role_str, "content": content_str})

    return clean_history[-10:]


def _activity_html(events: List[Dict[str, object]]) -> str:
    if not events:
        return "<div id='activity-panel'><b>Agent Activity</b><span class='activity-chip good'>READY: Waiting for your trip request.</span></div>"

    chips = []
    for event in events[-8:]:
        status = event.get("status", "IDLE")
        css = "good" if status == "SUCCEEDED" else "warn" if status == "FAILED" else "run" if status == "INVOKED" else ""
        state = html.escape(str(event.get("state", "STATUS")))
        message = html.escape(str(event.get("message", "")))
        chips.append(f"<span class='activity-chip {css}'>{state}: {message}</span>")
    return "<div id='activity-panel'><b>Agent Activity</b>" + "".join(chips) + "</div>"


def chat_with_tripweaver(message: str, chat_history: List[Dict[str, str]]) -> Generator:
    message = _message_content(message)
    chat_history = chat_history if isinstance(chat_history, list) else []
    if not message:
        yield chat_history, _activity_html([])
        return

    api_history = _history_for_api(chat_history)
    chat_history = chat_history + [{"role": "user", "content": message}, {"role": "assistant", "content": ""}]
    events: List[Dict[str, object]] = [{"state": "ROUTING", "message": "Sending request to TripWeaver...", "status": "INVOKED"}]
    yield chat_history, _activity_html(events)

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat/stream",
            json={"message": message, "history": api_history},
            stream=True,
            timeout=90,
        )
        if response.status_code >= 400:
            detail = response.text[:600]
            raise RuntimeError(f"{response.status_code} response from backend: {detail}")

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
            "TripWeaver could not complete this request. Make sure the FastAPI backend is running "
            f"and BACKEND_URL is correct. Details: {exc}"
        )
        yield chat_history, _activity_html(events)


def use_example(example: str) -> str:
    return example


with gr.Blocks(title="TripWeaver") as demo:
    gr.HTML(
        """
        <section id="hero">
          <div class="badge">MCP Powered Multi-Agent Travel Intelligence</div>
          <h1>TripWeaver</h1>
          <p>Plan hotels, flights, and bookings through one premium conversational workspace. TripWeaver routes each request to specialist agents, calls external travel services through MCP, and streams the journey back with clear activity signals.</p>
          <div class="stats">
            <div class="stat">Intent-Routed LangGraph</div>
            <div class="stat">Hotel + Flight MCP Servers</div>
            <div class="stat">Live Provider + Fallback</div>
            <div class="stat">Streaming FastAPI</div>
          </div>
        </section>
        """
    )

    with gr.Row():
        with gr.Column(scale=3, elem_classes=["panel"]):
            chatbot = gr.Chatbot(
                height=560,
                buttons=["copy", "copy_all"],
                label="Travel planning chat",
                sanitize_html=False,
            )
            user_input = gr.Textbox(
                placeholder="Ask for hotels, flights, bookings, or general travel advice...",
                label="Your trip request",
                lines=2,
            )
            with gr.Row(elem_classes=["quick-row"]):
                search_hotels = gr.Button("Hotels in Bangkok")
                search_flights = gr.Button("Flight BOM to DEL")
                combined = gr.Button("Colombo to Singapore plan")
            send = gr.Button("Plan my trip", variant="primary", elem_id="send-btn")
        with gr.Column(scale=1):
            activity = gr.HTML(_activity_html([]), label="Agent activity")
            gr.HTML(
                """
                <div class="pro-note">
                  <b>Demo prompts</b><br>
                  list all hotels<br>
                  available hotels in Bangkok<br>
                  flight from BOM to DEL<br>
                  Plan hotel and flight from Colombo to Singapore under $500<br>
                  Book hotel H-SIN-006 for Thara
                </div>
                """
            )

    send.click(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    user_input.submit(chat_with_tripweaver, [user_input, chatbot], [chatbot, activity]).then(lambda: "", None, user_input)
    search_hotels.click(lambda: "available hotels in Bangkok", None, user_input)
    search_flights.click(lambda: "flight from BOM to DEL", None, user_input)
    combined.click(lambda: "Plan hotel and flight from Colombo to Singapore under $500", None, user_input)


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.getenv("FRONTEND_HOST", "0.0.0.0"),
        server_port=int(os.getenv("PORT", os.getenv("FRONTEND_PORT", "7860"))),
        css=THEME_CSS,
    )
