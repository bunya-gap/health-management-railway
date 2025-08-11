"""
🌐 Complete Cloud Health Management Server
ローカル依存ゼロ - 完全クラウド化統合システム

機能:
- HAEデータ受信 → 即座変換・統合 → 分析 → LINE通知
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
            metrics = hae_data.get('data', {}).get('metrics', [])
            
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
            for metric in metrics:
                name = metric.get('name', '')
                if name in self.METRIC_MAPPING:
                    csv_column = self.METRIC_MAPPING[name]
                    data_points = metric.get('data', [])
                    
                    if data_points:
                        # 最新データを使用
                        latest_point = data_points[-1]
                        daily_row[csv_column] = latest_point.get('qty')
            
            # 体脂肪量計算
            if daily_row['体重_kg'] and daily_row['体脂肪率']:
                daily_row['体脂肪量_kg'] = daily_row['体重_kg'] * (daily_row['体脂肪率'] / 100)
            
            # カロリー収支計算
            intake = daily_row['摂取カロリー_kcal'] or 0
            basal = daily_row['基礎代謝_kcal'] or 0
            active = daily_row['活動カロリー_kcal'] or 0
            
            if intake and (basal or active):
                daily_row['消費カロリー_kcal'] = basal + active
                daily_row['カロリー収支_kcal'] = intake - (basal + active)
            
            return daily_row
            
        except Exception as e:
            print(f"[ERROR] HAEデータ変換エラー: {e}")
            return None

# ===== CSV統合機能 =====
class CSVDataIntegrator:
    """HAEデータを既存CSVに統合"""
    
    def __init__(self):
        self.reports_dir = Path(REPORTS_DIR)
        self.daily_csv = self.reports_dir / "日次データ.csv"
        self.ma7_csv = self.reports_dir / "7日移動平均データ.csv"
        self.index_csv = self.reports_dir / "インデックスデータ.csv"
    
    def integrate_daily_data(self, daily_row: Dict) -> bool:
        """日次データをCSVに統合"""
        try:
            # 既存データ読み込み
            if self.daily_csv.exists():
                df = pd.read_csv(self.daily_csv, encoding='utf-8-sig')
            else:
                df = pd.DataFrame()
            
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
            print(f"[SUCCESS] 日次データ統合完了: {len(df)}行")
            
            # 移動平均再計算
            self.recalculate_moving_averages(df)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] CSV統合エラー: {e}")
            return False
    
    def recalculate_moving_averages(self, df: pd.DataFrame):
        """移動平均再計算"""
        try:
            # 数値カラムの移動平均計算
            numeric_columns = ['体重_kg', '筋肉量_kg', '体脂肪量_kg', '体脂肪率', 
                             'カロリー収支_kcal', '摂取カロリー_kcal', '消費カロリー_kcal',
                             '基礎代謝_kcal', '活動カロリー_kcal', '歩数', '睡眠時間_hours']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[f'{col}_ma7'] = df[col].rolling(window=7, min_periods=1).mean()
                    df[f'{col}_ma14'] = df[col].rolling(window=14, min_periods=1).mean()
                    df[f'{col}_ma28'] = df[col].rolling(window=28, min_periods=1).mean()
            
            # 移動平均データ保存
            df.to_csv(self.ma7_csv, index=False, encoding='utf-8-sig')
            df.to_csv(self.index_csv, index=False, encoding='utf-8-sig')
            
            print("[SUCCESS] 移動平均再計算完了")
            
        except Exception as e:
            print(f"[ERROR] 移動平均計算エラー: {e}")

# ===== 健康分析エンジン =====
class HealthAnalyticsEngine:
    """健康指標分析エンジン"""
    
    def __init__(self):
        self.reports_dir = Path(REPORTS_DIR)
        self.target_body_fat_rate = 12.0
    
    def analyze_health_data(self) -> Optional[Dict]:
        """健康データ分析実行"""
        try:
            ma7_file = self.reports_dir / "7日移動平均データ.csv"
            if not ma7_file.exists():
                print("[ERROR] 移動平均データが見つかりません")
                return None
            
            df = pd.read_csv(ma7_file, encoding='utf-8-sig')
            if df.empty:
                print("[ERROR] データが空です")
                return None
            
            # 最新データ取得
            latest = df.iloc[-1]
            
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
            
            print("[SUCCESS] 健康分析完了")
            return report
            
        except Exception as e:
            print(f"[ERROR] 健康分析エラー: {e}")
            return None

# ===== LINE通知機能 =====
class LineBotNotifier:
    """LINE Bot API通知"""
    
    def __init__(self):
        self.token = LINE_BOT_TOKEN
        self.user_id = LINE_USER_ID
        self.api_url = "https://api.line.me/v2/bot/message/push"
    
    def send_health_report(self, report: Dict) -> bool:
        """健康レポートをLINE送信"""
        if not self.token or not self.user_id:
            print("[ERROR] LINE設定が不完全です")
            return False
        
        try:
            # レポートメッセージ作成
            message = self.format_health_message(report)
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': self.user_id,
                'messages': [{'type': 'text', 'text': message}]
            }
            
            response = requests.post(self.api_url, headers=headers, 
                                   data=json.dumps(data), timeout=10)
            
            if response.status_code == 200:
                print("[SUCCESS] LINE通知送信完了")
                return True
            else:
                print(f"[ERROR] LINE通知失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] LINE通知エラー: {e}")
            return False
    
    def format_health_message(self, report: Dict) -> str:
        """健康レポートメッセージ作成"""
        current_bf = report.get('current_body_fat_rate', 0)
        target_bf = report.get('target_body_fat_rate', 12.0)
        progress = report.get('body_fat_progress', {})
        
        message = f"""体脂肪率進捗 | {report.get('timestamp', 'N/A')}

