"""
🌐 Complete Cloud Health Management Server v3.1 - CSV Analysis Enhanced
ローカル依存ゼロ - 完全クラウド化統合システム

【修正内容】:
- ログ出力強化（gunicorn対応）
- エラーハンドリング詳細化
- デバッグ情報追加
- 処理状況可視化
- CSV内容表示エンドポイント追加

機能:
- HAEデータ受信 → 即座変換・統合 → 分析 → LINE通知
- CSV内容表示・期間別データ確認
- 定期監視・メンテナンス（バックグラウンド）
- 全処理をRailway環境で完結

Railway環境変数（必須）:
- LINE_BOT_CHANNEL_ACCESS_TOKEN
- LINE_USER_ID  
- OURA_ACCESS_TOKEN (Optional)
"""

from flask import Flask, request, jsonify
import json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import time
import traceback
import logging
import sys

# ===== ログ設定強化 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ===== 環境設定 =====
DATA_DIR = os.path.join(os.path.dirname(__file__), 'health_api_data')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')

# Railway Volume対応
if os.path.exists('/app/reports'):
    REPORTS_DIR = '/app/reports'
if os.path.exists('/app/health_api_data'):
    DATA_DIR = '/app/health_api_data'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# 環境変数
LINE_BOT_TOKEN = os.environ.get('LINE_BOT_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
OURA_TOKEN = os.environ.get('OURA_ACCESS_TOKEN')

logger.info(f"🚀 統合サーバーv3.1初期化開始")
logger.info(f"📁 DATA_DIR: {DATA_DIR}")
logger.info(f"📁 REPORTS_DIR: {REPORTS_DIR}")
logger.info(f"🔐 LINE設定: {'✅完了' if LINE_BOT_TOKEN and LINE_USER_ID else '❌要設定'}")
logger.info(f"🔐 Oura設定: {'✅完了' if OURA_TOKEN else '❌未設定'}")

# ===== HAEデータ変換機能 =====
class HAEDataConverter:
    """HAEデータをCSV形式に変換"""
    
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
        'carbohydrates': '糖質_g',
        'fiber': '食物繊維_g',
        'total_fat': '脂質_g'
    }
    
    def convert_hae_to_daily_row(self, hae_data: Dict) -> Dict:
        """HAE JSONを日次データ行に変換"""
        try:
            logger.info("🔄 HAEデータ変換開始")
            metrics = hae_data.get('data', {}).get('metrics', [])
            logger.info(f"📊 メトリクス数: {len(metrics)}")
            
            # 基本行データ
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
                '食物繊維_g': None,
                '脂質_g': None,
                'oura_total_calories': None,
                'oura_estimated_basal': None,
                'total_calories_updated': None,
                'calculation_method': 'HAE_AUTO'
            }
            
            # メトリクス変換
            converted_count = 0
            for metric in metrics:
                name = metric.get('name', '')
                if name in self.METRIC_MAPPING:
                    csv_column = self.METRIC_MAPPING[name]
                    data_points = metric.get('data', [])
                    
                    if data_points:
                        # 最新データを使用
                        latest_point = data_points[-1]
                        daily_row[csv_column] = latest_point.get('qty')
                        converted_count += 1
                        logger.info(f"✅ {name} → {csv_column}: {latest_point.get('qty')}")
            
            logger.info(f"🎯 変換完了: {converted_count}個のメトリクス")
            
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
            
            logger.info("✅ HAEデータ変換完了")
            return daily_row
            
        except Exception as e:
            logger.error(f"❌ HAEデータ変換エラー: {e}")
            logger.error(traceback.format_exc())
            return None

