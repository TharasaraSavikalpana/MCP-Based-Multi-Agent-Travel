@echo off
setlocal
cd /d "%~dp0"

echo Creating virtual environment...
py -m venv .venv
if errorlevel 1 (
  echo Python launcher "py" was not found. Install Python 3.11+ and try again.
  exit /b 1
)

echo Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if not exist .env (
  copy .env.example .env
  echo Created .env from .env.example. Open .env and add your rotated OPENAI_API_KEY.
) else (
  echo .env already exists. Keeping your current settings.
)

echo Setup complete.
echo Next: run start_backend.bat, then run start_frontend.bat in another terminal.
