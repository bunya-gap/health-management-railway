#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏥 GitHub Actions用体組成管理プロセッサー v1.0
Railway → GitHub移植版（完全無料対応）

機能:
- HAEデータ自動処理（JSON → CSV統合）
- 健康分析・LINE通知
- GitHub Actions環境最適化
- データ永続化（リポジトリ保存）

環境変数（GitHub Secrets）:
- LINE_BOT_CHANNEL_ACCESS_TOKEN
- LINE_USER_ID  
- OURA_ACCESS_TOKEN
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
import traceback
import logging
from typing import Dict, List, Any, Optional

# ===== ログ設定 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ===== GitHub Actions環境対応 =====
class GitHubEnvironment:
    """GitHub Actions環境情報"""
    
    def __init__(self):
        self.workspace = os.environ.get('GITHUB_WORKSPACE', '.')
        self.is_github_actions = bool(os.environ.get('GITHUB_ACTIONS'))
        self.event_name = os.environ.get('GITHUB_EVENT_NAME', 'unknown')
        
        # ディレクトリ設定
        self.base_dir = Path(self.workspace)
        self.data_dir = self.base_dir / 'health_api_data'
        self.reports_dir = self.base_dir / 'reports'
        
        # ディレクトリ作成
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"🌐 GitHub Actions: {'✅有効' if self.is_github_actions else '❌ローカル'}")
        logger.info(f"📁 ワークスペース: {self.workspace}")
        logger.info(f"🔄 イベント: {self.event_name}")

