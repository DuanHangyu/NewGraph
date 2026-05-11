@echo off
echo Stopping all backend processes on port 5001...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)

echo All backend processes stopped. Please press any key to continue.
pause
