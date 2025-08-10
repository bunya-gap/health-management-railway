"""
8月9日HAEデータ詳細分析スクリプト（エンコーディング修正版）
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def analyze_hae_data_0809_fixed():
    """8月9日のHAEデータを詳細分析（修正版）"""
    print("=== 8月9日HAEデータ詳細分析（修正版） ===")
    
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
        
        # 受信時刻を解析
        timestamp_str = json_file.stem.split('_')[-1]
        try:
            timestamp = datetime.strptime(timestamp_str, '%H%M%S')
            print(f"受信時刻: {timestamp.strftime('%H:%M:%S')}")
        except:
            print(f"受信時刻: {timestamp_str}")
        
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
                
                # Unicode文字を安全に処理
                try:
                    print(f"  - {name} ({units}) - {data_points}データポイント")
                except UnicodeEncodeError:
                    print(f"  - {name.encode('ascii', 'ignore').decode('ascii')} ({units}) - {data_points}データポイント")
                
                # 体組成データの値をチェック
                if name in ['weight_body_mass', 'body_fat_percentage', 'lean_body_mass']:
                    if metric.get('data'):
                        sample = metric['data'][-1]  # 最後の値
                        if 'qty' in sample:
                            print(f"    最新値: {sample['qty']}")
                
                # カロリーデータの合計をチェック  
                if name in ['dietary_energy', 'active_energy', 'basal_energy_burned']:
                    total = 0
                    for point in metric.get('data', []):
                        if 'qty' in point:
                            total += point['qty']
                    if total > 0:
                        print(f"    合計: {total}")
            
            # 対応するCSVファイル確認
            csv_file = json_file.with_suffix('.csv')
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    print(f"CSVデータ: {len(df)}行 x {len(df.columns)}列")
                    if 'date' in df.columns and len(df) > 0:
                        print(f"CSV日付: {df['date'].iloc[0]}")
                except Exception as e:
                    print(f"CSV読み込みエラー: {e}")
            else:
                print("対応するCSVファイルなし")
                
        except Exception as e:
            print(f"ERROR: ファイル読み込み失敗 - {e}")
    
    print(f"\n=== 統合処理結果確認 ===")
    
    # reports/日次データ.csvで8月9日のデータ確認
    reports_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/reports")
    daily_csv = reports_dir / "日次データ.csv"
    
    if daily_csv.exists():
        try:
            df_daily = pd.read_csv(daily_csv, encoding='utf-8-sig')
            aug9_data = df_daily[df_daily['date'] == '2025-08-09']
            
            print(f"日次データ.csvの8月9日行数: {len(aug9_data)}")
            if len(aug9_data) > 0:
                print(f"最終統合結果:")
                row = aug9_data.iloc[0]
                print(f"  体重: {row.get('体重_kg', 'なし')}kg")
                print(f"  体脂肪率: {row.get('体脂肪率', 'なし')}%") 
                print(f"  筋肉量: {row.get('筋肉量_kg', 'なし')}kg")
                print(f"  摂取カロリー: {row.get('摂取カロリー_kcal', 'なし')}kcal")
                print(f"  基礎代謝: {row.get('基礎代謝_kcal', 'なし')}kcal")
                print(f"  活動カロリー: {row.get('活動カロリー_kcal', 'なし')}kcal")
                print(f"  消費カロリー: {row.get('消費カロリー_kcal', 'なし')}kcal")
                print(f"  カロリー収支: {row.get('カロリー収支_kcal', 'なし')}kcal")
                print(f"  歩数: {row.get('歩数', 'なし')}歩")
                print(f"  タンパク質: {row.get('タンパク質_g', 'なし')}g")
                print(f"  糖質: {row.get('糖質_g', 'なし')}g")
                print(f"  脂質: {row.get('脂質_g', 'なし')}g")
            else:
                print("日次データ.csvに8月9日のデータなし")
        except Exception as e:
            print(f"日次データ読み込みエラー: {e}")
    else:
        print("日次データ.csvが見つかりません")

if __name__ == "__main__":
    analyze_hae_data_0809_fixed()
