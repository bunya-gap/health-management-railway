#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
28日・14日移動平均計算検証スクリプト

修正後のシステムが正しく移動平均の変化を計算しているかを検証
"""

import pandas as pd
from pathlib import Path

def verify_ma_calculations():
    """移動平均変化計算の検証"""
    
    print("=== 28日・14日移動平均計算検証 ===")
    
    csv_file = Path("reports/7日移動平均データ.csv")
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    
    # 最新データ
    latest = df.iloc[-1]
    print(f"最新日: {latest['date'].strftime('%Y-%m-%d')}")
    
    print(f"\n【最新の移動平均値（8/09）】")
    print(f"体脂肪量_ma7:  {latest['体脂肪量_kg_ma7']}kg")
    print(f"体脂肪量_ma14: {latest['体脂肪量_kg_ma14']}kg")
    print(f"体脂肪量_ma28: {latest['体脂肪量_kg_ma28']}kg")
    
    # 期間別変化検証
    periods = [7, 14, 28]
    
    for days in periods:
        col_name = f'体脂肪量_kg_ma{days}'
        valid_data = df.dropna(subset=[col_name])
        
        if len(valid_data) >= days:
            current_value = valid_data.iloc[-1][col_name]
            past_value = valid_data.iloc[-days][col_name]
            change = current_value - past_value
            
            past_date = valid_data.iloc[-days]['date'].strftime('%m/%d')
            current_date = valid_data.iloc[-1]['date'].strftime('%m/%d')
            
            print(f"\n【{days}日移動平均変化】")
            print(f"{past_date}: {past_value}kg")
            print(f"{current_date}: {current_value}kg")
            print(f"変化: {change:+.1f}kg")
        else:
            print(f"\n【{days}日移動平均変化】: データ不足")

if __name__ == "__main__":
    verify_ma_calculations()
