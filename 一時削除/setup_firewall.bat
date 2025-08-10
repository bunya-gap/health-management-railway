@echo off
echo Windowsファイアウォールに5000番ポートの許可ルールを追加中...
echo.

netsh advfirewall firewall add rule name="Health Auto Export Server" dir=in action=allow protocol=TCP localport=5000

echo.
echo ✅ ファイアウォール設定完了
echo Health Auto Export Server (ポート5000) への接続が許可されました
echo.
pause
