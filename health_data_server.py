"""
Health Auto Export データ受信サーバー
Health Auto Export REST API から送信されたデータを受信・保存
"""

from flask import Flask, request, jsonify
import json
import pandas as pd
from datetime import datetime, date
import os
import requests
from pathlib import Path
from typing import Dict, List, Any

app = Flask(__name__)

# データ保存ディレクトリ
DATA_DIR = os.path.join(os.path.dirname(__file__), 'health_api_data')
os.makedirs(DATA_DIR, exist_ok=True)

# Reports保存ディレクトリ（Railway Volume対応）
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
if os.path.exists('/app/reports'):  # Railway Volume環境
    REPORTS_DIR = '/app/reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

# Railway環境での起動時Volume初期化（Gunicorn対応）
try:
    initialize_volume_data()
    print(f"Volume initialization completed in {REPORTS_DIR}!")
    print("Health Auto Export Data Server Starting...")
    print(f"Data will be saved to: {DATA_DIR}")
    print(f"Reports will be saved to: {REPORTS_DIR}")
except Exception as e:
    print(f"Volume initialization error: {e}")


def initialize_volume_data():
    """
    Railway Volume初回起動時の過去データ移行処理
    REPORTS_DIR が空の場合、過去データを作成
    """
    reports_dir = Path(REPORTS_DIR)
    
    # ディレクトリが存在し、かつ必要なファイルがある場合はスキップ
    required_files = ["日次データ.csv", "7日移動平均データ.csv", "インデックスデータ.csv"]
    if all((reports_dir / f).exists() for f in required_files):
        print(f"Volume already contains data in {REPORTS_DIR}, skipping initialization")
        return
    
    print(f"Initializing volume with historical data in {REPORTS_DIR}...")
    
    # 簡易版の過去データ作成（GitHub接続に依存しない方法）
    try:
        # 日次データの基本ヘッダーとサンプルデータ
        daily_header = "date,体重_kg,筋肉量_kg,体脂肪量_kg,体脂肪率,カロリー収支_kcal,摂取カロリー_kcal,消費カロリー_kcal,基礎代謝_kcal,活動カロリー_kcal,歩数,睡眠時間_hours,体表温度_celsius,体表温変化_celsius,体表温偏差_celsius,体表温トレンド_celsius,タンパク質_g,糖質_g,食物繊維_g,脂質_g,oura_total_calories,oura_estimated_basal,total_calories_updated,calculation_method"
        
        # 基本的な空データファイルを作成
        with open(reports_dir / "日次データ.csv", 'w', encoding='utf-8') as f:
            f.write(daily_header + "\n")
            
        with open(reports_dir / "7日移動平均データ.csv", 'w', encoding='utf-8') as f:
            f.write(daily_header + ",体重_kg_ma7,体重_kg_ma14,体重_kg_ma28,筋肉量_kg_ma7,筋肉量_kg_ma14,筋肉量_kg_ma28,体脂肪量_kg_ma7,体脂肪量_kg_ma14,体脂肪量_kg_ma28,体脂肪率_ma7,体脂肪率_ma14,体脂肪率_ma28,カロリー収支_kcal_ma7,カロリー収支_kcal_ma14,カロリー収支_kcal_ma28,摂取カロリー_kcal_ma7,摂取カロリー_kcal_ma14,摂取カロリー_kcal_ma28,消費カロリー_kcal_ma7,消費カロリー_kcal_ma14,消費カロリー_kcal_ma28,基礎代謝_kcal_ma7,基礎代謝_kcal_ma14,基礎代謝_kcal_ma28,活動カロリー_kcal_ma7,活動カロリー_kcal_ma14,活動カロリー_kcal_ma28,歩数_ma7,歩数_ma14,歩数_ma28,睡眠時間_hours_ma7,睡眠時間_hours_ma14,睡眠時間_hours_ma28,体表温度_celsius_ma7,体表温度_celsius_ma14,体表温度_celsius_ma28,体表温変化_celsius_ma7,体表温変化_celsius_ma14,体表温変化_celsius_ma28,体表温偏差_celsius_ma7,体表温偏差_celsius_ma14,体表温偏差_celsius_ma28,体表温トレンド_celsius_ma7,体表温トレンド_celsius_ma14,体表温トレンド_celsius_ma28,タンパク質_g_ma7,タンパク質_g_ma14,タンパク質_g_ma28,糖質_g_ma7,糖質_g_ma14,糖質_g_ma28,食物繊維_g_ma7,食物繊維_g_ma14,食物繊維_g_ma28,脂質_g_ma7,脂質_g_ma14,脂質_g_ma28,oura_total_calories_ma7,oura_total_calories_ma14,oura_total_calories_ma28,oura_estimated_basal_ma7,oura_estimated_basal_ma14,oura_estimated_basal_ma28,total_calories_updated_ma7,total_calories_updated_ma14,total_calories_updated_ma28\n")
            
        with open(reports_dir / "インデックスデータ.csv", 'w', encoding='utf-8') as f:
            f.write(daily_header + "\n")
        
        print(f"Volume initialization completed in {REPORTS_DIR}!")
        
    except Exception as e:
        print(f"Error during volume initialization: {e}")