# ===== HAEデータ変換機能 =====
class HAEDataConverter:
    """HAEデータをCSV形式に変換（移植版）"""
    
    METRIC_MAPPING = {
        'weight_body_mass': '体重_kg',
        'lean_body_mass': '筋肉量_kg', 
        'body_fat_percentage': '体脂肪率',
        'dietary_energy': '摂取カロリー_kcal',
        'basal_energy_burned': '基礎代謝_kcal',
        'active_energy': '活動カロリー_kcal',
        'step_count': '歩数',
        'sleep_analysis': '睡眠時間_hours',
        'protein': 'タンパク質_g',
        'carbohydrates': '炭水化物_g',
        'dietary_sugar': '糖質_g',
        'fiber': '食物繊維_g',
        'total_fat': '脂質_g'
    }
    
    def convert_hae_to_daily_row(self, hae_data: Dict) -> Dict:
        """HAE JSONを日次データ行に変換"""
        try:
            logger.info("🔄 HAEデータ変換開始")
            metrics = hae_data.get('data', {}).get('metrics', [])
            logger.info(f"📊 メトリクス数: {len(metrics)}")
            
            # 基本行データ（Phase1修正版）
            daily_row = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                '体重_kg': None,
                '筋肉量_kg': None,
                '体脂肪量_kg': None,
                '体脂肪率': None,
                'カロリー収支_kcal': None,
                '摂取カロリー_kcal': None,
                '消費カロリー_kcal': None,
                '基礎代謝_kcal': None,
                '活動カロリー_kcal': None,
                '歩数': None,
                '睡眠時間_hours': None,
                '体表温度_celsius': None,
                '体表温変化_celsius': None,
                '体表温偏差_celsius': None,
                '体表温トレンド_celsius': None,
                'タンパク質_g': None,
                '糖質_g': None,
                '炭水化物_g': None,  # Phase1修正: 追加
                '食物繊維_g': None,
                '脂質_g': None,
                'oura_total_calories': None,
                'oura_estimated_basal': None,
                'total_calories_updated': None,
                'calculation_method': 'GITHUB_ACTIONS'
            }
            
            # メトリクス変換（Phase1修正対応）
            converted_count = 0
            for metric in metrics:
                name = metric.get('name', '')
                if name in self.METRIC_MAPPING:
                    csv_column = self.METRIC_MAPPING[name]
                    data_points = metric.get('data', [])
                    
                    if data_points:
                        latest_point = data_points[-1]
                        
                        # 【Phase1修正】sleep_analysis専用処理
                        if name == 'sleep_analysis':
                            daily_row[csv_column] = latest_point.get('totalSleep')
                        else:
                            daily_row[csv_column] = latest_point.get('qty')
                        
                        converted_count += 1
                        logger.info(f"✅ {name} → {csv_column}: {daily_row[csv_column]}")
            
            logger.info(f"🎯 変換完了: {converted_count}個のメトリクス")
            
            # 計算処理
            self._calculate_derived_values(daily_row)
            
            return daily_row
            
        except Exception as e:
            logger.error(f"❌ HAEデータ変換エラー: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_derived_values(self, daily_row: Dict):
        """派生値計算"""
        # 体脂肪量計算
        if daily_row['体重_kg'] and daily_row['体脂肪率']:
            daily_row['体脂肪量_kg'] = daily_row['体重_kg'] * (daily_row['体脂肪率'] / 100)
            logger.info(f"💡 体脂肪量計算: {daily_row['体脂肪量_kg']:.2f}kg")
        
        # カロリー収支計算
        intake = daily_row['摂取カロリー_kcal'] or 0
        basal = daily_row['基礎代謝_kcal'] or 0
        active = daily_row['活動カロリー_kcal'] or 0
        
        if intake and (basal or active):
            daily_row['消費カロリー_kcal'] = basal + active
            daily_row['カロリー収支_kcal'] = intake - (basal + active)
            logger.info(f"🔥 カロリー収支: {daily_row['カロリー収支_kcal']}kcal")

# ===== CSV統合機能 =====
class CSVDataIntegrator:
    """HAEデータを既存CSVに統合（GitHub版）"""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.daily_csv = self.reports_dir / "daily_health_data.csv"
        self.ma_csv = self.reports_dir / "health_data_with_ma.csv"
        self.index_csv = self.reports_dir / "health_data_index.csv"
        logger.info(f"📊 CSV統合機能初期化: {self.reports_dir}")
    
    def integrate_daily_data(self, daily_row: Dict) -> bool:
        """日次データをCSVに統合"""
        try:
            logger.info("🔄 CSV統合開始")
            
            # 既存データ読み込み
            if self.daily_csv.exists():
                df = pd.read_csv(self.daily_csv, encoding='utf-8-sig')
                logger.info(f"📖 既存データ読み込み: {len(df)}行")
            else:
                df = pd.DataFrame()
                logger.info("📝 新規データ作成")
            
            # 新データ追加（同一日付は上書き）
            new_df = pd.DataFrame([daily_row])
            if not df.empty:
                df = df[df['date'] != daily_row['date']]
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df
            
            # 日付順ソート
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # UTF-8 BOM付きで保存（Windows Excel対応）
            df.to_csv(self.daily_csv, index=False, encoding='utf-8-sig')
            logger.info(f"💾 日次データ保存完了: {len(df)}行")
            
            # 移動平均再計算
            self._recalculate_moving_averages(df)
            
            logger.info("✅ CSV統合完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ CSV統合エラー: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _recalculate_moving_averages(self, df: pd.DataFrame):
        """移動平均再計算"""
        try:
            logger.info("🔄 移動平均計算開始")
            
            # 数値カラムの移動平均計算
            numeric_columns = ['体重_kg', '筋肉量_kg', '体脂肪量_kg', '体脂肪率', 
                             'カロリー収支_kcal', '摂取カロリー_kcal', '消費カロリー_kcal',
                             '基礎代謝_kcal', '活動カロリー_kcal', '歩数', '睡眠時間_hours']
            
            calculated_count = 0
            for col in numeric_columns:
                if col in df.columns:
                    df[f'{col}_ma7'] = df[col].rolling(window=7, min_periods=1).mean()
                    df[f'{col}_ma14'] = df[col].rolling(window=14, min_periods=1).mean()
                    df[f'{col}_ma28'] = df[col].rolling(window=28, min_periods=1).mean()
                    calculated_count += 1
            
            # 移動平均データ保存
            df.to_csv(self.ma_csv, index=False, encoding='utf-8-sig')
            df.to_csv(self.index_csv, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ 移動平均計算完了: {calculated_count}カラム処理")
            
        except Exception as e:
            logger.error(f"❌ 移動平均計算エラー: {e}")

# ===== 健康分析エンジン =====
class HealthAnalyticsEngine:
    """健康指標分析エンジン（GitHub版）"""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.target_body_fat_rate = 12.0
        logger.info(f"🧠 健康分析エンジン初期化（目標体脂肪率: {self.target_body_fat_rate}%）")
    
    def analyze_health_data(self) -> Optional[Dict]:
        """健康データ分析実行"""
        try:
            logger.info("🔄 健康分析開始")
            
            ma_file = self.reports_dir / "health_data_with_ma.csv"
            if not ma_file.exists():
                logger.error("❌ 移動平均データが見つかりません")
                return None
            
            df = pd.read_csv(ma_file, encoding='utf-8-sig')
            if df.empty:
                logger.error("❌ データが空です")
                return None
            
            logger.info(f"📊 分析データ: {len(df)}行")
            
            # 最新データ取得
            latest = df.iloc[-1]
            logger.info(f"📅 最新データ日付: {latest.get('date')}")
            
            # 分析結果作成
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'system': 'GitHub Actions v1.0',
                'current_body_fat_rate': latest.get('体脂肪率'),
                'target_body_fat_rate': self.target_body_fat_rate,
                'body_fat_progress': self._calculate_progress(df),
                'body_composition': {
                    'weight': latest.get('体重_kg'),
                    'muscle_mass': latest.get('筋肉量_kg'),
                    'body_fat_mass': latest.get('体脂肪量_kg')
                },
                'calorie_balance': {
                    'current': latest.get('カロリー収支_kcal'),
                    '7day_avg': latest.get('カロリー収支_kcal_ma7'),
                    '14day_avg': latest.get('カロリー収支_kcal_ma14')
                }
            }
            
            # 分析レポート保存
            report_file = self.reports_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 分析レポート保存: {report_file.name}")
            logger.info(f"🎯 現在体脂肪率: {report['current_body_fat_rate']}%")
            logger.info("✅ 健康分析完了")
            return report
            
        except Exception as e:
            logger.error(f"❌ 健康分析エラー: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_progress(self, df: pd.DataFrame) -> Dict:
        """進捗計算"""
        latest = df.iloc[-1]
        current_bf = latest.get('体脂肪率', 0)
        
        progress = {}
        for days in [7, 14, 28]:
            if len(df) >= days + 1:
                past_bf = df.iloc[-(days + 1)].get('体脂肪率', current_bf)
                progress[f'{days}day_change'] = current_bf - past_bf
            else:
                progress[f'{days}day_change'] = 0
        
        return progress

# ===== LINE通知機能 =====
class LineBotNotifier:
    """LINE Bot API通知（GitHub版）"""
    
    def __init__(self):
        self.token = os.environ.get('LINE_BOT_CHANNEL_ACCESS_TOKEN')
        self.user_id = os.environ.get('LINE_USER_ID')
        self.api_url = "https://api.line.me/v2/bot/message/push"
        logger.info(f"📱 LINE通知機能初期化（設定: {'✅完了' if self.token and self.user_id else '❌不完全'}）")
    
    def send_health_report(self, report: Dict) -> bool:
        """健康レポートをLINE送信"""
        if not self.token or not self.user_id:
            logger.error("❌ LINE設定が不完全です")
            return False
        
        try:
            logger.info("🔄 LINE通知送信開始")
            
            # レポートメッセージ作成
            message = self._format_health_message(report)
            logger.info(f"📝 メッセージ作成完了（{len(message)}文字）")
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': self.user_id,
                'messages': [{'type': 'text', 'text': message}]
            }
            
            logger.info("🚀 LINE API呼び出し実行")
            response = requests.post(self.api_url, headers=headers, 
                                   data=json.dumps(data), timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ LINE通知送信完了")
                return True
            else:
                logger.error(f"❌ LINE通知失敗: {response.status_code}")
                logger.error(f"レスポンス: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ LINE通知エラー: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _format_health_message(self, report: Dict) -> str:
        """健康レポートメッセージ作成"""
        current_bf = report.get('current_body_fat_rate', 0)
        target_bf = report.get('target_body_fat_rate', 12.0)
        progress = report.get('body_fat_progress', {})
        
        message = f"""📊体脂肪率進捗 | {report.get('timestamp', 'N/A')}

🎯 {current_bf:.1f}% 【GitHub Actions】

現在: {current_bf:.1f}%  目標: {target_bf:.1f}%
28日: {progress.get('28day_change', 0):+.1f}%  14日: {progress.get('14day_change', 0):+.1f}%  7日: {progress.get('7day_change', 0):+.1f}%

💪体組成変化トレンド
体重: {report.get('body_composition', {}).get('weight', 0):.1f}kg
筋肉量: {report.get('body_composition', {}).get('muscle_mass', 0):.1f}kg
体脂肪量: {report.get('body_composition', {}).get('body_fat_mass', 0):.1f}kg

🔥カロリー収支状況
現在: {report.get('calorie_balance', {}).get('current', 0):.0f}kcal
7日平均: {report.get('calorie_balance', {}).get('7day_avg', 0):.0f}kcal

【GitHub Actions v1.0】完全無料システム稼働中✅"""

        return message

# ===== メイン処理クラス =====
class GitHubHealthProcessor:
    """GitHub Actions用統合健康管理プロセッサー"""
    
    def __init__(self):
        self.env = GitHubEnvironment()
        self.converter = HAEDataConverter()
        self.integrator = CSVDataIntegrator(self.env.reports_dir)
        self.analytics = HealthAnalyticsEngine(self.env.reports_dir)
        self.notifier = LineBotNotifier()
        logger.info("🚀 GitHub健康管理プロセッサー初期化完了")
    
    def process_new_data(self) -> bool:
        """新しいHAEデータを検出・処理"""
        try:
            logger.info("🎯 ===== 新データ処理開始 =====")
            
            # 新しいJSONファイルを検索
            new_files = self._find_new_data_files()
            if not new_files:
                logger.info("📭 新しいデータファイルなし")
                return True  # データなしは正常
            
            logger.info(f"📁 新データファイル: {len(new_files)}個")
            
            # 最新ファイルを処理
            latest_file = max(new_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"📄 処理対象: {latest_file.name}")
            
            # データ読み込み・処理
            with open(latest_file, 'r', encoding='utf-8') as f:
                hae_data = json.load(f)
            
            return self._process_hae_data_complete(hae_data)
            
        except Exception as e:
            logger.error(f"❌ 新データ処理エラー: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _find_new_data_files(self) -> List[Path]:
        """新しいデータファイルを検索"""
        data_files = list(self.env.data_dir.glob("*.json"))
        
        # 24時間以内のファイルを新しいとみなす
        cutoff_time = datetime.now() - timedelta(hours=24)
        new_files = []
        
        for file_path in data_files:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time > cutoff_time:
                new_files.append(file_path)
        
        return new_files
    
    def _process_hae_data_complete(self, hae_data: Dict) -> bool:
        """HAEデータ完全処理"""
        try:
            logger.info("🎯 ===== HAEデータ統合処理開始 =====")
            
            # 1. HAE → CSV変換
            logger.info("【STEP 1】 HAEデータ変換実行")
            daily_row = self.converter.convert_hae_to_daily_row(hae_data)
            if not daily_row:
                logger.error("❌ データ変換失敗")
                return False
            
            # 2. CSV統合・移動平均
            logger.info("【STEP 2】 CSV統合・移動平均実行")
            if not self.integrator.integrate_daily_data(daily_row):
                logger.error("❌ CSV統合失敗")
                return False
            
            # 3. 健康分析
            logger.info("【STEP 3】 健康分析実行")
            report = self.analytics.analyze_health_data()
            if not report:
                logger.error("❌ 健康分析失敗")
                return False
            
            # 4. LINE通知
            logger.info("【STEP 4】 LINE通知実行")
            if not self.notifier.send_health_report(report):
                logger.warning("⚠️ LINE通知失敗（処理は継続）")
            
            logger.info("🎉 ===== HAEデータ統合処理完了 =====")
            return True
            
        except Exception as e:
            logger.error(f"❌ HAEデータ処理エラー: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run_manual_analysis(self) -> bool:
        """手動分析実行"""
        try:
            logger.info("🧠 ===== 手動分析実行 =====")
            
            report = self.analytics.analyze_health_data()
            if report:
                notification_success = self.notifier.send_health_report(report)
                logger.info(f"📱 LINE通知: {'✅成功' if notification_success else '❌失敗'}")
                return True
            else:
                logger.error("❌ 手動分析失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 手動分析エラー: {e}")
            return False

# ===== メイン実行 =====
def main():
    """メイン実行関数"""
    try:
        logger.info("🏥 ===== GitHub Actions 体組成管理システム開始 =====")
        logger.info(f"📅 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # プロセッサー初期化
        processor = GitHubHealthProcessor()
        
        # 環境変数確認
        logger.info("🔐 環境変数確認:")
        logger.info(f"  LINE設定: {'✅完了' if os.environ.get('LINE_BOT_CHANNEL_ACCESS_TOKEN') and os.environ.get('LINE_USER_ID') else '❌不完全'}")
        logger.info(f"  OURA設定: {'✅完了' if os.environ.get('OURA_ACCESS_TOKEN') else '❌未設定'}")
        
        # イベント別処理分岐
        event_name = processor.env.event_name
        logger.info(f"🔄 実行モード: {event_name}")
        
        success = False
        
        if event_name == 'workflow_dispatch':
            # 手動実行
            logger.info("👤 手動実行モード")
            success = processor.run_manual_analysis()
        
        elif event_name == 'push':
            # データプッシュ時
            logger.info("📁 データプッシュモード")
            success = processor.process_new_data()
        
        elif event_name == 'schedule':
            # 定期実行
            logger.info("⏰ 定期実行モード")
            success = processor.run_manual_analysis()
        
        else:
            # その他・不明
            logger.info("❓ 不明なイベント - 手動分析実行")
            success = processor.run_manual_analysis()
        
        # 実行結果
        if success:
            logger.info("🎉 ===== 体組成管理システム実行完了（成功） =====")
            print("✅ 😀 𠮷 👨‍👩‍👧‍👦")  # Unicode検証出力
        else:
            logger.error("❌ ===== 体組成管理システム実行完了（失敗） =====")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ メイン実行エラー: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
