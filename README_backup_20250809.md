# 体組成管理アプリ - 総合README

## 📋 プロジェクト概要

AppleのHealthKitから書き出されたヘルスデータ（XML形式）を処理し、Health Auto Export (HAE)からのリアルタイムデータ受信にも対応した、体組成および健康指標を分析する統合データプロセッサーです。

**プロジェクト所在地**: `C:\Users\terada\Desktop\apps\体組成管理app`

## 🏗️ ディレクトリ構造

```
体組成管理app/
├── README.md                          # このファイル（総合ガイド）
├── unified_processor.py               # メイン処理スクリプト（XMLデータ処理）
├── unified_processor_api.py           # API連携版プロセッサー
├── health_data_server.py              # HAEデータ受信サーバー（本格版）
├── requirements.txt                   # Python依存関係
├── 書き出したデータ.zip               # AppleHealth XMLデータアーカイブ
├── oura_config.py                     # Oura Ring設定（稼働中）
├── setup_oura.py                      # Oura Ring セットアップ
├── start_server.bat                   # サーバー起動スクリプト
├── startup_health_server.bat          # サーバー自動起動
├── reports/                           # データ出力ディレクトリ
│   ├── 日次データ.csv
│   ├── 7日移動平均データ.csv
│   └── インデックスデータ.csv
├── health_api_data/                   # HAE受信データ保存ディレクトリ
├── reports_backup/                    # 手動データ使用時のバックアップ
└── 一時削除/                          # 削除ファイル（確認後完全削除予定）
```

## 🔧 主要機能

### 1. XMLデータ処理（unified_processor.py）
- **対象期間**: 2025年6月1日以降のデータのみ処理
- **データソース**: AppleHealth XMLファイル（ZIPアーカイブから展開）
- **処理対象指標**: 12項目（体重、体脂肪率、筋肉量、各種カロリー、歩数、睡眠、栄養素）

### 2. リアルタイムデータ受信（HAE連携）
- **Health Auto Export (HAE)** からのリアルタイムデータ受信
- **REST API エンドポイント**: `http://192.168.0.9:5000/health-data` (または8080)
- **自動データ保存**: JSON形式での生データ保存
- **CSV変換**: メトリクス自動変換機能

## 🌐 ネットワーク設定

### IPアドレス情報
- **サーバーIPアドレス**: `192.168.0.9`
- **標準ポート**: `5000`
- **代替ポート**: `8080` (ファイアウォール問題回避用)

### HAE設定
```
REST API URL: http://192.168.0.9:5000/health-data
Export Format: JSON
Aggregate Data: ON
Aggregation Interval: Days
Batch Requests: ON (推奨)
```

### ファイアウォール設定
**重要**: ポート5000/8080への着信を許可する必要があります

**手動設定方法**:
1. Windows設定 → ネットワークとインターネット → Windows Defender ファイアウォール
2. 詳細設定 → 受信の規則 → 新しい規則
3. ポート → TCP → 特定のローカルポート: 5000,8080
4. 接続を許可する → すべてのプロファイル → 名前: "Health Auto Export Server"

**注意**: 自動設定用のsetup_firewall.batは削除されました。手動でファイアウォール設定を行ってください。

## 🚀 サーバー起動方法

### 1. 本格サーバー（推奨）
```cmd
python health_data_server.py
```
- 完全なデータ処理機能
- 自動CSV変換
- ログ出力機能

### 2. バッチファイルでの起動
```cmd
start_server.bat          # 標準起動
startup_health_server.bat # 自動起動設定
```

**注意**: テストサーバーは使用頻度が低いため削除しました。トラブルシューティングが必要な場合は一時削除ディレクトリから復元可能です。

## 📊 データ処理仕様

### 処理対象指標（12項目）
| HealthKit識別子 | 指標名 | 集計方法 |
|---|---|---|
| HKQuantityTypeIdentifierBodyMass | 体重 | 最終値 |
| HKQuantityTypeIdentifierBodyFatPercentage | 体脂肪率 | 最終値 |
| HKQuantityTypeIdentifierLeanBodyMass | 筋肉量 | 最終値 |
| HKQuantityTypeIdentifierDietaryEnergyConsumed | 摂取カロリー | 積算 |
| HKQuantityTypeIdentifierActiveEnergyBurned | 活動カロリー | 積算 |
| HKQuantityTypeIdentifierBasalEnergyBurned | 基礎代謝 | 特別ロジック※ |
| HKQuantityTypeIdentifierStepCount | 歩数 | 積算 |
| HKCategoryTypeIdentifierSleepAnalysis | 睡眠時間 | Oura特別処理 |
| HKQuantityTypeIdentifierDietaryProtein | タンパク質 | 積算 |
| HKQuantityTypeIdentifierDietarySugar | 糖質 | 積算 |
| HKQuantityTypeIdentifierDietaryFiber | 食物繊維 | 積算 |
| HKQuantityTypeIdentifierDietaryFatTotal | 脂質 | 積算 |

