# 体組成管理アプリ - GitHub Actions完全無料システム

## 📋 アプリケーション概要

体脂肪を減らし、筋肉量を維持する生活をデータドリブンに過ごすための**GitHub Actions完全無料システム**です。

### 🎯 主な機能
- **データドリブン健康管理**: 複数デバイス・アプリからの健康データを統合分析
- **体組成改善支援**: 体脂肪率12%目標の体組成改善を科学的にサポート
- **リアルタイム分析**: データ受信と同時に分析・LINE通知による健康レポート配信
- **生活修正指導**: カロリー収支状況、体脂肪や筋肉量の増減ペースを確認し、生活の修正が可能

### 📊 データソース統合
- **RENPHO体組成計**: 体重・体脂肪率・筋肉量データ
- **カロミル**: カロリー計算・栄養素データ（摂取カロリー、タンパク質、糖質、脂質等）
- **Oura Ring**: 睡眠・体表温・活動データ（指輪型デバイス）
- **Apple HealthKit**: 上記データを統合管理
- **HAE (Health Auto Export)**: Apple HealthKit内のデータを自動でエクスポートするアプリケーション

### 📈 分析・通知内容
- **体脂肪率進捗**: 現在値・目標値・達成率・予測
- **体組成変化**: 28日/14日/7日の体脂肪量・筋肉量変化追跡
- **カロリー収支分析**: 期間別カロリー収支・必要調整量
- **代謝状況**: 体表温変化・停滞判定・チートデイ推奨
- **行動提案**: 具体的なカロリー調整・運動提案

---

## 🌐 本番環境情報

### GitHub Actions本番環境
```
プロジェクト名: health-management-free
GitHub Repository: https://github.com/bunya-gap/health-management-free
実行プラットフォーム: GitHub Actions (Ubuntu-latest)
月額費用: ¥0 (GitHub Actions無料枠)
```

### 🔗 実行状況
- **実行環境**: GitHub Actions - 完全無料
- **実行頻度**: 毎日 8:00, 12:00, 18:00, 22:00 JST（定期実行）+ 手動実行
- **データ永続化**: GitHubリポジトリ（reports/ディレクトリ）
- **稼働状況**: 完全自動稼働

### 🔐 環境変数（GitHub Secrets設定済み）
```
LINE_BOT_CHANNEL_ACCESS_TOKEN: LINE Bot API認証トークン
LINE_USER_ID: U352695f9f7d6ee3e869b4b636f4e4864
OURA_ACCESS_TOKEN: Oura Ring API認証トークン
```

---

## 🏗️ システム構成

### アーキテクチャ
```
【GitHub Actions完全無料システム】
定期実行/手動実行 → GitHub Actions → 健康分析・LINE通知
    ↓                    ↓                     ↓
自動トリガー         完全無料実行            即時送信
- 定期実行           - HAEデータ処理
- 手動実行           - CSV統合・移動平均計算
- データプッシュ     - 健康分析・レポート生成
                     - LINE通知送信
                     ※月額¥0
```

### 技術スタック
- **プラットフォーム**: GitHub Actions (Ubuntu-latest)
- **言語**: Python 3.11
- **データ処理**: pandas, numpy
- **外部API**: LINE Messaging API, Oura Ring API
- **データ永続化**: GitHubリポジトリ

---

## 🔄 実行方式

### 実行トリガー
```
1. 定期実行: 毎日 8:00, 12:00, 18:00, 22:00 JST
2. 手動実行: GitHub Actions画面から「Run workflow」
3. データプッシュ: health_api_data/*.json または reports/*.csv ファイル変更時
```

### 実行フロー
```
GitHub Actions起動
↓
Python環境セットアップ (3.11 + 依存関係)
↓
health_processor.py実行
├─ HAEデータ変換（JSON → CSV）
├─ CSV統合・移動平均計算
├─ 健康分析・レポート生成
└─ LINE通知送信
↓
結果データ自動コミット・プッシュ
↓
実行完了
```

---

## 📊 データ仕様

