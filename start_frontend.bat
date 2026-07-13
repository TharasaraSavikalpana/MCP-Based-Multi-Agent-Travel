@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\activate.bat (
  echo Virtual environment not found. Run setup_windows.bat first.
  exit /b 1
)

call .venv\Scripts\activate.bat
set BACKEND_URL=http://127.0.0.1:8000
python frontend.py