**※基礎代謝の特別ロジック**:
- RENPHO Healthデータがあれば優先採用
- RENPHO Healthがなければ、iPhone由来データを積算

### 出力データ形式

#### 日次データ（16カラム）
1. date - 日付
2. 体重_kg - 体重（kg）
3. 筋肉量_kg - 筋肉量（kg）
4. 体脂肪量_kg - 体脂肪量（計算値）
5. 体脂肪率 - 体脂肪率（%）
6. カロリー収支_kcal - カロリー収支
7. 摂取カロリー_kcal - 摂取カロリー
8. 消費カロリー_kcal - 消費カロリー
9. 基礎代謝_kcal - 基礎代謝
10. 活動カロリー_kcal - 活動カロリー
11. 歩数 - 歩数
12. 睡眠時間_hours - 睡眠時間
13. タンパク質_g - タンパク質（g）
14. 糖質_g - 糖質（g）
15. 食物繊維_g - 食物繊維（g）
16. 脂質_g - 脂質（g）

## 🔧 依存関係

### Python要件
```
Flask==3.0.0
pandas==2.1.0
lxml==4.9.3
requests==2.31.0
python-dotenv==1.0.0
```

### インストール
```cmd
pip install -r requirements.txt
```

## ⚠️ 重要な注意事項

### 1. iOSの設定要件
- **Local Network権限**: 設定 → プライバシーとセキュリティ → ローカルネットワーク → Health Auto Export を許可
- **同一WiFiネットワーク**: iPhoneとサーバーPCが同じWiFiに接続されていること

### 2. ファイアウォール設定
- **Windows Defender ファイアウォール**: TCP ポート5000, 8080を許可
- **ウイルス対策ソフト**: 本アプリケーションを除外設定に追加

### 3. データ安全性
- **バックアップ**: `書き出したデータ.zip`と`reports/`ディレクトリを定期バックアップ
- **一時ファイル削除**: テストファイルは使用後必ず削除

### 4. パフォーマンス
- **メモリ使用量**: 大容量XMLファイル処理時は十分なRAMを確保
- **ディスク容量**: HAE受信データが蓄積されるため定期的な容量確認

## 🛠️ トラブルシューティング

### よくある問題と解決策

#### 1. HAE接続タイムアウト
**症状**: Health Auto Export で "The request timed out" エラー

**解決策**:
1. **webhook.siteでのテスト**: HAE側の送信機能確認
2. **ファイアウォール確認**: ポート5000/8080の許可
3. **同一ネットワーク確認**: WiFi接続状況
4. **Local Network権限**: iOS設定確認

#### 2. サーバー起動失敗
**症状**: サーバーが起動しない、またはポートエラー

**解決策**:
```cmd
# 既存プロセス確認・停止
tasklist | findstr python
taskkill /f /im python.exe

# メインサーバー再起動で代替
python health_data_server.py
```

**注意**: テストサーバーは削除されました。必要に応じて「一時削除」ディレクトリから復元してください。

#### 3. データ処理エラー
**症状**: XMLファイル読み取りエラー

**解決策**:
1. `書き出したデータ.zip`の整合性確認
2. ファイルアクセス権限確認
3. 十分なディスク容量確認

### 診断コマンド
```cmd
# ネットワーク状態確認
netstat -an | findstr :5000

# サーバープロセス確認
tasklist | findstr python

# ファイアウォール状態確認（管理者権限）
netsh advfirewall firewall show rule name=all | findstr 5000
```

## 📈 今後の拡張計画

### 1. データ可視化
- Grafana連携によるリアルタイムダッシュボード
- 健康指標トレンド分析

### 2. 通知機能
- 異常値検出アラート
- 目標達成通知

### 3. 外部連携
- Google Fit API連携
- MyFitnessPal連携

## 🆘 緊急時の対応

### サーバー完全リセット
```cmd
# すべてのPythonプロセス停止
taskkill /f /im python.exe

# メインサーバー再起動
python health_data_server.py

# HAE設定確認
# URL: http://192.168.0.9:5000/health-data
```

**注意**: テストサーバーは削除されました。問題がある場合は「一時削除」ディレクトリから復元してください。

### データ復旧
- `health_api_data/`ディレクトリから生JSONデータを確認
- `reports/`ディレクトリから過去のCSVデータを確認

## 📞 サポート情報

このREADMEファイルで解決しない問題が発生した場合：

1. **ログ確認**: サーバーコンソール出力とHAEのActivity Log確認
2. **設定再確認**: ネットワーク、ファイアウォール、iOS権限設定
3. **最小構成テスト**: test_server_8080.pyでの基本動作確認

---

**最終更新**: 2025年8月9日  
**プロジェクト作成者**: terada  
**動作確認環境**: Windows, Python 3.13.0, Flask 3.0.0
