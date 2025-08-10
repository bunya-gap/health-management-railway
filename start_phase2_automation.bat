@echo off
title Phase 2自動化システム起動中...

echo ===================================
echo    Phase 2自動化システム起動
echo ===================================
echo.

cd /d "C:\Users\terada\Desktop\apps\体組成管理app"

echo [INFO] 依存関係チェック中...
python -c "import requests, psutil" 2>nul
if errorlevel 1 (
    echo [ERROR] 必要なPythonパッケージが不足しています
    echo [INFO] インストール中: pip install requests psutil
    pip install requests psutil
)

echo [INFO] システム状況確認中...
python automation\monitoring.py > temp_system_check.log 2>&1

echo [INFO] HAEサーバー稼働確認...
netstat -an | findstr :5000 > nul
if errorlevel 1 (
    echo [WARNING] HAEサーバーが停止中です
    echo [INFO] HAEサーバーを起動中...
    start /b python health_data_server.py
    timeout /t 3 > nul
)

echo [INFO] Phase 2自動処理システム開始...
echo [INFO] 以下の機能が利用可能です:
echo   • HAEデータ自動監視
echo   • 自動分析実行
echo   • LINE自動通知
echo   • システム監視
echo.
echo [INFO] 停止する場合は Ctrl+C を押してください
echo.

python automation\auto_processor.py --monitor

pause
