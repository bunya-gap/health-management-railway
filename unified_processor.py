"""
体組成管理アプリ 統合データプロセッサー（Oura体表温統合版）
- 基礎代謝: RENPHO優先、なければiPhone積算
- Oura体表温データ自動取得・統合
- 既存ロジックを最小限修正のみ
"""

import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import datetime as dt
import os
import time
import requests
from typing import Dict, List, Optional

def get_oura_temperature_data(start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    Oura Ring APIから体表温データを取得
    
    Args:
        start_date_str: 開始日 (YYYY-MM-DD)
        end_date_str: 終了日 (YYYY-MM-DD)
        
    Returns:
        体表温データのDataFrame
    """
    try:
        from oura_config import is_oura_configured, OURA_ACCESS_TOKEN, OURA_API_BASE_URL
        
        if not is_oura_configured():
            print("Oura設定が未完了です。体表温データをスキップします。")
            print("oura_config.py でOURA_ACCESS_TOKENを設定してください。")
            return pd.DataFrame()
        
        # 🔧 修正: 正しいエンドポイントは Daily Readiness
        url = f"{OURA_API_BASE_URL}/usercollection/daily_readiness"
        headers = {
            'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        params = {
            'start_date': start_date_str,
            'end_date': end_date_str
        }
        
        print(f"Oura APIから体表温データ取得中... (Daily Readiness) ({start_date_str} ~ {end_date_str})")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        readiness_records = data.get('data', [])
        
        # 体表温データを抽出（修正版）
        temperature_records = []
        for record in readiness_records:
            date_str = record.get('day')
            if date_str:
                temp_data = {
                    'date': pd.to_datetime(date_str).date(),
                    'oura_temp_delta': None,  # Daily Readinessには存在しない
                    'oura_temp_deviation': record.get('temperature_deviation'),      # 日次偏差
                    'oura_temp_trend': record.get('temperature_trend_deviation'),   # 3日トレンド
                }
                
                # None値をスキップ
                if any(v is not None for v in [temp_data['oura_temp_deviation'], 
                                              temp_data['oura_temp_trend']]):
                    temperature_records.append(temp_data)
        
        df = pd.DataFrame(temperature_records)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
            print(f"Oura体表温データ: {len(df)} レコード取得 (Daily Readinessより)")
        
        return df
        
    except ImportError:
        print("oura_config.py が見つかりません。体表温データをスキップします。")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Oura API エラー: {e}")
        print("インターネット接続またはAPIトークンを確認してください。")
        return pd.DataFrame()
    except Exception as e:
        print(f"体表温データ取得エラー: {e}")
        return pd.DataFrame()

def wait_for_file_access(filepath, max_wait=30):
    """ファイルが閉じられるまで待機"""
    for i in range(max_wait):
        try:
            with open(filepath, 'w', encoding='utf-8'):
                pass
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except (PermissionError, IOError):
            if i == 0:
                print(f"ファイルが開かれています: {os.path.basename(filepath)}")
                print("ファイルを閉じてください。待機中...")
            time.sleep(1)
    
    print(f"警告: {max_wait}秒待機しましたが、ファイルにアクセスできません")
    return False

def process_health_data():
    """データ処理（基礎代謝修正 + Oura体表温統合）"""
    
    os.chdir(r'C:\Users\terada\Desktop\apps\体組成管理app')
    
    print("=== 体組成管理アプリ 統合データプロセッサー（Oura体表温統合版）===")
    
    # 処理期間の設定
    cutoff_date = dt.date(2025, 6, 1)
    end_date = dt.date.today()
    
    # Oura体表温データを最初に取得
    print("\n=== Oura体表温データ取得 ===")
    oura_temp_df = get_oura_temperature_data(
        cutoff_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # 既存ファイルを上書き
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    files_to_check = [
        os.path.join(reports_dir, '日次データ.csv'),
        os.path.join(reports_dir, '7日移動平均データ.csv'),
        os.path.join(reports_dir, 'インデックスデータ.csv')
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            if not wait_for_file_access(filepath):
                print(f"エラー: {os.path.basename(filepath)} にアクセスできません")
                return
    
    # 全対象指標を定義
    target_metrics = {
        'HKQuantityTypeIdentifierBodyMass': 'weight',
        'HKQuantityTypeIdentifierBodyFatPercentage': 'bf_rate',
        'HKQuantityTypeIdentifierLeanBodyMass': 'muscle',
        'HKQuantityTypeIdentifierDietaryEnergyConsumed': 'intake_cal',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_cal',
        'HKQuantityTypeIdentifierBasalEnergyBurned': 'basal_cal',
        'HKQuantityTypeIdentifierStepCount': 'steps',
        'HKCategoryTypeIdentifierSleepAnalysis': 'sleep',
        'HKQuantityTypeIdentifierDietaryProtein': 'protein',
        'HKQuantityTypeIdentifierDietarySugar': 'carbs',
        'HKQuantityTypeIdentifierDietaryFiber': 'fiber',
        'HKQuantityTypeIdentifierDietaryFatTotal': 'fat',
        'HKQuantityTypeIdentifierBodyTemperature': 'body_temp'
    }
    
    # 基準日付（2025年6月1日）
    print(f"処理対象: {cutoff_date} 以降のデータのみ")
    
    # 日付別にデータを蓄積
    daily_metrics = {}
    
    with zipfile.ZipFile("書き出したデータ.zip") as zf:
        with zf.open("apple_health_export/export.xml") as xml_file:
            print("XMLファイル解析中...")
            
            count = 0
            skipped = 0
            
            parser = ET.iterparse(xml_file, events=('start', 'end'))
            
            for event, elem in parser:
                if event == 'end' and elem.tag == "Record":
                    typ = elem.attrib.get("type")
                    
                    if typ not in target_metrics:
                        elem.clear()
                        continue
                    
                    start_date_str = elem.attrib.get("startDate")
                    if not start_date_str:
                        elem.clear()
                        continue
                    
                    try:
                        date_part = start_date_str.split(' ')[0]
                        year, month, day = map(int, date_part.split('-'))
                        date = dt.date(year, month, day)
                        
                        if date < cutoff_date:
                            skipped += 1
                            elem.clear()
                            continue
                        
                        if typ == 'HKCategoryTypeIdentifierSleepAnalysis':
                            # 睡眠データの処理
                            start_time = pd.to_datetime(elem.attrib['startDate'])
                            end_time = pd.to_datetime(elem.attrib['endDate'])
                            duration_hours = (end_time - start_time).total_seconds() / 3600
                            sleep_stage = elem.attrib.get("value", "")
                            source = elem.attrib.get("sourceName", "Unknown")
                            
                            if 'Oura' in source:
                                if ('AsleepCore' in sleep_stage or 
                                    'AsleepDeep' in sleep_stage or 
                                    'AsleepREM' in sleep_stage):
                                    
                                    sleep_date = date
                                    if start_time.hour >= 18:
                                        sleep_date = date + dt.timedelta(days=1)
                                    
                                    if 0.001 <= duration_hours <= 12.0:
                                        value = duration_hours
                                        metric = target_metrics[typ]
                                        
                                        if sleep_date not in daily_metrics:
                                            daily_metrics[sleep_date] = {}
                                        if metric not in daily_metrics[sleep_date]:
                                            daily_metrics[sleep_date][metric] = []
                                        
                                        daily_metrics[sleep_date][metric].append({
                                            'value': value,
                                            'source': source,
                                            'stage': sleep_stage
                                        })
                                        
                                        count += 1
                        else:
                            # 通常の数値データ処理
                            value = float(elem.attrib.get("value", 0))
                            source = elem.attrib.get("sourceName", "Unknown")
                            metric = target_metrics[typ]
                            
                            if date not in daily_metrics:
                                daily_metrics[date] = {}
                            if metric not in daily_metrics[date]:
                                daily_metrics[date][metric] = []
                            
                            daily_metrics[date][metric].append({
                                'value': value,
                                'source': source
                            })
                            
                            count += 1
                        
                    except (ValueError, IndexError):
                        elem.clear()
                        continue
                    
                    elem.clear()
            
            print(f"XMLファイル処理完了: {count:,} レコード処理, {skipped:,} レコードスキップ")
    
    # 日次データの集計
    print("\n=== 日次データ集計中 ===")
    daily_data = []
    
    for date in sorted(daily_metrics.keys()):
        row = {'date': date}
        
        # 基本指標の集計
        for original_key, metric in target_metrics.items():
            if original_key == 'HKCategoryTypeIdentifierSleepAnalysis':
                continue
            
            if metric in daily_metrics[date]:
                values = [item['value'] for item in daily_metrics[date][metric]]
                
                if metric in ['weight', 'bf_rate', 'muscle', 'body_temp']:
                    row[metric] = values[-1] if values else None
                elif metric == 'basal_cal':
                    # 基礎代謝のシンプルな修正ロジック
                    sources = daily_metrics[date][metric]
                    
                    # RENPHO Healthがあれば優先
                    renpho_values = [item['value'] for item in sources if 'RENPHO' in item['source']]
                    if renpho_values:
                        row[metric] = renpho_values[0]  # RENPHO最初の値のみ
                    else:
                        # RENPHO がなければiPhone積算
                        iphone_values = [item['value'] for item in sources if 'iPhone' in item['source']]
                        row[metric] = sum(iphone_values) if iphone_values else 0
                elif metric in ['steps', 'active_cal']:
                    # 歩数と活動カロリーの重複除去ロジック
                    sources = daily_metrics[date][metric]
                    
                    # データソース優先順位: Oura > Apple Watch > iPhone > その他
                    priority_order = ['Oura', 'Apple Watch', 'iPhone']
                    
                    # 優先順位に基づいて最優先ソースのデータのみを使用
                    selected_values = None
                    selected_source = None
                    
                    for priority_source in priority_order:
                        matching_values = [item['value'] for item in sources if priority_source in item['source']]
                        if matching_values:
                            selected_values = matching_values
                            selected_source = priority_source
                            break
                    
                    # 優先ソースが見つからない場合は、その他のソースから最初の値を使用
                    if selected_values is None:
                        if sources:
                            selected_values = [sources[0]['value']]
                            selected_source = sources[0]['source']
                    
                    if selected_values:
                        # 最優先ソースのデータを積算（同一ソース内での小刻みな計測値の合計）
                        row[metric] = sum(selected_values)
                    else:
                        row[metric] = 0
                else:
                    row[metric] = sum(values) if values else 0
        
        # 睡眠時間の処理
        if 'sleep' in daily_metrics[date]:
            sleep_entries = daily_metrics[date]['sleep']
            total_sleep_hours = sum(entry['value'] for entry in sleep_entries)
            row['sleep'] = total_sleep_hours
        else:
            row['sleep'] = 0
        
        daily_data.append(row)
    
    # DataFrameに変換
    df = pd.DataFrame(daily_data)
    
    if df.empty:
        print("データがありません。")
        return
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # Oura体表温データとマージ
    if not oura_temp_df.empty:
        print(f"\n=== 体表温データ統合 ===")
        df = df.merge(oura_temp_df, on='date', how='left')
        temp_count = df['oura_temp_delta'].notna().sum()
        print(f"体表温データ統合: {temp_count} 日分のデータ")
    else:
        # Oura体表温データがない場合は空の列を追加
        df['oura_temp_delta'] = None
        df['oura_temp_deviation'] = None
        df['oura_temp_trend'] = None
    
    # 指定された順番でカラムを作成
    final_df = pd.DataFrame()
    
    # 日付を先頭に追加
    final_df.insert(0, 'date', df['date'])
    
    # 1-15の指定順序でカラム作成
    final_df['体重_kg'] = df['weight'].round(1)
    final_df['筋肉量_kg'] = df['muscle'].round(1)
    final_df['体脂肪量_kg'] = (df['weight'] * df['bf_rate']).round(1)
    final_df['体脂肪率'] = (df['bf_rate'] * 100).round(1)
    
    # カロリー計算
    total_burned = df['active_cal'] + df['basal_cal']
    final_df['カロリー収支_kcal'] = (df['intake_cal'] - total_burned).round(0)
    final_df['摂取カロリー_kcal'] = df['intake_cal'].round(0)
    final_df['消費カロリー_kcal'] = total_burned.round(0)
    final_df['基礎代謝_kcal'] = df['basal_cal'].round(0)
    final_df['活動カロリー_kcal'] = df['active_cal'].round(0)
    final_df['歩数'] = df['steps'].round(0)
    final_df['睡眠時間_hours'] = df['sleep'].round(2)
    
    # 体表温データを統合（AppleHealthとOuraを統合）
    apple_temp = df.get('body_temp', pd.Series([None] * len(df)))
    oura_temp_delta = df.get('oura_temp_delta', pd.Series([None] * len(df)))
    oura_temp_deviation = df.get('oura_temp_deviation', pd.Series([None] * len(df)))
    oura_temp_trend = df.get('oura_temp_trend', pd.Series([None] * len(df)))
    
    # Apple体表温度がある場合は優先、ない場合はOuraの変化量を表示
    final_df['体表温度_celsius'] = apple_temp.round(1)
    final_df['体表温変化_celsius'] = oura_temp_delta.round(3)  # Oura基準値からの変化
    final_df['体表温偏差_celsius'] = oura_temp_deviation.round(3)  # 日次偏差
    final_df['体表温トレンド_celsius'] = oura_temp_trend.round(3)  # 3日トレンド
    final_df['タンパク質_g'] = df['protein'].round(1)
    final_df['糖質_g'] = df['carbs'].round(1)
    final_df['食物繊維_g'] = df['fiber'].round(1)
    final_df['脂質_g'] = df['fat'].round(1)
    
    # 7日移動平均の計算
    print("\n=== 7日移動平均計算中 ===")
    ma_df = final_df.copy()
    
    numeric_cols = [col for col in final_df.columns if col != 'date']
    for col in numeric_cols:
        ma_df[f'{col}_ma7'] = ma_df[col].rolling(window=7, min_periods=1).mean().round(2)
    
    # ファイル保存
    daily_file = os.path.join(reports_dir, '日次データ.csv')
    final_df.to_csv(daily_file, index=False, encoding='utf-8-sig')
    print(f"日次データ保存: {daily_file}")
    
    ma_file = os.path.join(reports_dir, '7日移動平均データ.csv')
    ma_df.to_csv(ma_file, index=False, encoding='utf-8-sig')
    print(f"7日移動平均データ保存: {ma_file}")
    
    # インデックス処理
    print("\n=== インデックス処理中 ===")
    create_index_data(ma_df)
    
    # 修正結果の確認
    print(f"\n=== 基礎代謝修正結果確認 ===")
    problem_dates = [dt.date(2025, 8, 1), dt.date(2025, 7, 29)]
    for check_date in problem_dates:
        date_data = final_df[final_df['date'] == check_date]
        if not date_data.empty:
            row = date_data.iloc[0]
            print(f"{check_date}: 基礎代謝{row['基礎代謝_kcal']:.0f}kcal")
    
    # 最新データの表示（体表温情報追加）
    print(f"\n=== 最新データ（直近5日分）===")
    latest_data = final_df.tail(5)
    
    for _, row in latest_data.iterrows():
        date_str = row['date'].strftime('%m/%d')
        temp_info = ""
        if pd.notna(row.get('体表温変化_celsius')):
            temp_change = row['体表温変化_celsius']
            temp_info = f" 体表温{temp_change:+.2f}°C"
        
        print(f"{date_str}: 体重{row['体重_kg']}kg 基礎代謝{row['基礎代謝_kcal']:.0f}kcal "
              f"活動{row['活動カロリー_kcal']:.0f}kcal 睡眠{row['睡眠時間_hours']}h{temp_info}")
    
    print(f"\n修正完了！基礎代謝: RENPHO優先、なければiPhone積算")
    if not oura_temp_df.empty:
        print(f"Oura体表温データ: {len(oura_temp_df)}日分を統合")

def create_index_data(ma_df):
    """インデックス処理（体脂肪量・糖質・体表温追加版）"""
    
    reports_dir = 'reports'
    
    target_columns = {
        '体重_kg_ma7': '体重インデックス',
        '筋肉量_kg_ma7': '筋肉量インデックス', 
        '体脂肪量_kg_ma7': '体脂肪量インデックス',
        'カロリー収支_kcal_ma7': 'カロリー収支インデックス',
        '睡眠時間_hours_ma7': '睡眠時間インデックス',
        '糖質_g_ma7': '糖質インデックス',
        '体表温変化_celsius_ma7': '体表温変化インデックス'
    }
    
    index_df = pd.DataFrame()
    index_df['date'] = ma_df['date']
    
    for original_col, index_col in target_columns.items():
        if original_col not in ma_df.columns:
            continue
        
        valid_data = ma_df[original_col].dropna()
        if len(valid_data) == 0:
            index_df[index_col] = 100
            continue
        
        if original_col == 'カロリー収支_kcal_ma7':
            mean_val = valid_data.mean()
            std_val = valid_data.std()
            if std_val > 0:
                z_scores = (ma_df[original_col] - mean_val) / std_val
                index_values = (z_scores * 5 + 100).round(1).clip(90, 110)
            else:
                index_values = pd.Series([100] * len(ma_df))
                
        elif original_col == '睡眠時間_hours_ma7':
            sleep_data = ma_df[original_col].copy()
            sleep_data = sleep_data.replace(0.0, 7.0).fillna(7.0)
            index_values = (sleep_data * 10 + 30).round(1).clip(90, 110)
            
        elif original_col == '糖質_g_ma7':
            # 糖質: 50gを100として設定
            base_value = 50.0
            index_values = (ma_df[original_col] / base_value * 100).round(1)
            # 糖質は健康的な範囲として30-110gを60-120にマッピング
            index_values = index_values.clip(60, 120)
            
        elif original_col == '体表温変化_celsius_ma7':
            # 体表温変化: 0°Cを100として、±0.5°Cごとに±10ポイント
            temp_change = ma_df[original_col].fillna(0)
            index_values = (100 + temp_change * 20).round(1).clip(80, 120)
            
        else:
            first_value = valid_data.iloc[0]
            base_index = (ma_df[original_col] / first_value * 100)
            min_val = base_index.min()
            max_val = base_index.max()
            
            if max_val - min_val > 20:
                median_val = base_index.median()
                index_values = ((base_index - median_val) * 0.5 + 100).round(1).clip(90, 110)
            else:
                index_values = base_index.round(1)
        
        index_df[index_col] = index_values
    
    index_file = os.path.join(reports_dir, 'インデックスデータ.csv')
    index_df.to_csv(index_file, index=False, encoding='utf-8-sig')
    print(f"インデックスデータ保存: {index_file}")

if __name__ == "__main__":
    process_health_data()
