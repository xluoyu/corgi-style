@echo off
echo [Corgi-style] Stopping existing services...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill //F //PID %%a >nul 2>&1
)

echo [Corgi-style] Starting uvicorn...

cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
