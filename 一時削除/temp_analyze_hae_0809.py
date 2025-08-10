"""
8月9日HAEデータ詳細分析スクリプト
ファイル数・内容・処理方法を詳細調査
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def analyze_hae_data_0809():
    """8月9日のHAEデータを詳細分析"""
    print("=== 8月9日HAEデータ詳細分析 ===")
    
    health_api_data_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/health_api_data")
    
    # 8月9日のファイルを抽出
    files_0809 = list(health_api_data_dir.glob("*20250809*"))
    json_files = [f for f in files_0809 if f.suffix == '.json']
    csv_files = [f for f in files_0809 if f.suffix == '.csv']
    
    print(f"8月9日受信ファイル数:")
    print(f"  JSONファイル: {len(json_files)}個")
    print(f"  CSVファイル: {len(csv_files)}個")
    
    # 各JSONファイルの詳細分析
    for i, json_file in enumerate(sorted(json_files), 1):
        print(f"\n[ファイル{i}] {json_file.name}")
        print(f"受信時刻: {json_file.stem.split('_')[-1]}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # ファイルサイズ
            file_size = json_file.stat().st_size
            print(f"ファイルサイズ: {file_size:,} bytes")
            
            # メトリクス詳細
            metrics = data.get('data', {}).get('metrics', [])
            print(f"メトリクス数: {len(metrics)}個")
            
            print("含まれるメトリクス:")
            for metric in metrics:
                name = metric.get('name', 'Unknown')
                units = metric.get('units', 'None')
                data_points = len(metric.get('data', []))
                print(f"  • {name} ({units}) - {data_points}データポイント")
                
                # 最初のデータポイントのサンプル
                if metric.get('data'):
                    sample = metric['data'][0]
                    if 'qty' in sample:
                        print(f"    サンプル値: {sample['qty']}")
                    elif 'source' in sample:
                        print(f"    ソース: {sample['source']}")
            
            # 対応するCSVファイル確認
            csv_file = json_file.with_suffix('.csv')
            if csv_file.exists():
                df = pd.read_csv(csv_file, encoding='utf-8')
                print(f"CSVデータ: {len(df)}行 x {len(df.columns)}列")
                print(f"CSV日付: {df['date'].iloc[0] if 'date' in df.columns and len(df) > 0 else 'なし'}")
            else:
                print("対応するCSVファイルなし")
                
        except Exception as e:
            print(f"ERROR: ファイル読み込み失敗 - {e}")
    
    print(f"\n=== 処理フロー確認 ===")
    
    # reports/日次データ.csvで8月9日のデータ確認
    reports_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/reports")
    daily_csv = reports_dir / "日次データ.csv"
    
    if daily_csv.exists():
        df_daily = pd.read_csv(daily_csv, encoding='utf-8-sig')
        aug9_data = df_daily[df_daily['date'] == '2025-08-09']
        
        print(f"日次データ.csvの8月9日行数: {len(aug9_data)}")
        if len(aug9_data) > 0:
            print(f"処理済みデータ:")
            row = aug9_data.iloc[0]
            print(f"  体重: {row.get('体重_kg', 'なし')}kg")
            print(f"  体脂肪率: {row.get('体脂肪率', 'なし')}%")
            print(f"  摂取カロリー: {row.get('摂取カロリー_kcal', 'なし')}kcal")
            print(f"  消費カロリー: {row.get('消費カロリー_kcal', 'なし')}kcal")
        else:
            print("日次データ.csvに8月9日のデータなし")
    else:
        print("日次データ.csvが見つかりません")

if __name__ == "__main__":
    analyze_hae_data_0809()
