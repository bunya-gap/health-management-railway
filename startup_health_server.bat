@echo off
cd /d "%~dp0"
echo Health Auto Export Server - Startup Mode
echo Starting at %DATE% %TIME%
echo.
echo Server will run in background...
echo To stop: Close this window or press Ctrl+C
echo.
python health_data_server.py
pause