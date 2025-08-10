"""
Oura Ring API v2クライアント - 総消費カロリー取得
Daily Activity Summary エンドポイントから総消費カロリーデータを取得
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import sys

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from oura_config import OURA_ACCESS_TOKEN, OURA_API_BASE_URL, OURA_ENABLED


class OuraAPIClient:
    """Oura Ring API v2クライアント"""
    
    def __init__(self):
        self.access_token = OURA_ACCESS_TOKEN
        self.base_url = OURA_API_BASE_URL
        self.enabled = OURA_ENABLED
        
        if not self.enabled:
            print("[INFO] Oura API取得が無効化されています")
            return
            
        if not self.access_token or len(self.access_token) < 10:
            print("[ERROR] Oura APIアクセストークンが設定されていません")
            self.enabled = False
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Oura APIリクエスト実行"""
        if not self.enabled:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Oura API リクエストエラー: {e}")
            return None
    
    def get_daily_activity(self, start_date: str, end_date: str = None) -> Optional[List[Dict]]:
        """
        Daily Activity Summary取得
        
        Args:
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD), Noneの場合は開始日のみ
            
        Returns:
            Daily Activity データのリスト
        """
        if not self.enabled:
            return None
            
        params = {'start_date': start_date}
        if end_date:
            params['end_date'] = end_date
            
        print(f"[INFO] Oura API Daily Activity取得: {start_date}")
        result = self._make_request('usercollection/daily_activity', params)
        
        if result and 'data' in result:
            return result['data']
        else:
            print(f"[WARNING] Oura API Daily Activity データが取得できませんでした: {start_date}")
            return []
    
    def get_total_calories_for_date(self, date: str) -> Optional[Dict[str, float]]:
        """
        指定日の総消費カロリーデータを取得
        
        Args:
            date: 対象日 (YYYY-MM-DD)
            
        Returns:
            カロリーデータ辞書 {
                'total_calories': 総消費カロリー,
                'active_calories': 活動カロリー, 
                'rest_calories': 安静時カロリー
            }
        """
        daily_data = self.get_daily_activity(date)
        
        if not daily_data:
            return None
            
        # 指定日のデータを検索
        for activity in daily_data:
            if activity.get('day') == date:
                calories_data = {
                    'total_calories': activity.get('total_calories'),
                    'active_calories': activity.get('active_calories'),
                    'rest_calories': activity.get('rest_calories'),
                    'date': date
                }
                
                print(f"[SUCCESS] Oura総消費カロリー取得: {date}")
                print(f"  - 総消費: {calories_data['total_calories']} kcal")
                print(f"  - 活動: {calories_data['active_calories']} kcal") 
                print(f"  - 安静時: {calories_data['rest_calories']} kcal")
                
                return calories_data
        
        print(f"[WARNING] {date}のOura Daily Activityデータが見つかりません")
        return None
    
    def get_calories_for_date_range(self, start_date: str, end_date: str) -> Dict[str, Dict[str, float]]:
        """
        期間内の全日付の総消費カロリーデータを取得
        
        Args:
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD)
            
        Returns:
            日付をキーとした辞書 {
                'YYYY-MM-DD': {
                    'total_calories': 総消費カロリー,
                    'active_calories': 活動カロリー,
                    'rest_calories': 安静時カロリー
                }
            }
        """
        daily_data = self.get_daily_activity(start_date, end_date)
        
        if not daily_data:
            return {}
            
        calories_by_date = {}
        
        for activity in daily_data:
            date = activity.get('day')
            if date:
                calories_by_date[date] = {
                    'total_calories': activity.get('total_calories'),
                    'active_calories': activity.get('active_calories'), 
                    'rest_calories': activity.get('rest_calories')
                }
        
        print(f"[SUCCESS] Oura総消費カロリー期間取得: {start_date} - {end_date}")
        print(f"  - 取得日数: {len(calories_by_date)}日")
        
        return calories_by_date


def test_oura_api():
    """Oura API総消費カロリー取得テスト"""
    client = OuraAPIClient()
    
    if not client.enabled:
        print("[ERROR] Oura API設定が無効です")
        return
    
    # 8/9のデータをテスト取得
    test_date = "2025-08-09"
    calories_data = client.get_total_calories_for_date(test_date)
    
    if calories_data:
        print(f"\n=== {test_date} Oura総消費カロリーテスト結果 ===")
        print(f"総消費カロリー: {calories_data['total_calories']} kcal")
        print(f"活動カロリー: {calories_data['active_calories']} kcal")
        print(f"安静時カロリー: {calories_data['rest_calories']} kcal")
        
        # ユーザー報告値との比較
        print(f"\n=== ユーザー報告値との比較 ===")
        print(f"総消費: {calories_data['total_calories']} vs 2878 (報告値)")
        print(f"活動: {calories_data['active_calories']} vs 910 (報告値)")
        
    else:
        print(f"[ERROR] {test_date}のOuraデータ取得に失敗しました")


if __name__ == "__main__":
    test_oura_api()
