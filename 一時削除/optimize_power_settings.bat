@echo off
echo Health Server用 - 電源設定の最適化
echo.
echo 現在の電源設定を確認中...
powercfg /query

echo.
echo スリープ無効化を実行中...
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 0
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0

echo.
echo ✅ 電源設定を最適化しました
echo - モニター: 常時点灯
echo - スタンバイ: 無効
echo - 休眠: 無効
echo.
echo ⚠️  ノートPCの場合はバッテリー消費にご注意ください
pause