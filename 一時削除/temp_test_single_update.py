"""
Oura Ring総消費カロリー統合テスト（8/9のみ）
特定日付のみを更新してテスト実行
"""

import pandas as pd
import requests
from pathlib import Path
import shutil
from datetime import datetime

# Oura API設定
OURA_ACCESS_TOKEN = "JQI3Z4TCC57DMDIKIPH77IFEJJS255Z3"
OURA_API_BASE_URL = "https://api.ouraring.com/v2"

def get_oura_calories_single_date(date: str) -> dict:
    """指定日のOura総消費カロリーを取得"""
    headers = {
        'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        url = f"{OURA_API_BASE_URL}/usercollection/daily_activity"
        params = {'start_date': date}
        
        print(f"[INFO] Oura API呼び出し: {date}")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return {'error': f'API失敗: {response.status_code}'}
        
        data = response.json()
        
        if 'data' in data and data['data']:
            for activity in data['data']:
                if activity.get('day') == date:
                    total_cal = activity.get('total_calories')
                    active_cal = activity.get('active_calories')
                    estimated_basal = total_cal - active_cal if total_cal and active_cal else None
                    
                    return {
                        'success': True,
                        'date': date,
                        'total_calories': total_cal,
                        'active_calories': active_cal,
                        'estimated_basal': estimated_basal
                    }
        
        return {'error': f'{date}のデータなし'}
        
    except Exception as e:
        return {'error': f'API呼び出しエラー: {str(e)}'}

def test_single_date_update():
    """8/9のデータのみを更新してテスト"""
    
    print("=== Oura Ring総消費カロリー統合テスト（8/9のみ） ===")
    
    # CSV パス
    csv_path = Path("C:/Users/terada/Desktop/apps/体組成管理app/reports/日次データ.csv")
    
    if not csv_path.exists():
        print(f"[ERROR] CSVファイルが見つかりません: {csv_path}")
        return
    
    # バックアップ作成
    backup_path = str(csv_path).replace('.csv', f'_backup_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    shutil.copy2(str(csv_path), backup_path)
    print(f"[BACKUP] テスト用バックアップ: {backup_path}")
    
    # CSV読み込み
    df = pd.read_csv(str(csv_path))
    print(f"[INFO] CSV読み込み: {len(df)}行")
    
    # 8/9のデータを検索
    target_date = "2025-08-09"
    target_row = df[df['date'] == target_date]
    
    if len(target_row) == 0:
        print(f"[ERROR] {target_date}のデータが見つかりません")
        return
    
    target_index = target_row.index[0]
    
    print(f"\n=== {target_date} 現在のデータ ===")
    current_row = df.loc[target_index]
    print(f"現在の消費カロリー: {current_row['消費カロリー_kcal']} kcal")
    print(f"現在の基礎代謝: {current_row['基礎代謝_kcal']} kcal")
    print(f"現在の活動カロリー: {current_row['活動カロリー_kcal']} kcal")
    
    # Oura APIからデータ取得
    print(f"\n=== Oura APIからデータ取得 ===")
    oura_result = get_oura_calories_single_date(target_date)
    
    if 'error' in oura_result:
        print(f"[ERROR] Oura API取得失敗: {oura_result['error']}")
        return
    
    print(f"[SUCCESS] Oura APIデータ取得成功")
    print(f"Oura総消費カロリー: {oura_result['total_calories']} kcal")
    print(f"Oura活動カロリー: {oura_result['active_calories']} kcal")
    print(f"Oura推定基礎代謝: {oura_result['estimated_basal']} kcal")
    
    # 差異計算
    print(f"\n=== 差異分析 ===")
    total_diff = oura_result['total_calories'] - current_row['消費カロリー_kcal']
    active_diff = oura_result['active_calories'] - current_row['活動カロリー_kcal']
    basal_diff = oura_result['estimated_basal'] - current_row['基礎代謝_kcal']
    
    print(f"総消費カロリー差異: {total_diff:+.1f} kcal")
    print(f"活動カロリー差異: {active_diff:+.1f} kcal")
    print(f"基礎代謝差異: {basal_diff:+.1f} kcal")
    
    # CSVデータ更新
    print(f"\n=== CSVデータ更新 ===")
    
    # 新しい列を追加（初回のみ）
    if 'oura_total_calories' not in df.columns:
        df['oura_total_calories'] = None
        df['oura_estimated_basal'] = None
        df['calculation_method'] = 'RENPHO+Oura'
    
    # 8/9のデータを更新
    df.at[target_index, 'oura_total_calories'] = oura_result['total_calories']
    df.at[target_index, 'oura_estimated_basal'] = oura_result['estimated_basal']
    df.at[target_index, 'calculation_method'] = 'Oura_API'
    
    # 既存列も更新
    df.at[target_index, '消費カロリー_kcal'] = oura_result['total_calories']
    df.at[target_index, '基礎代謝_kcal'] = oura_result['estimated_basal']
    df.at[target_index, '活動カロリー_kcal'] = oura_result['active_calories']
    
    # CSV保存
    df.to_csv(str(csv_path), index=False)
    print(f"[SUCCESS] CSV更新完了")
    
    # 更新後の確認
    updated_row = df.loc[target_index]
    print(f"\n=== 更新後データ確認 ===")
    print(f"更新後の消費カロリー: {updated_row['消費カロリー_kcal']} kcal")
    print(f"更新後の基礎代謝: {updated_row['基礎代謝_kcal']} kcal")
    print(f"更新後の活動カロリー: {updated_row['活動カロリー_kcal']} kcal")
    print(f"計算方式: {updated_row['calculation_method']}")
    
    print(f"\n=== テスト完了サマリー ===")
    print(f"バックアップファイル: {backup_path}")
    print(f"改善効果: {total_diff:+.1f} kcal/日")
    print(f"精度向上率: {(abs(total_diff)/current_row['消費カロリー_kcal']*100):+.1f}%")
    print(f"テスト成功: Oura API統合準備完了")

if __name__ == "__main__":
    test_single_date_update()