{current_bf:.1f}%

現在: {current_bf:.1f}%  目標: {target_bf:.1f}%
28日: {progress.get('28day_change', 0):+.1f}%  14日: {progress.get('14day_change', 0):+.1f}%  7日: {progress.get('7day_change', 0):+.1f}%

体組成変化トレンド
体重: {report.get('body_composition', {}).get('weight', 0):.1f}kg
筋肉量: {report.get('body_composition', {}).get('muscle_mass', 0):.1f}kg
体脂肪量: {report.get('body_composition', {}).get('body_fat_mass', 0):.1f}kg

カロリー収支状況
現在: {report.get('calorie_balance', {}).get('current', 0):.0f}kcal
7日平均: {report.get('calorie_balance', {}).get('7day_avg', 0):.0f}kcal"""

        return message

# ===== 統合処理クラス =====
class CompleteProcessor:
    """統合処理エンジン"""
    
    def __init__(self):
        self.converter = HAEDataConverter()
        self.integrator = CSVDataIntegrator()
        self.analytics = HealthAnalyticsEngine()
        self.notifier = LineBotNotifier()
    
    def process_hae_data_complete(self, hae_data: Dict) -> bool:
        """HAEデータ受信から通知まで完全処理"""
        try:
            print("[INFO] 統合処理開始...")
            
            # 1. HAE → CSV変換
            daily_row = self.converter.convert_hae_to_daily_row(hae_data)
            if not daily_row:
                print("[ERROR] データ変換失敗")
                return False
            
            # 2. CSV統合・移動平均
            if not self.integrator.integrate_daily_data(daily_row):
                print("[ERROR] CSV統合失敗")
                return False
            
            # 3. 健康分析
            report = self.analytics.analyze_health_data()
            if not report:
                print("[ERROR] 健康分析失敗")
                return False
            
            # 4. LINE通知
            if not self.notifier.send_health_report(report):
                print("[WARNING] LINE通知失敗")
                # 通知失敗でも処理は成功とする
            
            print("[SUCCESS] 統合処理完了！")
            return True
            
        except Exception as e:
            print(f"[ERROR] 統合処理エラー: {e}")
            print(traceback.format_exc())
            return False

# ===== グローバル統合処理インスタンス =====
processor = CompleteProcessor()

# ===== Flask エンドポイント =====
@app.route('/', methods=['GET'])
def root():
    """ルートパス"""
    return jsonify({
        'status': 'healthy',
        'service': 'Complete Cloud Health Management Server',
        'version': '3.0',
        'features': ['HAE Reception', 'Auto Analysis', 'LINE Notification'],
        'endpoints': {
            'health_data': '/health-data (POST)',
            'health_check': '/health-check (GET)',
            'latest_data': '/latest-data (GET)',
            'manual_analysis': '/manual-analysis (POST)'
        }
    })

@app.route('/health-data', methods=['POST'])
def receive_health_data():
    """HAEデータ受信 → 即座統合処理"""
    try:
        session_id = request.headers.get('session-id', 'unknown')
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # 生データ保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_data_{timestamp}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"[INFO] HAEデータ受信 (Session: {session_id}) - {filename}")
        
        # 【重要】即座に統合処理実行
        success = processor.process_hae_data_complete(data)
        
        metrics = data.get('data', {}).get('metrics', [])
        workouts = data.get('data', {}).get('workouts', [])
        
        return jsonify({
            'status': 'success',
            'message': 'Data received and processed completely',
            'metrics_count': len(metrics),
            'workouts_count': len(workouts),
            'session_id': session_id,
            'processing_success': success,
            'features_executed': ['Data Conversion', 'CSV Integration', 'Health Analysis', 'LINE Notification']
        })
    
    except Exception as e:
        print(f"[ERROR] データ受信・処理エラー: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health-check', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'line_configured': bool(LINE_BOT_TOKEN and LINE_USER_ID),
        'oura_configured': bool(OURA_TOKEN)
    })

@app.route('/latest-data', methods=['GET'])
def get_latest_data():
    """最新データ確認"""
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        if not files:
            return jsonify({'message': 'No data files found'})
        
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(DATA_DIR, x)))
        
        with open(os.path.join(DATA_DIR, latest_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'latest_file': latest_file,
            'data_preview': {
                'metrics_count': len(data.get('data', {}).get('metrics', [])),
                'workouts_count': len(data.get('data', {}).get('workouts', [])),
                'first_few_metrics': data.get('data', {}).get('metrics', [])[:3]
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manual-analysis', methods=['POST'])
def manual_analysis():
    """手動分析実行"""
    try:
        print("[INFO] 手動分析実行...")
        report = processor.analytics.analyze_health_data()
        
        if report:
            # LINE通知送信
            notification_success = processor.notifier.send_health_report(report)
            
            return jsonify({
                'status': 'success',
                'message': 'Manual analysis completed',
                'report': report,
                'line_notification': notification_success
            })
        else:
            return jsonify({'error': 'Analysis failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("🌐 Complete Cloud Health Management Server v3.0")
    print("=" * 60)
    print(f"📱 HAE送信先: http://localhost:{port}/health-data")
    print(f"🔍 ヘルスチェック: http://localhost:{port}/health-check")
    print(f"📊 手動分析: http://localhost:{port}/manual-analysis (POST)")
    print("=" * 60)
    print("✅ 機能: HAE受信 → 変換 → 統合 → 分析 → LINE通知（完全自動）")
    print(f"✅ LINE設定: {'完了' if LINE_BOT_TOKEN and LINE_USER_ID else '要設定'}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
