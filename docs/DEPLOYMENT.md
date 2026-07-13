# Deployment Guide

TripWeaver has two deployable web services:

- Backend API: FastAPI app in `main.py`
- Frontend UI: Gradio app in `frontend.py`

The MCP servers are bundled with the backend and launched as subprocesses by the
MCP client.

## Required Environment Variables

Backend:

```bash
OPENAI_API_KEY=your-rotated-openai-key
OPENAI_MODEL=gpt-4o-mini
APP_ENV=production
HOTEL_API_BASE=https://standing-fish-574.convex.site/hotels
FLIGHT_API_BASE=https://standing-fish-574.convex.site/flights
TRAVEL_PROVIDER_MODE=live_with_fallback
```

Frontend:

```bash
BACKEND_URL=https://your-backend-url
APP_ENV=production
```

Never commit `.env`. Commit only `.env.example`.

## Render Deployment

1. Push this project to GitHub.
2. Open Render and create a new Blueprint from `render.yaml`, or create two web services manually.
3. For the backend service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add `OPENAI_API_KEY` as a secret environment variable.
4. For the frontend service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python frontend.py`
   - Set `BACKEND_URL` to the deployed backend URL.
5. Test `/health` on the backend, then open the frontend URL.

## Hugging Face Spaces Frontend Option

Use a Gradio Space for the frontend:

1. Upload `frontend.py` and `requirements.txt`.
2. Add `BACKEND_URL` in Space secrets.
3. Keep backend deployed separately on Render, Railway, or another Python host.

## Local Production Test

Terminal 1:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
BACKEND_URL=http://127.0.0.1:8000 python frontend.py
```
