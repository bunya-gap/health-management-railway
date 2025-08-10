"""
Oura API詳細デバッグテスト
APIレスポンスの詳細確認
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from oura_config import OURA_ACCESS_TOKEN, OURA_API_BASE_URL

def detailed_api_test():
    """詳細APIテスト実行"""
    
    # 設定確認
    print("=== Oura API設定確認 ===")
    print(f"Base URL: {OURA_API_BASE_URL}")
    print(f"Token設定: {bool(OURA_ACCESS_TOKEN)}")
    print(f"Token長: {len(OURA_ACCESS_TOKEN) if OURA_ACCESS_TOKEN else 0}")
    print(f"Token先頭4文字: {OURA_ACCESS_TOKEN[:4] if OURA_ACCESS_TOKEN else 'None'}")
    
    if not OURA_ACCESS_TOKEN:
        print("[ERROR] アクセストークンが設定されていません")
        return
    
    # ヘッダー準備
    headers = {
        'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # 1. Personal Info APIテスト（認証確認）
    print("\n=== 1. Personal Info API テスト（認証確認） ===")
    try:
        url = f"{OURA_API_BASE_URL}/usercollection/personal_info"
        response = requests.get(url, headers=headers)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            print("[SUCCESS] 認証成功")
            data = response.json()
            print(f"ユーザーID: {data.get('id', 'N/A')}")
            print(f"年齢: {data.get('age', 'N/A')}")
        else:
            print(f"[ERROR] 認証失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] Personal Info API エラー: {e}")
        return
    
    # 2. Daily Activity API詳細テスト
    print("\n=== 2. Daily Activity API 詳細テスト ===")
    test_date = "2025-08-08"  # 8/8でテスト
    
    try:
        url = f"{OURA_API_BASE_URL}/usercollection/daily_activity"
        params = {'start_date': test_date}
        
        print(f"リクエストURL: {url}")
        print(f"パラメータ: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] データ取得成功")
            print(f"レスポンス構造: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'data' in data and data['data']:
                print(f"データ件数: {len(data['data'])}")
                
                for item in data['data']:
                    day = item.get('day')
                    total_cal = item.get('total_calories')
                    active_cal = item.get('active_calories')
                    rest_cal = item.get('rest_calories')
                    
                    print(f"日付: {day}")
                    print(f"  総消費: {total_cal} kcal")
                    print(f"  活動: {active_cal} kcal")
                    print(f"  安静時: {rest_cal} kcal")
                    
                    if total_cal and total_cal > 2800:
                        print(f"  [MATCH] 2878kcal報告値に近い値発見!")
            else:
                print("[WARNING] dataフィールドが空です")
        else:
            print(f"[ERROR] データ取得失敗: {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Daily Activity API エラー: {e}")
    
    # 3. 期間を拡張してテスト
    print("\n=== 3. 期間拡張テスト（過去30日） ===")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = f"{OURA_API_BASE_URL}/usercollection/daily_activity"
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        print(f"期間: {start_date} - {end_date}")
        
        response = requests.get(url, headers=headers, params=params)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                print(f"30日間データ件数: {len(data['data'])}")
                
                # 最新3件を表示
                recent_data = sorted(data['data'], key=lambda x: x.get('day', ''), reverse=True)[:3]
                
                for item in recent_data:
                    day = item.get('day')
                    total_cal = item.get('total_calories')
                    print(f"  {day}: {total_cal} kcal")
            else:
                print("[WARNING] 30日間でもデータなし")
        else:
            print(f"[ERROR] 30日間データ取得失敗")
            
    except Exception as e:
        print(f"[ERROR] 期間拡張テスト エラー: {e}")

if __name__ == "__main__":
    detailed_api_test()
