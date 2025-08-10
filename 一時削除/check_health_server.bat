@echo off
echo Checking Health Auto Export Server Status...
echo.
netstat -an | findstr ":5000"
if %errorlevel%==0 (
    echo ✓ Server is running on port 5000
) else (
    echo ✗ Server is not running
)
echo.
pause