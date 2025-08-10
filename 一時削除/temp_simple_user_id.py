"""
LINE Bot User ID 取得 - シンプル版（Unicode文字なし）
"""

import sys
from pathlib import Path
import requests

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from automation.config import config

def get_followers():
    """友達リストからUser ID取得"""
    print("=== User ID 取得中 ===")
    
    headers = {
        'Authorization': f'Bearer {config.LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 友達リスト取得
        response = requests.get(
            'https://api.line.me/v2/bot/followers/ids',
            headers=headers
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user_ids = data.get('userIds', [])
            
            print(f"友達数: {len(user_ids)}")
            
            if user_ids:
                user_id = user_ids[0]
                print(f"User ID: {user_id}")
                
                # ファイルに保存
                with open('temp_user_id.txt', 'w', encoding='utf-8') as f:
                    f.write(f'LINE_USER_ID = "{user_id}"\n')
                
                # テスト送信
                test_data = {
                    'to': user_id,
                    'messages': [{'type': 'text', 'text': 'User ID取得成功！Phase 2システム準備完了です！'}]
                }
                
                test_response = requests.post(
                    'https://api.line.me/v2/bot/message/push',
                    headers=headers, 
                    json=test_data
                )
                
                print(f"テストメッセージ送信: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    print("SUCCESS: User ID取得・設定・テスト完了！")
                    return user_id
                else:
                    print(f"テスト送信失敗: {test_response.text}")
            else:
                print("友達がまだ追加されていません")
                
        elif response.status_code == 403:
            print("権限エラー: 友達リストAPIが無効化されています")
            print("代替方法: 手動User ID入力")
            
            user_input = input("User IDを入力してください（Uで始まる33文字）: ").strip()
            
            if user_input and user_input.startswith('U') and len(user_input) == 33:
                # ファイルに保存
                with open('temp_user_id.txt', 'w', encoding='utf-8') as f:
                    f.write(f'LINE_USER_ID = "{user_input}"\n')
                
                print(f"User ID保存完了: {user_input}")
                return user_input
            else:
                print("無効なUser ID形式")
                
        else:
            print(f"API エラー: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"エラー: {e}")
        
    return None

if __name__ == "__main__":
    result = get_followers()
    
    if result:
        print("\n=== 成功 ===")
        print(f"User ID: {result}")
        print("次のステップ: python automation\\auto_processor.py --test-line")
    else:
        print("\n=== 失敗 ===")
        print("手動設定が必要です")