def save_raw_data(data: Dict[str, Any]) -> str:
    """受信した生データをJSONファイルに保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"health_data_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    return filename

def process_health_metrics(metrics: List[Dict]) -> pd.DataFrame:
    """ヘルスメトリクスを処理してDataFrameに変換"""
    processed_data = []
    
    for metric in metrics:
        name = metric.get('name', '')
        units = metric.get('units', '')
        data_points = metric.get('data', [])
        
        for point in data_points:
            row = {
                'metric_name': name,
                'units': units,
                'date': point.get('date', ''),
                'qty': point.get('qty', None),
                'source': metric.get('source', ''),
            }
            
            # 特殊なメトリクス（血圧、睡眠など）の追加フィールド処理
            for key, value in point.items():
                if key not in ['date', 'qty']:
                    row[f'{name}_{key}'] = value
            
            processed_data.append(row)
    
    return pd.DataFrame(processed_data) if processed_data else pd.DataFrame()

@app.route('/health-data', methods=['POST'])
def receive_health_data():
    """Health Auto Export からのデータ受信エンドポイント"""
    try:
        # セッションIDをヘッダーから取得
        session_id = request.headers.get('session-id', 'unknown')
        
        # JSONデータを取得
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # 生データを保存
        filename = save_raw_data(data)
        print(f"Data received (Session: {session_id}) - Saved as: {filename}")
        
        # データ構造を確認
        metrics = data.get('data', {}).get('metrics', [])
        workouts = data.get('data', {}).get('workouts', [])
        
        print(f"Received {len(metrics)} metrics, {len(workouts)} workouts")
        
        # メトリクスを処理してCSV保存
        if metrics:
            df_metrics = process_health_metrics(metrics)
            if not df_metrics.empty:
                csv_filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                csv_path = os.path.join(DATA_DIR, csv_filename)
                df_metrics.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"Metrics saved as CSV: {csv_filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data received and processed',
            'metrics_count': len(metrics),
            'workouts_count': len(workouts),
            'session_id': session_id
        })
    
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health-data', methods=['GET'])
def health_check():
    """サーバー稼働確認エンドポイント"""
    return jsonify({
        'status': 'Health Auto Export Data Server is running',
        'timestamp': datetime.now().isoformat(),
        'data_directory': DATA_DIR
    })

@app.route('/health-check', methods=['GET'])
def health_check_simple():
    """シンプルなヘルスチェックエンドポイント（監視用）"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/latest-data', methods=['GET'])
def get_latest_data():
    """最新のデータファイルを確認"""
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Health Auto Export should POST data to: http://localhost:{port}/health-data")
    print(f"Server health check: http://localhost:{port}/health-data (GET)")
    
    app.run(host='0.0.0.0', port=port, debug=False)
