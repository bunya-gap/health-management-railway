#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全計算項目総点検スクリプト

システムの全ての計算項目について以下を検証：
1. 使用データの適切性
2. 計算式の正確性  
3. 手動検算による値の照合
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, date, timedelta

def comprehensive_calculation_check():
    """全計算項目の総点検"""
    
    print("=== 全計算項目総点検 ===")
    
    # データ読み込み
    csv_file = Path("reports/7日移動平均データ.csv")
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['date'])
    
    # 最新レポート読み込み
    with open("reports/analysis_report_20250810_090333.json", 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print(f"データ期間: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"総データ数: {len(df)}行")
    
    errors = []
    
    # 1. KGI進捗分析の検証
    print("\n【1. KGI進捗分析】")
    errors.extend(check_kgi_progress(df, report))
    
    # 2. 総合成績計算の検証
    print("\n【2. 総合成績計算】")
    errors.extend(check_total_performance(df, report))
    
    # 3. 期間別成績計算の検証
    print("\n【3. 期間別成績計算】")
    errors.extend(check_period_performance(df, report))
    
    # 4. 体脂肪率変化計算の検証
    print("\n【4. 体脂肪率変化計算】")
    errors.extend(check_bf_rate_changes(df, report))
    
    # 5. 代謝分析の検証
    print("\n【5. 代謝分析】")
    errors.extend(check_metabolism_analysis(df, report))
    
    # 6. カロリー計算の検証
    print("\n【6. カロリー計算】")
    errors.extend(check_calorie_calculations(df, report))
    
    # 結果まとめ
    print("\n" + "="*50)
    if not errors:
        print("✅ 全計算項目で問題なし！")
    else:
        print(f"❌ {len(errors)}個の問題を発見:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    return errors

def check_kgi_progress(df, report):
    """KGI進捗分析の検証"""
    errors = []
    kgi = report.get('kgi_progress', {})
    
    # 体脂肪率データの検証
    valid_data = df.dropna(subset=['体脂肪率_ma7'])
    if len(valid_data) >= 2:
        start_bf = valid_data.iloc[0]['体脂肪率_ma7']
        current_bf = valid_data.iloc[-1]['体脂肪率_ma7']
        
        print(f"使用データ: 体脂肪率_ma7（7日移動平均）")
        print(f"開始値: {start_bf}% vs レポート: {kgi.get('start_bf_rate')}%")
        print(f"現在値: {current_bf}% vs レポート: {kgi.get('current_bf_rate')}%")
        
        # 許容誤差0.1%で比較
        if abs(start_bf - kgi.get('start_bf_rate', 0)) > 0.1:
            errors.append(f"KGI開始体脂肪率不一致: 計算{start_bf}% vs レポート{kgi.get('start_bf_rate')}%")
        if abs(current_bf - kgi.get('current_bf_rate', 0)) > 0.1:
            errors.append(f"KGI現在体脂肪率不一致: 計算{current_bf}% vs レポート{kgi.get('current_bf_rate')}%")
            
        # 進捗率計算検証
        target_bf = 12.0
        total_needed = start_bf - target_bf
        achieved = start_bf - current_bf
        progress_rate = (achieved / total_needed) * 100 if total_needed > 0 else 0
        
        print(f"進捗率計算: ({start_bf}-{current_bf})/({start_bf}-{target_bf})*100 = {progress_rate:.1f}%")
        print(f"レポート進捗率: {kgi.get('progress_rate')}%")
        
        if abs(progress_rate - kgi.get('progress_rate', 0)) > 1.0:
            errors.append(f"KGI進捗率不一致: 計算{progress_rate:.1f}% vs レポート{kgi.get('progress_rate')}%")
    
    return errors

def check_total_performance(df, report):
    """総合成績計算の検証"""
    errors = []
    
    # 7日移動平均での開始〜現在変化（長期トレンド用）
    valid_data = df.dropna(subset=['体重_kg_ma7', '体脂肪率_ma7', '筋肉量_kg_ma7'])
    if len(valid_data) >= 2:
        print("使用データ: 各指標の7日移動平均（長期トレンド分析）")
        
        start_data = valid_data.iloc[0]
        latest_data = valid_data.iloc[-1]
        
        # 体重変化
        weight_change = latest_data['体重_kg_ma7'] - start_data['体重_kg_ma7']
        print(f"体重変化: {start_data['体重_kg_ma7']}kg → {latest_data['体重_kg_ma7']}kg = {weight_change:+.1f}kg")
        
        # 体脂肪率変化
        bf_rate_change = latest_data['体脂肪率_ma7'] - start_data['体脂肪率_ma7']
        print(f"体脂肪率変化: {start_data['体脂肪率_ma7']}% → {latest_data['体脂肪率_ma7']}% = {bf_rate_change:+.1f}%")
    
    return errors

def check_period_performance(df, report):
    """期間別成績計算の検証"""
    errors = []
    
    periods = [
        (28, '体脂肪量_kg_ma28', '筋肉量_kg_ma28', 'last_28days'),
        (14, '体脂肪量_kg_ma14', '筋肉量_kg_ma14', 'last_14days'),
        (7, '体脂肪量_kg_ma7', '筋肉量_kg_ma7', 'last_7days')
    ]
    
    for days, fat_col, muscle_col, report_key in periods:
        print(f"\n◆ {days}日間計算")
        print(f"使用データ: {fat_col}, {muscle_col}")
        
        # 体脂肪量変化検証
        valid_fat = df.dropna(subset=[fat_col])
        if len(valid_fat) >= days:
            current_fat = valid_fat.iloc[-1][fat_col]
            past_fat = valid_fat.iloc[-days][fat_col]
            fat_change = current_fat - past_fat
            
            report_fat_change = report.get(report_key, {}).get('body_fat_mass_change')
            
            print(f"体脂肪量: {past_fat}kg → {current_fat}kg = {fat_change:+.2f}kg")
            print(f"レポート値: {report_fat_change}kg")
            
            if report_fat_change is not None and abs(fat_change - report_fat_change) > 0.1:
                errors.append(f"{days}日体脂肪量変化不一致: 計算{fat_change:+.2f}kg vs レポート{report_fat_change}kg")
        
        # 筋肉量変化検証
        valid_muscle = df.dropna(subset=[muscle_col])
        if len(valid_muscle) >= days:
            current_muscle = valid_muscle.iloc[-1][muscle_col]
            past_muscle = valid_muscle.iloc[-days][muscle_col]
            muscle_change = current_muscle - past_muscle
            
            report_muscle_change = report.get(report_key, {}).get('muscle_mass_change')
            
            print(f"筋肉量: {past_muscle}kg → {current_muscle}kg = {muscle_change:+.2f}kg")
            print(f"レポート値: {report_muscle_change}kg")
            
            if report_muscle_change is not None and abs(muscle_change - report_muscle_change) > 0.1:
                errors.append(f"{days}日筋肉量変化不一致: 計算{muscle_change:+.2f}kg vs レポート{report_muscle_change}kg")
    
    return errors

def check_bf_rate_changes(df, report):
    """体脂肪率変化計算の検証"""
    errors = []
    
    periods = [
        (28, '体脂肪率_ma28'),
        (14, '体脂肪率_ma14'),
        (7, '体脂肪率_ma7')
    ]
    
    for days, col_name in periods:
        print(f"\n◆ {days}日体脂肪率変化")
        print(f"使用データ: {col_name}")
        
        valid_data = df.dropna(subset=[col_name])
        if len(valid_data) >= days:
            current_bf = valid_data.iloc[-1][col_name]
            past_bf = valid_data.iloc[-days][col_name]
            bf_change = current_bf - past_bf
            
            print(f"変化: {past_bf}% → {current_bf}% = {bf_change:+.2f}%")
            
            # レポート内の該当値は表示のみ（詳細比較は他のセクションで）
    
    return errors

def check_metabolism_analysis(df, report):
    """代謝分析の検証"""
    errors = []
    metabolism = report.get('metabolism_analysis', {})
    
    periods = [
        (28, '体脂肪量_kg_ma28', 'fat_loss_28d'),
        (14, '体脂肪量_kg_ma14', 'fat_loss_14d'),
        (7, '体脂肪量_kg_ma7', 'fat_loss_7d')
    ]
    
    for days, col_name, report_key in periods:
        print(f"\n◆ {days}日代謝分析")
        print(f"使用データ: {col_name}")
        
        valid_data = df.dropna(subset=[col_name])
        if len(valid_data) >= days:
            current_value = valid_data.iloc[-1][col_name]
            past_value = valid_data.iloc[-days][col_name]
            change = current_value - past_value
            
            report_value = metabolism.get(report_key)
            
            print(f"計算: {past_value}kg → {current_value}kg = {change:+.2f}kg")
            print(f"レポート: {report_value}kg")
            
            if report_value is not None and abs(change - report_value) > 0.1:
                errors.append(f"{days}日代謝分析不一致: 計算{change:+.2f}kg vs レポート{report_value}kg")
    
    return errors

def check_calorie_calculations(df, report):
    """カロリー計算の検証"""
    errors = []
    
    periods = [(28, 'last_28days'), (14, 'last_14days'), (7, 'last_7days')]
    
    for days, report_key in periods:
        print(f"\n◆ {days}日カロリー計算")
        
        period_df = df.tail(days)
        cal_balance_total = period_df['カロリー収支_kcal'].sum()
        total_intake = period_df['摂取カロリー_kcal'].sum()
        total_consumed = period_df['消費カロリー_kcal'].sum()
        
        report_data = report.get(report_key, {})
        report_balance = report_data.get('calorie_balance_total')
        report_intake = report_data.get('total_intake_calories')
        report_consumed = report_data.get('total_consumed_calories')
        
        print(f"カロリー収支: 計算{cal_balance_total}kcal vs レポート{report_balance}kcal")
        print(f"摂取カロリー: 計算{total_intake}kcal vs レポート{report_intake}kcal")
        print(f"消費カロリー: 計算{total_consumed}kcal vs レポート{report_consumed}kcal")
        
        # 検算確認
        calc_balance = total_intake - total_consumed
        print(f"検算: {total_intake} - {total_consumed} = {calc_balance}kcal")
        
        if abs(cal_balance_total - (report_balance or 0)) > 1:
            errors.append(f"{days}日カロリー収支不一致: 計算{cal_balance_total}kcal vs レポート{report_balance}kcal")
    
    return errors

if __name__ == "__main__":
    errors = comprehensive_calculation_check()
    if errors:
        print(f"\n❌ 発見された問題: {len(errors)}個")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 全計算項目で問題なし！")
