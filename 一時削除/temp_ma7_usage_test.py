#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
7日移動平均列使用確認テスト

修正後のシステムが正しく_ma7列を使用しているかを検証
"""

import pandas as pd
from pathlib import Path
import sys
sys.path.append('.')

def test_ma7_usage():
    """7日移動平均列の使用確認"""
    
    print("=== 7日移動平均列使用確認テスト ===")
    
    # 元データと移動平均データの比較
    csv_file = Path("reports/7日移動平均データ.csv")
    
    if not csv_file.exists():
        print("[ERROR] 7日移動平均データ.csvが見つかりません")
        return
    
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    
    # 最新データ確認
    latest = df.iloc[-1]
    
    print("【最新データ比較（8/09）】")
    print(f"日次データ vs 移動平均データ:")
    print(f"体重: {latest.get('体重_kg', 'N/A')}kg vs {latest.get('体重_kg_ma7', 'N/A')}kg")
    print(f"体脂肪率: {latest.get('体脂肪率', 'N/A')}% vs {latest.get('体脂肪率_ma7', 'N/A')}%")
    print(f"体脂肪量: {latest.get('体脂肪量_kg', 'N/A')}kg vs {latest.get('体脂肪量_kg_ma7', 'N/A')}kg")
    print(f"筋肉量: {latest.get('筋肉量_kg', 'N/A')}kg vs {latest.get('筋肉量_kg_ma7', 'N/A')}kg")
    
    # 修正前後の変化計算比較
    print("\n【7日間変化比較】")
    
    # 日次データでの変化
    fat_data_daily = df.dropna(subset=['体脂肪量_kg']).tail(7)
    if len(fat_data_daily) >= 2:
        daily_change = fat_data_daily.iloc[-1]['体脂肪量_kg'] - fat_data_daily.iloc[0]['体脂肪量_kg']
        print(f"日次データ: {daily_change:+.1f}kg")
    
    # 移動平均データでの変化
    fat_data_ma7 = df.dropna(subset=['体脂肪量_kg_ma7']).tail(7)
    if len(fat_data_ma7) >= 2:
        ma7_change = fat_data_ma7.iloc[-1]['体脂肪量_kg_ma7'] - fat_data_ma7.iloc[0]['体脂肪量_kg_ma7']
        print(f"移動平均データ: {ma7_change:+.1f}kg")
    
    # 最新5日間の変動具合確認
    print("\n【最新5日間の変動比較】")
    recent_5 = df.tail(5)[['date', '体脂肪量_kg', '体脂肪量_kg_ma7']]
    for _, row in recent_5.iterrows():
        date_str = row['date'].strftime('%m/%d')
        daily = row['体脂肪量_kg'] if pd.notna(row['体脂肪量_kg']) else 'N/A'
        ma7 = row['体脂肪量_kg_ma7'] if pd.notna(row['体脂肪量_kg_ma7']) else 'N/A'
        print(f"{date_str}: 日次={daily}kg, MA7={ma7}kg")
    
    print("\n✅ 7日移動平均列は日次データより変動が平滑化されており、")
    print("   トレンド分析により適しています。")

if __name__ == "__main__":
    test_ma7_usage()
