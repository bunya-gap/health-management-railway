"""
運動データ異常問題の詳細調査スクリプト
HAE受信データ vs 実際のOuraデータの比較分析
"""

import json
import pandas as pd
from pathlib import Path

def investigate_exercise_data_issue():
    """運動データ異常問題を詳細調査"""
    print("=== 運動データ異常問題調査 ===")
    print("実際のOuraデータ: 歩数18,728歩、活動カロリー910kcal")
    print("システム記録: 歩数2歩、活動カロリー1.455kcal")
    print("差異: 歩数9,364倍、活動カロリー626倍の異常")
    print()
    
    health_api_data_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/health_api_data")
    
    # 8月9日の全JSONファイルから運動データを抽出
    json_files = sorted(list(health_api_data_dir.glob("*20250809*.json")))
    
    total_steps = 0
    total_active_energy = 0
    
    for i, json_file in enumerate(json_files, 1):
        print(f"[ファイル{i}] {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metrics = data.get('data', {}).get('metrics', [])
            
            file_steps = 0
            file_active_energy = 0
            
            for metric in metrics:
                name = metric.get('name', '')
                
                # 歩数データの詳細確認
                if name == 'step_count':
                    steps_data = metric.get('data', [])
                    print(f"  歩数データポイント: {len(steps_data)}個")
                    
                    for point in steps_data:
                        if 'qty' in point:
                            steps_value = point['qty']
                            file_steps += steps_value
                            print(f"    歩数: {steps_value} ({point.get('date', 'unknown')})")
                
                # 活動カロリーデータの詳細確認
                if name == 'active_energy':
                    energy_data = metric.get('data', [])
                    print(f"  活動カロリーデータポイント: {len(energy_data)}個")
                    
                    for point in energy_data:
                        if 'qty' in point:
                            energy_value = point['qty']
                            file_active_energy += energy_value
                            print(f"    活動カロリー: {energy_value}kcal ({point.get('date', 'unknown')})")
            
            total_steps += file_steps
            total_active_energy += file_active_energy
            
            print(f"  ファイル{i}合計: 歩数{file_steps}歩、活動カロリー{file_active_energy:.2f}kcal")
            print()
            
        except Exception as e:
            print(f"  エラー: {e}")
            print()
    
    print(f"=== HAE受信データ合計 ===")
    print(f"歩数合計: {total_steps}歩")
    print(f"活動カロリー合計: {total_active_energy:.2f}kcal")
    print()
    
    print(f"=== 実際のOuraデータとの比較 ===")
    print(f"歩数:")
    print(f"  HAE受信: {total_steps}歩")
    print(f"  Oura実際: 18,728歩")
    print(f"  差異: {18728 - total_steps}歩 ({(18728/max(total_steps,1)):.1f}倍)")
    print()
    print(f"活動カロリー:")
    print(f"  HAE受信: {total_active_energy:.2f}kcal")
    print(f"  Oura実際: 910kcal")
    print(f"  差異: {910 - total_active_energy:.2f}kcal ({(910/max(total_active_energy,1)):.1f}倍)")
    print()
    
    # CSVファイルの確認
    print(f"=== CSV変換結果確認 ===")
    csv_files = sorted(list(health_api_data_dir.glob("*20250809*.csv")))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # 歩数データ確認
            step_rows = df[df['metric_name'] == 'step_count']
            if len(step_rows) > 0:
                csv_steps = step_rows['qty'].sum()
                print(f"{csv_file.name}: 歩数{csv_steps}歩")
            
            # 活動カロリー確認
            energy_rows = df[df['metric_name'] == 'active_energy']
            if len(energy_rows) > 0:
                csv_energy = energy_rows['qty'].sum()
                print(f"{csv_file.name}: 活動カロリー{csv_energy:.2f}kcal")
                
        except Exception as e:
            print(f"{csv_file.name}: CSVエラー - {e}")
    
    print()
    
    # 日次データ.csvの確認
    print(f"=== 最終統合結果確認 ===")
    reports_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/reports")
    daily_csv = reports_dir / "日次データ.csv"
    
    if daily_csv.exists():
        try:
            df_daily = pd.read_csv(daily_csv, encoding='utf-8-sig')
            aug9_data = df_daily[df_daily['date'] == '2025-08-09']
            
            if len(aug9_data) > 0:
                row = aug9_data.iloc[0]
                final_steps = row.get('歩数', 0)
                final_active = row.get('活動カロリー_kcal', 0)
                
                print(f"日次データ.csv:")
                print(f"  歩数: {final_steps}歩")
                print(f"  活動カロリー: {final_active}kcal")
                print()
                
                print(f"=== 問題箇所の特定 ===")
                if total_steps != final_steps:
                    print(f"❌ CSV統合処理に問題: HAE受信{total_steps}歩 → 最終{final_steps}歩")
                if total_active_energy != final_active:
                    print(f"❌ CSV統合処理に問題: HAE受信{total_active_energy:.2f}kcal → 最終{final_active}kcal")
                
                if total_steps < 18728:
                    print(f"❌ HAEデータ受信に問題: 実際18,728歩 → 受信{total_steps}歩")
                if total_active_energy < 910:
                    print(f"❌ HAEデータ受信に問題: 実際910kcal → 受信{total_active_energy:.2f}kcal")
                    
        except Exception as e:
            print(f"日次データ確認エラー: {e}")

if __name__ == "__main__":
    investigate_exercise_data_issue()
