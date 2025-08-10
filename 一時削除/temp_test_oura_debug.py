"""
Oura API総消費カロリー取得デバッグテスト
日付を調整してテスト実行
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from temp_oura_api_client import OuraAPIClient

def debug_test():
    """デバッグテスト実行"""
    client = OuraAPIClient()
    
    if not client.enabled:
        print("[ERROR] Oura API設定が無効です")
        return
    
    # 現在日付から過去7日間の日付をテスト
    today = datetime.now()
    test_dates = []
    
    for i in range(7):
        test_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        test_dates.append(test_date)
    
    print(f"[INFO] テスト対象日付: {test_dates}")
    
    # 各日付でテスト
    for test_date in test_dates:
        print(f"\n=== {test_date} テスト実行 ===")
        calories_data = client.get_total_calories_for_date(test_date)
        
        if calories_data:
            print(f"[SUCCESS] 成功: 総消費 {calories_data['total_calories']} kcal")
            
            # 2878kcalに近い値があるかチェック
            if calories_data['total_calories'] and calories_data['total_calories'] > 2800:
                print(f"[MATCH] 2878kcal報告値に近い値発見: {calories_data['total_calories']} kcal")
                print(f"   活動カロリー: {calories_data['active_calories']} kcal")
                print(f"   安静時カロリー: {calories_data['rest_calories']} kcal")
            
            break  # 成功したら停止
        else:
            print(f"[FAILED] 失敗: {test_date}")
    
    # より詳細なAPI情報確認
    print(f"\n=== API設定確認 ===")
    print(f"API URL: {client.base_url}")
    print(f"Token設定: {'OK' if client.access_token else 'NG'}")
    print(f"Token長: {len(client.access_token) if client.access_token else 0}")

if __name__ == "__main__":
    debug_test()
