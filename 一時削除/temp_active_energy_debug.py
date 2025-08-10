#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
活動カロリー処理のデバッグスクリプト
実際のHAEデータ処理でどのような値が計算されているかを確認
"""

import json
import os
from hae_data_converter import HAEDataConverter

def debug_active_energy_processing():
    """最新HAEデータで活動カロリー処理をデバッグ"""
    
    # 最新のHAEデータファイルを確認
    data_dir = r"C:\Users\terada\Desktop\apps\体組成管理app\health_api_data"
    json_files = [f for f in os.listdir(data_dir) if f.startswith('health_data_') and f.endswith('.json')]
    if not json_files:
        print("[ERROR] HAEデータファイルが見つかりません")
        return
    
    latest_file = sorted(json_files)[-1]
    json_path = os.path.join(data_dir, latest_file)
    
    print(f"[INFO] 処理対象ファイル: {latest_file}")
    
    # HAEデータを読み込み
    with open(json_path, 'r', encoding='utf-8') as f:
        hae_data = json.load(f)
    
    # active_energyメトリクスを探す（正しい構造）
    metrics = hae_data.get('data', {}).get('metrics', [])
    active_energy_metric = None
    
    for metric in metrics:
        if metric.get('name') == 'active_energy':
            active_energy_metric = metric
            break
    
    if not active_energy_metric:
        print("[ERROR] active_energyメトリクスが見つかりません")
        return
    
    print(f"[INFO] active_energyデータポイント数: {len(active_energy_metric.get('data', []))}")
    
    # 最初の5件を表示
    data_points = active_energy_metric.get('data', [])
    print("\n=== 最初の5件のデータポイント ===")
    for i, point in enumerate(data_points[:5]):
        date = point.get('date', '')
        qty = point.get('qty', 0)
        print(f"{i+1}. {date}: {qty}kcal")
    
    # HAEDataConverterを使用して処理
    converter = HAEDataConverter(r"C:\Users\terada\Desktop\apps\体組成管理app\health_api_data")
    processed_metric = converter.process_metric(active_energy_metric)
    
    print(f"\n=== 処理結果 ===")
    if processed_metric:
        print(f"累積値: {processed_metric['value']}kcal")
        print(f"ソース: {processed_metric['source']}")
        print(f"日付: {processed_metric['date']}")
    else:
        print("処理に失敗しました")
    
    # 手動で累積計算も実行
    manual_total = sum(point.get('qty', 0) for point in data_points)
    print(f"\n=== 手動累積計算 ===")
    print(f"手動計算値: {manual_total}kcal")
    print(f"データ件数: {len(data_points)}件")
    
    return processed_metric

if __name__ == "__main__":
    debug_active_energy_processing()
