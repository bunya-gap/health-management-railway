@echo off
echo Stopping Health Auto Export Server...
taskkill /f /im python.exe /fi "windowtitle eq Health Auto Export Data Server*"
echo Server stopped.
pause