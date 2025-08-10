"""
LINE Bot User ID取得ヘルパー
友達になったユーザーのUser IDを取得する一時的なスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from automation.config import config
import requests

def get_bot_info():
    """Bot情報とUser ID取得のヒントを表示"""
    print("=== LINE Bot 設定確認 ===")
    
    if not config.LINE_BOT_CHANNEL_ACCESS_TOKEN:
        print("[ERROR] Channel Access Tokenが設定されていません")
        print("1. LINE Official Account Manager → 設定 → Messaging API")
        print("2. Channel access token を発行")
        print("3. automation/config.py でトークンを設定")
        return False
        
    print(f"Channel Access Token: {'設定済み' if config.LINE_BOT_CHANNEL_ACCESS_TOKEN else '未設定'}")
    
    # Bot情報取得
    headers = {
        'Authorization': f'Bearer {config.LINE_BOT_CHANNEL_ACCESS_TOKEN}'
    }
    
    try:
        # Bot情報取得
        response = requests.get('https://api.line.me/v2/bot/info', headers=headers)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"Bot名: {bot_info.get('displayName', '不明')}")
            print(f"Bot ID: {bot_info.get('userId', '不明')}")
            print(f"基本ID: {bot_info.get('basicId', '不明')}")
            print("\n✅ Channel Access Token は正常に動作しています！")
            
            print("\n🔍 User ID取得方法:")
            print("1. QRコードでBotと友達になる")
            print("2. Botに任意のメッセージを送信")
            print("3. 以下のいずれかでUser IDを取得:")
            print("   - Webhook設定（推奨）")
            print("   - LINE Developers Console のログ")
            print("   - Botにメッセージ送信後、エラーログからUser IDを特定")
            
            return True
            
        else:
            print(f"[ERROR] Bot情報取得失敗: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 接続エラー: {e}")
        return False

def test_user_id_if_set():
    """User IDが設定されている場合のテスト"""
    if not config.LINE_USER_ID:
        print("\n[INFO] User IDが未設定のため、User IDテストをスキップ")
        print("設定完了後に再実行してください")
        return False
        
    print(f"\n=== User ID テスト ===")
    print(f"User ID: {config.LINE_USER_ID}")
    
    headers = {
        'Authorization': f'Bearer {config.LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': config.LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': '🧪 User ID接続テスト\n\nLINE Bot APIの設定が完了しました！\nPhase 2自動化システムの準備が整いました。'
            }
        ]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', 
                               headers=headers, json=data)
        
        if response.status_code == 200:
            print("✅ テストメッセージ送信成功！")
            print("LINEアプリでメッセージを確認してください。")
            return True
        else:
            print(f"❌ メッセージ送信失敗: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 送信エラー: {e}")
        return False

if __name__ == "__main__":
    print("LINE Bot 設定ヘルパー")
    print("=" * 40)
    
    # Bot情報確認
    bot_ok = get_bot_info()
    
    if bot_ok:
        # User IDテスト（設定されている場合）
        test_user_id_if_set()
        
        print("\n📋 次のステップ:")
        if not config.LINE_USER_ID:
            print("1. Botと友達になってメッセージ送信")
            print("2. User IDを取得")
            print("3. automation/config.py でLINE_USER_IDを設定")
            print("4. このスクリプトを再実行")
        else:
            print("1. python automation\\auto_processor.py --test-line")
            print("2. start_phase2_automation.bat")