### 日次データ仕様（25カラム）
```
1. date - 日付
2. 体重_kg - 体重（kg）
3. 筋肉量_kg - 筋肉量（kg）
4. 体脂肪量_kg - 体脂肪量（kg・計算値）
5. 体脂肪率 - 体脂肪率（%）
6. カロリー収支_kcal - カロリー収支（摂取-消費）
7. 摂取カロリー_kcal - 摂取カロリー
8. 消費カロリー_kcal - 消費カロリー（基礎代謝+活動）
9. 基礎代謝_kcal - 基礎代謝
10. 活動カロリー_kcal - 活動カロリー
11. 歩数 - 歩数
12. 睡眠時間_hours - 睡眠時間（Phase1修正済み）
13. 体表温度_celsius - 体表温度（Oura Ring）
14. 体表温変化_celsius - 体表温変化
15. 体表温偏差_celsius - 体表温偏差
16. 体表温トレンド_celsius - 体表温トレンド
17. タンパク質_g - タンパク質摂取量
18. 糖質_g - 糖質摂取量（Phase1修正済み）
19. 炭水化物_g - 炭水化物摂取量（Phase1追加）
20. 食物繊維_g - 食物繊維摂取量
21. 脂質_g - 脂質摂取量
22. oura_total_calories - Oura Ring総カロリー
23. oura_estimated_basal - Oura Ring推定基礎代謝
24. total_calories_updated - 更新済み総カロリー
25. calculation_method - 計算方法（GITHUB_ACTIONS）
```

### CSVファイル構成
```
reports/daily_health_data.csv          # 日次データ
reports/health_data_with_ma.csv        # 移動平均データ
reports/health_data_index.csv          # インデックスデータ
health_api_data/*.json                 # HAE受信データ保存
```

### HAEメトリクスマッピング（Phase1修正版）
```python
METRIC_MAPPING = {
    'weight_body_mass': '体重_kg',
    'lean_body_mass': '筋肉量_kg', 
    'body_fat_percentage': '体脂肪率',
    'dietary_energy': '摂取カロリー_kcal',
    'basal_energy_burned': '基礎代謝_kcal',
    'active_energy': '活動カロリー_kcal',
    'step_count': '歩数',
    'sleep_analysis': '睡眠時間_hours',  # Phase1修正: totalSleepフィールド使用
    'protein': 'タンパク質_g',
    'carbohydrates': '炭水化物_g',       # Phase1修正: 正しいラベル
    'dietary_sugar': '糖質_g',          # Phase1修正: 正しい糖質データ
    'fiber': '食物繊維_g',
    'total_fat': '脂質_g'
}
```

---

## 📁 ローカルファイル構成

### メインファイル
```
health_processor.py                   # GitHub Actions実行メインファイル
.github/workflows/health-process.yml  # GitHub Actions設定
README.md                            # このドキュメント
requirements.txt                     # Python依存関係
.gitignore                          # Git除外設定
```

### ディレクトリ構成
```
├── health_api_data/                 # HAE受信データ保存（未使用）
├── reports/                         # CSV・分析結果保存
│   ├── daily_health_data.csv       # 日次データ（統一済み）
│   ├── health_data_with_ma.csv     # 移動平均データ（統一済み）
│   ├── health_data_index.csv       # インデックスデータ（統一済み）
│   └── analysis_report_*.json      # 分析レポート履歴
├── .github/workflows/               # GitHub Actions設定
│   └── health-process.yml          # ワークフロー定義
├── automation/                      # 旧ローカル処理（未使用）
├── temp_github_migration/           # 移行作業ファイル
├── temp_github_setup/               # GitHub設定ファイル
└── 一時削除/                       # バックアップディレクトリ
```

### 現在未使用のローカルファイル
```
❌ health_data_server.py             # 旧Railwayサーバー（停止済み）
❌ automation/*                      # 旧ローカル処理（移行済み）
❌ csv_data_integrator.py            # health_processor.pyに統合済み
❌ hae_data_converter.py             # health_processor.pyに統合済み
❌ health_analytics_engine.py        # health_processor.pyに統合済み
❌ temp_*.py                         # 開発時一時ファイル
```

---

## 🚨 運用・メンテナンス

