@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Corgi-style Service Restart
echo ============================================
echo.

echo [1/2] Killing existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill //F //PID %%a >nul 2>&1
    echo   Killed PID %%a
)
echo   (no processes found - port was already free)
echo.

echo [2/2] Starting uvicorn in background...
echo   Service will run after this window closes.
echo   Use stop.bat to shut down the service.
echo.

cd /d "%~dp0"
start "Corgi-style Service" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

timeout /t 3 /nobreak >nul
netstat -ano | findstr :8000 | findstr LISTENING && echo. && echo Service started successfully! || echo WARNING: Service failed to start.