# ===== CSV統合機能 =====
class CSVDataIntegrator:
    """HAEデータを既存CSVに統合"""
    
    def __init__(self):
        self.reports_dir = Path(REPORTS_DIR)
        self.daily_csv = self.reports_dir / "日次データ.csv"
        self.ma7_csv = self.reports_dir / "7日移動平均データ.csv"
        self.index_csv = self.reports_dir / "インデックスデータ.csv"
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
                df = df[df['date'] != daily_row['date']]  # 既存の同日データ削除
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df
            
            # 日付順ソート
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # 保存
            df.to_csv(self.daily_csv, index=False, encoding='utf-8-sig')
            logger.info(f"💾 日次データ保存完了: {len(df)}行")
            
            # 移動平均再計算
            self.recalculate_moving_averages(df)
            
            logger.info("✅ CSV統合完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ CSV統合エラー: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def recalculate_moving_averages(self, df: pd.DataFrame):
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
            df.to_csv(self.ma7_csv, index=False, encoding='utf-8-sig')
            df.to_csv(self.index_csv, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ 移動平均計算完了: {calculated_count}カラム処理")
            
        except Exception as e:
            logger.error(f"❌ 移動平均計算エラー: {e}")
            logger.error(traceback.format_exc())

# ===== 健康分析エンジン =====
class HealthAnalyticsEngine:
    """健康指標分析エンジン"""
    
    def __init__(self):
        self.reports_dir = Path(REPORTS_DIR)
        self.target_body_fat_rate = 12.0
        logger.info(f"🧠 健康分析エンジン初期化（目標体脂肪率: {self.target_body_fat_rate}%）")
    
    def analyze_health_data(self) -> Optional[Dict]:
        """健康データ分析実行"""
        try:
            logger.info("🔄 健康分析開始")
            
            ma7_file = self.reports_dir / "7日移動平均データ.csv"
            if not ma7_file.exists():
                logger.error("❌ 移動平均データが見つかりません")
                return None
            
            df = pd.read_csv(ma7_file, encoding='utf-8-sig')
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
                'current_body_fat_rate': latest.get('体脂肪率'),
                'target_body_fat_rate': self.target_body_fat_rate,
                'body_fat_progress': {
                    '7day_change': latest.get('体脂肪率') - df.iloc[-8].get('体脂肪率', latest.get('体脂肪率')) if len(df) >= 8 else 0,
                    '14day_change': latest.get('体脂肪率') - df.iloc[-15].get('体脂肪率', latest.get('体脂肪率')) if len(df) >= 15 else 0,
                    '28day_change': latest.get('体脂肪率') - df.iloc[-29].get('体脂肪率', latest.get('体脂肪率')) if len(df) >= 29 else 0
                },
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

# ===== LINE通知機能 =====
class LineBotNotifier:
    """LINE Bot API通知"""
    
    def __init__(self):
        self.token = LINE_BOT_TOKEN
        self.user_id = LINE_USER_ID
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
            message = self.format_health_message(report)
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
    
    def format_health_message(self, report: Dict) -> str:
        """健康レポートメッセージ作成"""
        current_bf = report.get('current_body_fat_rate', 0)
        target_bf = report.get('target_body_fat_rate', 12.0)
        progress = report.get('body_fat_progress', {})
        
        message = f"""📊体脂肪率進捗 | {report.get('timestamp', 'N/A')}

🎯 {current_bf:.1f}%

現在: {current_bf:.1f}%  目標: {target_bf:.1f}%
28日: {progress.get('28day_change', 0):+.1f}%  14日: {progress.get('14day_change', 0):+.1f}%  7日: {progress.get('7day_change', 0):+.1f}%

💪体組成変化トレンド
体重: {report.get('body_composition', {}).get('weight', 0):.1f}kg
筋肉量: {report.get('body_composition', {}).get('muscle_mass', 0):.1f}kg
体脂肪量: {report.get('body_composition', {}).get('body_fat_mass', 0):.1f}kg

🔥カロリー収支状況
現在: {report.get('calorie_balance', {}).get('current', 0):.0f}kcal
7日平均: {report.get('calorie_balance', {}).get('7day_avg', 0):.0f}kcal

【v3.1】統合サーバー稼働中✅"""

        return message

# ===== 統合処理クラス =====
class CompleteProcessor:
    """統合処理エンジン"""
    
    def __init__(self):
        self.converter = HAEDataConverter()
        self.integrator = CSVDataIntegrator()
        self.analytics = HealthAnalyticsEngine()
        self.notifier = LineBotNotifier()
        logger.info("🚀 統合処理エンジン初期化完了")
    
    def process_hae_data_complete(self, hae_data: Dict) -> bool:
        """HAEデータ受信から通知まで完全処理"""
        try:
            logger.info("🎯 ===== 統合処理開始 =====")
            
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
                # 通知失敗でも処理は成功とする
            
            logger.info("🎉 ===== 統合処理完了 =====")
            return True
            
        except Exception as e:
            logger.error(f"❌ 統合処理エラー: {e}")
            logger.error(traceback.format_exc())
            return False

# ===== グローバル統合処理インスタンス =====
processor = CompleteProcessor()

# ===== Flask エンドポイント =====
@app.route('/', methods=['GET'])
def root():
    """ルートパス"""
    logger.info("🌐 ルートパスアクセス")
    return jsonify({
        'status': 'healthy',
        'service': 'Complete Cloud Health Management Server',
        'version': '3.1',
        'debug_mode': 'csv_analysis_enhanced',
        'features': ['HAE Reception', 'Auto Analysis', 'LINE Notification', 'CSV Content Display'],
        'endpoints': {
            'health_data': '/health-data (POST)',
            'health_check': '/health-check (GET)',
            'latest_data': '/latest-data (GET)',
            'manual_analysis': '/manual-analysis (POST)',
            'csv_content': '/csv-content (GET)',
            'csv_dates': '/csv-dates (GET)'
        }
    })

@app.route('/health-data', methods=['POST'])
def receive_health_data():
    """HAEデータ受信 → 即座統合処理"""
    try:
        session_id = request.headers.get('session-id', 'unknown')
        data = request.get_json()
        
        logger.info(f"🎯 ===== HAEデータ受信 (Session: {session_id}) =====")
        
        if not data:
            logger.error("❌ データなし")
            return jsonify({'error': 'No data received'}), 400
        
        # 生データ保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_data_{timestamp}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"💾 HAEデータ保存: {filename}")
        
        # 【重要】即座に統合処理実行
        logger.info("🚀 統合処理開始")
        success = processor.process_hae_data_complete(data)
        
        metrics = data.get('data', {}).get('metrics', [])
        workouts = data.get('data', {}).get('workouts', [])
        
        logger.info(f"📊 メトリクス: {len(metrics)}個")
        logger.info(f"🏃 ワークアウト: {len(workouts)}個")
        logger.info(f"🎯 処理結果: {'✅成功' if success else '❌失敗'}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data received and processed completely',
            'metrics_count': len(metrics),
            'workouts_count': len(workouts),
            'session_id': session_id,
            'processing_success': success,
            'features_executed': ['Data Conversion', 'CSV Integration', 'Health Analysis', 'LINE Notification'],
            'debug_info': {
                'timestamp': timestamp,
                'filename': filename,
                'data_dir': DATA_DIR,
                'reports_dir': REPORTS_DIR
            }
        })
    
    except Exception as e:
        logger.error(f"❌ データ受信・処理エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/health-check', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    logger.info("🔍 ヘルスチェック実行")
    return jsonify({
        'status': 'OK',
        'version': '3.1',
        'timestamp': datetime.now().isoformat(),
        'line_configured': bool(LINE_BOT_TOKEN and LINE_USER_ID),
        'oura_configured': bool(OURA_TOKEN),
        'directories': {
            'data_dir': DATA_DIR,
            'reports_dir': REPORTS_DIR,
            'data_dir_exists': os.path.exists(DATA_DIR),
            'reports_dir_exists': os.path.exists(REPORTS_DIR)
        }
    })

@app.route('/latest-data', methods=['GET'])
def get_latest_data():
    """最新データ確認"""
    try:
        logger.info("📋 最新データ確認")
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        if not files:
            logger.warning("📭 データファイルなし")
            return jsonify({'message': 'No data files found'})
        
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(DATA_DIR, x)))
        
        with open(os.path.join(DATA_DIR, latest_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"📄 最新ファイル: {latest_file}")
        return jsonify({
            'latest_file': latest_file,
            'data_preview': {
                'metrics_count': len(data.get('data', {}).get('metrics', [])),
                'workouts_count': len(data.get('data', {}).get('workouts', [])),
                'first_few_metrics': data.get('data', {}).get('metrics', [])[:3]
            }
        })
    
    except Exception as e:
        logger.error(f"❌ 最新データ確認エラー: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/manual-analysis', methods=['POST'])
def manual_analysis():
    """手動分析実行"""
    try:
        logger.info("🧠 ===== 手動分析実行 =====")
        report = processor.analytics.analyze_health_data()
        
        if report:
            # LINE通知送信
            notification_success = processor.notifier.send_health_report(report)
            
            logger.info(f"📱 LINE通知: {'✅成功' if notification_success else '❌失敗'}")
            
            return jsonify({
                'status': 'success',
                'message': 'Manual analysis completed',
                'report': report,
                'line_notification': notification_success
            })
        else:
            logger.error("❌ 分析失敗")
            return jsonify({'error': 'Analysis failed'}), 500
            
    except Exception as e:
        logger.error(f"❌ 手動分析エラー: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== CSV表示エンドポイント（新機能） =====
@app.route('/csv-content', methods=['GET'])
def get_csv_content():
    """CSV内容表示（日次データ・移動平均データ）"""
    try:
        logger.info("📊 CSV内容確認開始")
        
        reports_dir = Path(REPORTS_DIR)
        daily_csv = reports_dir / "日次データ.csv"
        ma7_csv = reports_dir / "7日移動平均データ.csv"
        index_csv = reports_dir / "インデックスデータ.csv"
        
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files_status': {},
            'csv_data': {}
        }
        
        # ファイル存在確認
        for name, path in [('daily', daily_csv), ('ma7', ma7_csv), ('index', index_csv)]:
            if path.exists():
                try:
                    df = pd.read_csv(path, encoding='utf-8-sig')
                    result['files_status'][name] = {
                        'exists': True,
                        'rows': len(df),
                        'columns': len(df.columns)
                    }
                    
                    # 最新10行を取得
                    if len(df) > 0:
                        latest_data = df.tail(10).to_dict('records')
                        result['csv_data'][name] = {
                            'columns': list(df.columns),
                            'latest_10_rows': latest_data,
                            'date_range': {
                                'first': df.iloc[0]['date'] if 'date' in df.columns else 'N/A',
                                'last': df.iloc[-1]['date'] if 'date' in df.columns else 'N/A'
                            }
                        }
                    else:
                        result['csv_data'][name] = {'message': 'Empty file'}
                        
                except Exception as e:
                    result['files_status'][name] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                result['files_status'][name] = {'exists': False}
        
        logger.info(f"📋 CSV確認完了")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ CSV確認エラー: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/csv-dates', methods=['GET'])
def get_csv_dates():
    """指定期間のCSVデータ確認"""
    try:
        start_date = request.args.get('start_date', '2025-08-08')
        end_date = request.args.get('end_date', '2025-08-11')
        
        logger.info(f"📅 期間指定CSV確認: {start_date} - {end_date}")
        
        reports_dir = Path(REPORTS_DIR)
        daily_csv = reports_dir / "日次データ.csv"
        
        if not daily_csv.exists():
            return jsonify({'error': 'Daily CSV file not found'}), 404
        
        df = pd.read_csv(daily_csv, encoding='utf-8-sig')
        
        # 期間フィルタリング
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            filtered_df = df.loc[mask]
            
            # 日付を文字列に戻す
            filtered_df = filtered_df.copy()
            filtered_df['date'] = filtered_df['date'].dt.strftime('%Y-%m-%d')
            
            result = {
                'period': f"{start_date} to {end_date}",
                'total_rows': len(filtered_df),
                'data': filtered_df.to_dict('records')
            }
            
            logger.info(f"📊 期間データ: {len(filtered_df)}行")
            return jsonify(result)
        else:
            return jsonify({'error': 'Date column not found'}), 400
            
    except Exception as e:
        logger.error(f"❌ 期間CSV確認エラー: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== アプリケーション初期化 =====
def initialize_app():
    """アプリケーション初期化"""
    logger.info("🌐 Complete Cloud Health Management Server v3.1 - CSV Enhanced")
    logger.info("=" * 60)
    logger.info("🎯 機能: HAE受信 → 変換 → 統合 → 分析 → LINE通知（完全自動）")
    logger.info("📊 新機能: CSV内容表示・期間指定データ確認")
    logger.info(f"📱 LINE設定: {'✅完了' if LINE_BOT_TOKEN and LINE_USER_ID else '❌要設定'}")
    logger.info(f"🔍 Oura設定: {'✅完了' if OURA_TOKEN else '❌未設定'}")
    logger.info(f"📁 データディレクトリ: {DATA_DIR}")
    logger.info(f"📊 レポートディレクトリ: {REPORTS_DIR}")
    logger.info("=" * 60)
    logger.info("✅ 統合サーバーv3.1起動完了")

# ===== アプリケーション起動時処理 =====
initialize_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"🚀 開発モード起動: http://localhost:{port}")
    logger.info(f"📡 HAE送信先: http://localhost:{port}/health-data")
    logger.info(f"🔍 ヘルスチェック: http://localhost:{port}/health-check")
    logger.info(f"📊 手動分析: http://localhost:{port}/manual-analysis (POST)")
    logger.info(f"📋 CSV内容確認: http://localhost:{port}/csv-content")
    logger.info(f"📅 期間データ確認: http://localhost:{port}/csv-dates?start_date=2025-08-08&end_date=2025-08-11")
    
    app.run(host='0.0.0.0', port=port, debug=False)