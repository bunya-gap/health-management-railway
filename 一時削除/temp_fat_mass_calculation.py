#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体脂肪量変化計算検証スクリプト

7日移動平均データ.csvの日次データ列（体脂肪量_kg）を使用して
システム計算値を再検算・検証する
"""

import pandas as pd
from pathlib import Path

def calculate_fat_mass_changes():
    """体脂肪量変化計算"""
    
    # データ読み込み
    csv_file = Path("reports/7日移動平均データ.csv")
    
    if not csv_file.exists():
        print("[ERROR] 7日移動平均データ.csvが見つかりません")
        return
    
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    
    print("=== 体脂肪量変化計算検証 ===")
    print(f"総データ数: {len(df)}行")
    
    # 体脂肪量データのある行のみ抽出
    fat_data = df.dropna(subset=['体脂肪量_kg'])
    print(f"体脂肪量データあり: {len(fat_data)}行")
    
    if len(fat_data) < 1:
        print("[ERROR] 体脂肪量データが不足")
        return
        
    # 最新値
    latest_fat_mass = fat_data.iloc[-1]['体脂肪量_kg']
    latest_date = fat_data.iloc[-1]['date'].strftime('%Y-%m-%d')
    
    print(f"最新体脂肪量: {latest_fat_mass}kg ({latest_date})")
    
    # 期間別変化計算
    periods = [7, 14, 28]
    
    for days in periods:
        period_data = fat_data.tail(days)
        
        if len(period_data) >= 2:
            start_fat_mass = period_data.iloc[0]['体脂肪量_kg']
            start_date = period_data.iloc[0]['date'].strftime('%Y-%m-%d')
            
            change = latest_fat_mass - start_fat_mass
            
            print(f"\n【{days}日間変化】")
            print(f"開始: {start_fat_mass}kg ({start_date})")
            print(f"終了: {latest_fat_mass}kg ({latest_date})")
            print(f"変化: {change:+.1f}kg")
            
            # 実際のデータ日数
            actual_days = len(period_data)
            print(f"実際データ: {actual_days}日分")
            
        else:
            print(f"\n【{days}日間変化】: データ不足")
    
    # 最新5日分の詳細表示
    print("\n=== 最新5日分の詳細データ ===")
    recent_data = fat_data.tail(5)[['date', '体脂肪量_kg']]
    for _, row in recent_data.iterrows():
        date_str = row['date'].strftime('%m/%d')
        fat_mass = row['体脂肪量_kg']
        print(f"{date_str}: {fat_mass}kg")

if __name__ == "__main__":
    calculate_fat_mass_changes()
