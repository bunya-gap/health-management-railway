"""
7日移動平均データCSV直接修正
Oura統合データとカロリー収支を正しく更新
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Oura API設定
OURA_ACCESS_TOKEN = "JQI3Z4TCC57DMDIKIPH77IFEJJS255Z3"
OURA_API_BASE_URL = "https://api.ouraring.com/v2"

def fix_moving_average_csv():
    """7日移動平均データCSVを直接修正"""
    
    print("=== 7日移動平均データCSV直接修正開始 ===")
    
    # パス設定
    reports_dir = Path("C:/Users/terada/Desktop/apps/体組成管理app/reports")
    ma_csv_path = reports_dir / "7日移動平均データ.csv"
    
    if not ma_csv_path.exists():
        print(f"[ERROR] 7日移動平均データCSVが見つかりません: {ma_csv_path}")
        return
    
    # バックアップ作成
    backup_path = str(ma_csv_path).replace('.csv', f'_backup_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    shutil.copy2(str(ma_csv_path), backup_path)
    print(f"[BACKUP] 7日移動平均バックアップ: {backup_path}")
    
    # 過去30日分のOuraデータ取得
    def get_oura_data_30days():
        headers = {
            'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            url = f"{OURA_API_BASE_URL}/usercollection/daily_activity"
            params = {'start_date': start_date, 'end_date': end_date}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            
            if 'data' in data and data['data']:
                oura_data = {}
                for activity in data['data']:
                    date = activity.get('day')
                    if date:
                        total_cal = activity.get('total_calories')
                        active_cal = activity.get('active_calories')
                        estimated_basal = total_cal - active_cal if total_cal and active_cal else None
                        
                        oura_data[date] = {
                            'total_calories': total_cal,
                            'active_calories': active_cal,
                            'estimated_basal': estimated_basal
                        }
                
                return oura_data
            
            return {}
            
        except Exception as e:
            print(f"[ERROR] Oura API取得エラー: {e}")
            return {}
    
    # Ouraデータ取得
    print(f"[INFO] Oura APIデータ取得中...")
    oura_data = get_oura_data_30days()
    print(f"[INFO] Oura API取得完了: {len(oura_data)}日分")
    
    # CSV読み込み
    df = pd.read_csv(str(ma_csv_path))
    print(f"[INFO] 7日移動平均CSV読み込み: {len(df)}行")
    
    # 新しい列を準備
    if 'oura_total_calories' not in df.columns:
        df['oura_total_calories'] = None
        df['oura_estimated_basal'] = None
        df['previous_total_calories'] = df['消費カロリー_kcal'].copy()
        df['previous_calorie_balance'] = df['カロリー収支_kcal'].copy()
        df['calculation_method'] = 'RENPHO+Oura'
    
    updated_count = 0
    calorie_balance_fixed_count = 0
    
    # 全行を処理
    for index, row in df.iterrows():
        date_str = str(row['date'])
        
        if pd.isna(date_str) or date_str == 'nan':
            continue
        
        # Ouraデータが利用可能な場合
        if date_str in oura_data:
            oura_info = oura_data[date_str]
            
            # Oura統合データを記録
            df.at[index, 'oura_total_calories'] = oura_info['total_calories']
            df.at[index, 'oura_estimated_basal'] = oura_info['estimated_basal']
            df.at[index, 'calculation_method'] = 'Oura_API_v2'
            
            # 既存列をOura値に更新
            df.at[index, '消費カロリー_kcal'] = oura_info['total_calories']
            df.at[index, '基礎代謝_kcal'] = oura_info['estimated_basal']
            df.at[index, '活動カロリー_kcal'] = oura_info['active_calories']
            
            updated_count += 1
            print(f"[UPDATE] {date_str}: {oura_info['total_calories']} kcal")
        
        # カロリー収支を再計算（全行対象）
        intake_cal = row['摂取カロリー_kcal']
        consumed_cal = df.at[index, '消費カロリー_kcal']
        
        if not pd.isna(intake_cal) and not pd.isna(consumed_cal):
            new_balance = intake_cal - consumed_cal
            df.at[index, 'カロリー収支_kcal'] = new_balance
            calorie_balance_fixed_count += 1
    
    # CSV保存
    df.to_csv(str(ma_csv_path), index=False)
    
    print(f"\n=== 7日移動平均CSV修正完了 ===")
    print(f"Oura更新日数: {updated_count}日")
    print(f"カロリー収支修正行数: {calorie_balance_fixed_count}行")
    print(f"バックアップ: {backup_path}")
    
    # 修正効果の確認
    if updated_count > 0:
        latest_updated = [date for date in oura_data.keys() if date in df['date'].astype(str).values]
        if latest_updated:
            latest_date = max(latest_updated)
            latest_row = df[df['date'] == latest_date].iloc[0]
            
            print(f"\n=== 修正効果確認（{latest_date}） ===")
            print(f"消費カロリー: {latest_row['消費カロリー_kcal']} kcal")
            print(f"カロリー収支: {latest_row['カロリー収支_kcal']} kcal")
            print(f"計算方式: {latest_row['calculation_method']}")

if __name__ == "__main__":
    fix_moving_average_csv()
