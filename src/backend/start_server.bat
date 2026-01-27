@echo off
echo ================================
echo Origin Notes AI Agent Backend
echo ================================
echo.

cd /d %~dp0

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ================================
echo Starting Agent Backend Server...
echo ================================
echo Server URL: http://127.0.0.1:8765
echo Health check: http://127.0.0.1:8765/health
echo.
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8765 --reload

pause
