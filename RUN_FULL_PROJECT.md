# How To Run TripWeaver From Zero

This is the simple version. The `Example/` folder is only for reference. Do not
run or submit that as your final project.

## 1. Prepare Your OpenAI Key

The key you pasted earlier should be treated as exposed. Go to the OpenAI
dashboard, revoke it, and create a new key.

Never put the key in GitHub code. It goes only in `.env` locally and in hosting
platform environment variables.

## 2. Run Locally On Windows

Open PowerShell inside this folder:

```powershell
cd "C:\Users\thara\Desktop\MCP-Based Multi-Agent Travel"
```

Run setup:

```powershell
.\setup_windows.bat
```

Open `.env` and replace:

```text
OPENAI_API_KEY=replace-with-your-openai-key
```

with your new rotated key.

Start backend in one terminal:

```powershell
.\start_backend.bat
```

Start frontend in a second terminal:

```powershell
.\start_frontend.bat
```

Open:

```text
http://127.0.0.1:7860
```

## 3. Test These Prompts

Use these in the chat UI:

```text
list all hotels
available hotels in Bangkok
flight from BOM to DEL
list all flights
Plan hotel and flight from Colombo to Singapore under $500
Book hotel H-SIN-006 for Thara
```

## 4. What Is Running

Backend:

```text
FastAPI + LangGraph agents
http://127.0.0.1:8000
```

Frontend:

```text
Gradio chat UI
http://127.0.0.1:7860
```

MCP:

```text
mcp_servers/hotel_server.py
mcp_servers/flight_server.py
```

The backend starts MCP servers as subprocesses when tools are called. The agents
do not directly call the hotel/flight provider.

## 5. GitHub Repository Screen

On the GitHub page in your screenshot:

1. Repository name: `MCP-Based-Multi-Agent-Travel`
2. Description: `TripWeaver MCP-based multi-agent travel planner with FastAPI, LangGraph, MCP servers, and Gradio.`
3. Visibility: Public, unless your lecturer says private.
4. Add README: Off
5. Add .gitignore: No .gitignore
6. Add license: No license
7. Click Create repository.

After GitHub creates it, copy the repository URL and send it to me. I can help
you connect this local project to that remote.

Manual push commands, if you want to do it yourself:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/MCP-Based-Multi-Agent-Travel.git
git branch -M main
git push -u origin main
```

## 6. Deploy Globally

Recommended easiest route: Render for backend and frontend.

1. Push the code to GitHub.
2. Go to Render.
3. Create a new Blueprint from `render.yaml`, or create two web services.
4. Backend service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment variables:
     - `OPENAI_API_KEY`: your new rotated key
     - `OPENAI_MODEL`: `gpt-4o-mini`
     - `APP_ENV`: `production`
5. Frontend service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python frontend.py`
   - Environment variables:
     - `BACKEND_URL`: your deployed backend URL
     - `APP_ENV`: `production`
6. Submit:
   - GitHub repository link
   - Frontend deployed link
   - Backend health link: `https://your-backend-url/health`

## 7. For Viva

Read:

```text
docs/VIVA_NOTES.md
docs/MCP_SETUP.md
docs/DEPLOYMENT.md
```

Main explanation:

TripWeaver uses a LangGraph router to identify intent. Hotel and flight agents
call only MCP tools. MCP servers bridge to the external Convex travel service
links, with local fallback data for reliability. The frontend streams activity
and response tokens from FastAPI.
