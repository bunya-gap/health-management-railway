#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正しい移動平均使用検証スクリプト

体脂肪率、体脂肪量、筋肉量で適切な移動平均列が使用されているかを検証
"""

import pandas as pd
from pathlib import Path

def verify_correct_ma_usage():
    """正しい移動平均使用の検証"""
    
    print("=== 正しい移動平均使用検証 ===")
    
    csv_file = Path("reports/7日移動平均データ.csv")
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    
    # 最新データ
    latest = df.iloc[-1]
    print(f"最新日: {latest['date'].strftime('%Y-%m-%d')}")
    
    print("\n【各移動平均の最新値（8/09）】")
    
    # 体脂肪率
    print(f"体脂肪率:")
    print(f"  7日MA:  {latest['体脂肪率_ma7']:.2f}%")
    print(f"  14日MA: {latest['体脂肪率_ma14']:.2f}%") 
    print(f"  28日MA: {latest['体脂肪率_ma28']:.2f}%")
    
    # 体脂肪量  
    print(f"体脂肪量:")
    print(f"  7日MA:  {latest['体脂肪量_kg_ma7']:.2f}kg")
    print(f"  14日MA: {latest['体脂肪量_kg_ma14']:.2f}kg")
    print(f"  28日MA: {latest['体脂肪量_kg_ma28']:.2f}kg")
    
    # 筋肉量
    print(f"筋肉量:")
    print(f"  7日MA:  {latest['筋肉量_kg_ma7']:.2f}kg") 
    print(f"  14日MA: {latest['筋肉量_kg_ma14']:.2f}kg")
    print(f"  28日MA: {latest['筋肉量_kg_ma28']:.2f}kg")
    
    print("\n【期間別変化検証】")
    
    # 各指標・各期間の変化を手動計算
    metrics = [
        ('体脂肪率', 'body_fat_rate'),
        ('体脂肪量', 'body_fat_mass'), 
        ('筋肉量', 'muscle_mass')
    ]
    
    for metric_name, metric_key in metrics:
        print(f"\n◆ {metric_name}変化:")
        
        for days in [7, 14, 28]:
            col_name = f'{metric_name.replace("率", "").replace("脂肪", "脂肪量").replace("量量", "量")}_kg_ma{days}' if 'kg' in metric_name else f'{metric_name}_ma{days}'
            
            # CSVの列名調整
            if metric_name == '体脂肪率':
                col_name = f'体脂肪率_ma{days}'
            elif metric_name == '体脂肪量':
                col_name = f'体脂肪量_kg_ma{days}'
            elif metric_name == '筋肉量':
                col_name = f'筋肉量_kg_ma{days}'
            
            valid_data = df.dropna(subset=[col_name])
            
            if len(valid_data) >= days:
                current_value = valid_data.iloc[-1][col_name]
                past_value = valid_data.iloc[-days][col_name]
                change = current_value - past_value
                
                past_date = valid_data.iloc[-days]['date'].strftime('%m/%d')
                current_date = valid_data.iloc[-1]['date'].strftime('%m/%d')
                
                unit = '%' if '率' in metric_name else 'kg'
                print(f"  {days}日: {past_date}({past_value:.2f}{unit}) → {current_date}({current_value:.2f}{unit}) = {change:+.2f}{unit}")
            else:
                print(f"  {days}日: データ不足")

if __name__ == "__main__":
    verify_correct_ma_usage()