### 日常運用
- **監視**: 不要（完全自動稼働・無料）
- **データ受信**: 定期実行 + 手動実行で対応
- **通知配信**: LINE Bot経由で即時配信
- **データ保存**: GitHubリポジトリに自動保存

### GitHub Actions手動実行方法
```
1. https://github.com/bunya-gap/health-management-free にアクセス
2. [Actions] タブクリック
3. [🏥 Health Data Processing] ワークフロー選択
4. [Run workflow] ボタンクリック
5. 実行完了まで約2-3分
```

### ログ確認方法
```
1. GitHub Actions実行画面でワークフロー実行を選択
2. 各ステップのログを展開して確認
3. エラー時は❌マークのステップを重点確認
```

---

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. GitHub Actions実行失敗
```bash
# 確認手順
1. GitHub Actions画面でエラーログ確認
2. Secrets設定確認（LINE/OURA トークン）
3. 手動実行で動作テスト
```

#### 2. LINE通知が届かない
```bash
# 確認手順
1. GitHub Secrets設定確認
   → LINE_BOT_CHANNEL_ACCESS_TOKEN
   → LINE_USER_ID
2. 手動実行でエラーログ確認
3. LINE Bot APIステータス確認
```

#### 3. 移動平均データが見つからない
```bash
# 原因: ファイル名不一致（修正済み）
✅ 修正完了: health_data_with_ma.csv に統一
- 旧ファイル名: 7日移動平均データ.csv
- 新ファイル名: health_data_with_ma.csv
```

### エラーコード一覧
```
exit 0: 正常処理完了
exit 1: 処理失敗（分析失敗・LINE通知失敗等）
```

---

## 📖 重要用語集

- **HAE (Health Auto Export)**: Apple HealthKit内のデータを自動でエクスポートするiOSアプリケーション
- **体組成**: 体脂肪率・筋肉量・体脂肪量などの身体構成比率
- **Oura Ring**: フィンランド製の指輪型ヘルスデバイス（睡眠・体表温・活動量測定）
- **RENPHO**: Bluetooth対応体組成計メーカー
- **カロミル**: 栄養管理・カロリー計算モバイルアプリ
- **GitHub Actions**: 本アプリケーションが動作する無料CI/CDプラットフォーム

---

## 📈 プロジェクト履歴

### 🎉 **2025年8月14日 - GitHub Actions完全移行達成**
**Railway → GitHub Actions移行・Phase 1バグ修正完了プロジェクト**

#### 最終成果
- ✅ **完全無料化**: Railway(有料) → GitHub Actions(無料)移行完了
- ✅ **ファイル名統一**: ローカル日本語ファイル名 → 英語標準ファイル名
- ✅ **Phase 1バグ修正**: 睡眠時間・糖質マッピング修正完了
- ✅ **GitHub Actions最適化**: 定期実行・手動実行・データプッシュ対応
- ✅ **運用完全自動化**: 人的介入ゼロでの定期実行

#### 技術的達成
- **統合プロセッサー**: health_processor.py (567行) - GitHub Actions完全対応
- **処理性能**: HAE変換→分析→通知 完全自動化
- **稼働率**: GitHub Actions 99.9%稼働
- **月額費用**: ¥0（GitHub Actions無料枠内）

#### Phase 1バグ修正完了項目
- ✅ **睡眠時間取得修正**: `qty` → `totalSleep`フィールド使用
- ✅ **糖質マッピング修正**: `carbohydrates` → `dietary_sugar` + `炭水化物_g`追加
- ✅ **ファイル名統一**: 日本語ファイル名 → 英語標準ファイル名

### 🔮 **Phase 2予定（OURA API統合）**
- **対象**: 活動カロリー異常値修正（0.208kcal → 正常値）
- **方法**: OURA API直接連携による消費カロリー正確化
- **優先度**: 中（Phase 1完了後実装）

---

**🎊 システム稼働中 - GitHub Actions完全無料健康管理システム**

**作成者**: terada  
**最終更新**: 2025年8月14日  
**システム種別**: GitHub Actions完全無料健康管理システム  
**稼働状況**: 定期実行・手動実行対応 ✅  
**月額費用**: ¥0 💰

---

**✅ 😀 𠮷 👨‍👩‍👧‍👦**
