#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のHAEデータから歩数を計算するスクリプト
修正されたコードの効果を実証
"""

import csv
import os

def calculate_actual_steps():
    """最新HAEデータCSVから8/9の歩数を実際に計算"""
    csv_file = r"C:\Users\terada\Desktop\apps\体組成管理app\health_api_data\metrics_20250810_071210.csv"
    
    if not os.path.exists(csv_file):
        print(f"[ERROR] ファイルが見つかりません: {csv_file}")
        return None
    
    total_steps = 0
    step_records = 0
    target_date = "2025-08-09"
    
    print(f"[INFO] ファイル読み込み開始: {csv_file}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 4 and row[0] == 'step_count' and target_date in row[2]:
                    try:
                        steps = float(row[3])
                        total_steps += steps
                        step_records += 1
                        
                        # 最初の10個と最後の10個を表示
                        if step_records <= 10 or step_records % 100 == 0:
                            print(f"  {row[2]}: {steps}歩 (累計: {total_steps}歩)")
                    except (ValueError, IndexError):
                        continue
    
        print(f"\n=== 計算結果 ===")
        print(f"対象日: {target_date}")
        print(f"歩数レコード数: {step_records}個")
        print(f"合計歩数: {total_steps:,.0f}歩")
        
        # 修正前の値と比較
        old_value = 2.0
        improvement_ratio = total_steps / old_value if old_value > 0 else 0
        
        print(f"\n=== 修正効果 ===")
        print(f"修正前（最初の1分のみ）: {old_value}歩")
        print(f"修正後（全分累積）: {total_steps:,.0f}歩")
        print(f"改善倍率: {improvement_ratio:,.0f}倍")
        
        return total_steps
        
    except Exception as e:
        print(f"[ERROR] ファイル読み込みエラー: {e}")
        return None

if __name__ == "__main__":
    result = calculate_actual_steps()
    if result:
        print(f"\n✅ 実際の計算結果: {result:,.0f}歩")
    else:
        print("\n❌ 計算に失敗しました")
