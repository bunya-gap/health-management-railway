@echo off
echo Health Auto Export Data Server を起動中...
echo.
echo サーバーURL: http://localhost:5000/health-data
echo 健康確認: http://localhost:5000/health-data (GET)
echo.
cd /d "%~dp0"
python health_data_server.py
pause
