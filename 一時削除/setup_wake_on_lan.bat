@echo off
echo Wake-on-LAN 設定の確認と有効化
echo.
echo 現在のネットワークアダプター確認中...
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Format-Table Name, InterfaceDescription, LinkSpeed"

echo.
echo Wake-on-LANを有効化中...
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Enable-NetAdapterPowerManagement -WakeOnMagicPacket"

echo.
echo ✅ Wake-on-LAN設定完了
echo iPhoneから接続要求があった時にPCが自動復帰します
echo.
pause