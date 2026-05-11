@echo off
echo ========================================
echo MiroFish - Clean Start Script
echo ========================================
echo.

echo [1/3] Stopping all old backend processes...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 >nul

echo.
echo [2/3] Starting backend (port 5001)...
cd backend
start "MiroFish Backend" cmd /k "uv run python run.py"
cd ..

timeout /t 5 >nul

echo.
echo [3/3] Starting frontend (port 3006)...
cd frontend
start "MiroFish Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo Services started!
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:3006
echo ========================================
echo.
echo Press any key to exit this window...
pause
