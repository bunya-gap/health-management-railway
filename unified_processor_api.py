"""
体組成管理アプリ 統合データプロセッサー（REST API版）
- Health Auto Export REST API からデータ取得
- Oura体表温データ統合
- 既存出力フォーマット維持
"""

import json
import pandas as pd
import datetime as dt
import os
import time
import requests
from typing import Dict, List, Optional
import glob
from pathlib import Path

def load_health_api_data(data_dir: str = "health_api_data") -> pd.DataFrame:
    """
    Health Auto Export REST APIで受信したデータを読み込み
    """
    data_dir_path = Path(data_dir)
    
    if not data_dir_path.exists():
        print(f"❌ データディレクトリが見つかりません: {data_dir}")
        return pd.DataFrame()
    
    # 最新のJSONファイルを取得
    json_files = list(data_dir_path.glob("health_data_*.json"))
    
    if not json_files:
        print("❌ Health APIデータファイルが見つかりません")
        return pd.DataFrame()
    
    # 最新ファイルを選択
    latest_file = max(json_files, key=lambda x: x.stat().st_ctime)
    print(f"📂 最新データファイル: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        api_data = json.load(f)
    
    return process_health_api_data(api_data)

def process_health_api_data(api_data: Dict) -> pd.DataFrame:
    """
    Health Auto Export APIデータを処理して統一フォーマットに変換
    """
    metrics = api_data.get('data', {}).get('metrics', [])
    
    if not metrics:
        print("❌ メトリクスデータが見つかりません")
        return pd.DataFrame()
    
    print(f"📊 処理対象メトリクス数: {len(metrics)}")
    
    # メトリクス名のマッピング（Health Auto Export → 体組成アプリ形式）
    metric_mapping = {
        'body_mass': '体重_kg',
        'body_fat_percentage': '体脂肪率',
        'lean_body_mass': '筋肉量_kg',
        'dietary_energy_consumed': '摂取カロリー_kcal',
        'active_energy_burned': '活動カロリー_kcal',
        'basal_energy_burned': '基礎代謝_kcal',
        'step_count': '歩数',
        'sleep_analysis': '睡眠時間_hours',
        'dietary_protein': 'タンパク質_g',
        'dietary_carbohydrates': '糖質_g',
        'dietary_fiber': '食物繊維_g',
        'dietary_fat_total': '脂質_g'
    }
    
    # 日付別データ辞書
    daily_data = {}
    
    for metric in metrics:
        name = metric.get('name', '').lower().replace(' ', '_')
        data_points = metric.get('data', [])
        
        # マッピングにない場合はスキップ
        if name not in metric_mapping:
            continue
        
        column_name = metric_mapping[name]
        
        for point in data_points:
            date_str = point.get('date', '')
            if not date_str:
                continue
            
            # 日付解析
            try:
                date_obj = pd.to_datetime(date_str).date()
            except:
                continue
            
            # 日付別データ初期化
            if date_obj not in daily_data:
                daily_data[date_obj] = {'date': date_obj}
            
            # 値の処理
            if name == 'sleep_analysis':
                # 睡眠時間は特別処理（時間単位に変換）
                asleep_minutes = point.get('asleep', 0)
                daily_data[date_obj][column_name] = asleep_minutes / 60.0 if asleep_minutes else 0
            else:
                qty = point.get('qty', 0)
                daily_data[date_obj][column_name] = qty
    
    # DataFrameに変換
    df = pd.DataFrame(list(daily_data.values()))
    
    if df.empty:
        print("❌ 処理可能なデータが見つかりませんでした")
        return df
    
    # 日付順でソート
    df = df.sort_values('date').reset_index(drop=True)
    
    # 計算フィールドの追加
    df = add_calculated_fields(df)
    
    print(f"✅ データ処理完了: {len(df)} 日分のデータ")
    return df

def add_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算フィールドを追加（体脂肪量、カロリー収支など）
    """
    # 体脂肪量の計算
    if '体重_kg' in df.columns and '体脂肪率' in df.columns:
        df['体脂肪量_kg'] = df['体重_kg'] * (df['体脂肪率'] / 100)
    
    # 消費カロリーの計算
    basal_col = '基礎代謝_kcal'
    active_col = '活動カロリー_kcal'
    
    if basal_col in df.columns and active_col in df.columns:
        df['消費カロリー_kcal'] = df[basal_col].fillna(0) + df[active_col].fillna(0)
    
    # カロリー収支の計算
    if '摂取カロリー_kcal' in df.columns and '消費カロリー_kcal' in df.columns:
        df['カロリー収支_kcal'] = df['摂取カロリー_kcal'].fillna(0) - df['消費カロリー_kcal'].fillna(0)
    
    return df

def get_oura_temperature_data(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    Oura Ring APIから体表温データを取得（既存コードを維持）
    """
    try:
        from oura_config import is_oura_configured, OURA_ACCESS_TOKEN, OURA_API_BASE_URL
        
        if not is_oura_configured():
            print("Oura設定が未完了です。体表温データをスキップします。")
            return pd.DataFrame()
        
        url = f"{OURA_API_BASE_URL}/usercollection/daily_readiness"
        headers = {
            'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        params = {
            'start_date': start_date_str,
            'end_date': end_date_str
        }
        
        print(f"Oura APIから体表温データ取得中... ({start_date_str} ~ {end_date_str})")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        readiness_records = data.get('data', [])
        
        temperature_records = []
        for record in readiness_records:
            date_str = record.get('day')
            if date_str:
                temp_data = {
                    'date': pd.to_datetime(date_str).date(),
                    'oura_temp_deviation': record.get('temperature_deviation'),
                    'oura_temp_trend': record.get('temperature_trend_deviation'),
                }
                temperature_records.append(temp_data)
        
        return pd.DataFrame(temperature_records) if temperature_records else pd.DataFrame()
    
    except Exception as e:
        print(f"❌ Oura体表温データ取得エラー: {e}")
        return pd.DataFrame()

def main():
    """
    メイン処理（REST API版）
    """
    print("🚀 体組成管理アプリ 統合データプロセッサー（REST API版）")
    print("=" * 60)
    
    # 設定
    target_start_date = dt.date(2025, 6, 1)
    data_dir = os.path.join(os.path.dirname(__file__), 'health_api_data')
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    
    os.makedirs(reports_dir, exist_ok=True)
    
    # Health Auto Export APIデータを読み込み
    print("📂 Health Auto Export APIデータを読み込み中...")
    health_df = load_health_api_data(data_dir)
    
    if health_df.empty:
        print("❌ データが見つかりません。以下を確認してください:")
        print("   1. Health Auto Export REST APIサーバーが起動しているか")
        print("   2. iPhoneアプリからデータが送信されているか")
        print("   3. health_api_data/ フォルダにJSONファイルがあるか")
        return
    
    # 日付フィルタリング
    health_df = health_df[health_df['date'] >= target_start_date].reset_index(drop=True)
    
    if health_df.empty:
        print(f"❌ {target_start_date}以降のデータが見つかりません")
        return
    
    print(f"✅ {len(health_df)} 日分のデータを読み込み")
    
    # Oura体表温データ取得
    start_date_str = health_df['date'].min().strftime('%Y-%m-%d')
    end_date_str = health_df['date'].max().strftime('%Y-%m-%d')
    
    oura_df = get_oura_temperature_data(start_date_str, end_date_str)
    
    if not oura_df.empty:
        health_df = pd.merge(health_df, oura_df, on='date', how='left')
        print(f"✅ Oura体表温データを統合")
    
    # 出力ファイル
    daily_file = os.path.join(reports_dir, '日次データ.csv')
    ma7_file = os.path.join(reports_dir, '7日移動平均データ.csv')
    index_file = os.path.join(reports_dir, 'インデックスデータ.csv')
    
    # 日次データ出力
    health_df.to_csv(daily_file, index=False, encoding='utf-8-sig')
    print(f"💾 日次データを保存: {daily_file}")
    
    # 7日移動平均計算・出力
    ma7_df = health_df.copy()
    numeric_columns = health_df.select_dtypes(include=['float64', 'int64']).columns
    
    for col in numeric_columns:
        if col != 'date':
            ma7_df[f'{col}_ma7'] = health_df[col].rolling(window=7, min_periods=1).mean()
    
    ma7_df.to_csv(ma7_file, index=False, encoding='utf-8-sig')
    print(f"💾 7日移動平均データを保存: {ma7_file}")
    
    # インデックスデータ計算・出力
    index_df = calculate_index_data(health_df)
    index_df.to_csv(index_file, index=False, encoding='utf-8-sig')
    print(f"💾 インデックスデータを保存: {index_file}")
    
    print("=" * 60)
    print("🎉 処理完了！")
    print(f"📊 処理期間: {start_date_str} ～ {end_date_str}")
    print(f"📁 出力先: {reports_dir}")

def calculate_index_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    インデックスデータを計算（既存ロジックを維持）
    """
    index_data = []
    
    for _, row in df.iterrows():
        index_row = {'date': row['date']}
        
        # 体重インデックス（初回値を100として相対計算）
        if '体重_kg' in df.columns:
            first_weight = df['体重_kg'].dropna().iloc[0] if not df['体重_kg'].dropna().empty else None
            if first_weight and pd.notna(row['体重_kg']):
                index_row['体重インデックス'] = (row['体重_kg'] / first_weight) * 100
        
        # 筋肉量インデックス
        if '筋肉量_kg' in df.columns:
            first_muscle = df['筋肉量_kg'].dropna().iloc[0] if not df['筋肉量_kg'].dropna().empty else None
            if first_muscle and pd.notna(row['筋肉量_kg']):
                index_row['筋肉量インデックス'] = (row['筋肉量_kg'] / first_muscle) * 100
        
        # 体脂肪量インデックス
        if '体脂肪量_kg' in df.columns:
            first_fat = df['体脂肪量_kg'].dropna().iloc[0] if not df['体脂肪量_kg'].dropna().empty else None
            if first_fat and pd.notna(row['体脂肪量_kg']):
                index_row['体脂肪量インデックス'] = (row['体脂肪量_kg'] / first_fat) * 100
        
        # 睡眠時間インデックス（時間×10+30）
        if '睡眠時間_hours' in df.columns and pd.notna(row['睡眠時間_hours']):
            index_row['睡眠時間インデックス'] = row['睡眠時間_hours'] * 10 + 30
        
        # 糖質インデックス（50g基準の相対計算）
        if '糖質_g' in df.columns and pd.notna(row['糖質_g']):
            index_row['糖質インデックス'] = min(max((row['糖質_g'] / 50) * 60, 60), 120)
        
        index_data.append(index_row)
    
    return pd.DataFrame(index_data)

if __name__ == "__main__":
    main()
