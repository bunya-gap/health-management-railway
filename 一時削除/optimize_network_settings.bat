@echo off
echo ネットワーク接続の維持設定
echo.
echo Wi-Fiアダプターの電源管理を無効化中...
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object { $adapter = Get-WmiObject -Class Win32_NetworkAdapter | Where-Object {$_.GUID -eq $_.InterfaceGuid}; if($adapter.PNPDeviceID) { $powerMgmt = Get-WmiObject MSPower_DeviceEnable -Namespace root\wmi | Where-Object {$_.InstanceName -match [regex]::Escape($adapter.PNPDeviceID)}; if($powerMgmt) { $powerMgmt.Enable = $False; $powerMgmt.Put() } } }"

echo.
echo ✅ Wi-Fiアダプターの電源管理を無効化しました
echo これでスリープ時でもネットワーク接続が維持されます
echo.
pause