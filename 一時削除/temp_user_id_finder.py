"""
LINE Bot User ID 簡単取得ツール
Push APIのエラーレスポンスからUser IDを特定
"""

import sys
from pathlib import Path
import requests

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from automation.config import config

def try_common_user_ids():
    """一般的なUser IDパターンを試行"""
    print("=== User ID 自動検出 ===")
    
    if not config.LINE_BOT_CHANNEL_ACCESS_TOKEN:
        print("[ERROR] Channel Access Token が設定されていません")
        return None
        
    # 一般的なUser IDパターン（実際のUser IDは動的に生成される）
    # 代わりに、Push APIを使って間違ったUser IDでリクエストし、
    # エラーレスポンスから正しいUser IDのヒントを得る
    
    headers = {
        'Authorization': f'Bearer {config.LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("Bot情報を確認中...")
    
    # Bot情報取得
    try:
        response = requests.get('https://api.line.me/v2/bot/info', headers=headers)
        if response.status_code == 200:
            bot_info = response.json()
            print(f"Bot名: {bot_info.get('displayName', '不明')}")
            print(f"Bot User ID: {bot_info.get('userId', '不明')}")
            
            # BotのUser IDをベースに、実際のユーザーIDを推測
            bot_user_id = bot_info.get('userId', '')
            if bot_user_id:
                print(f"\n📋 Bot User ID: {bot_user_id}")
                print("🔍 実際のUser IDはBotと友達になったユーザーに固有です")
                
                # 友達一覧を試す（権限がある場合）
                print("\n友達情報の取得を試行中...")
                try:
                    followers_response = requests.get(
                        'https://api.line.me/v2/bot/followers/ids',
                        headers=headers
                    )
                    
                    if followers_response.status_code == 200:
                        followers_data = followers_response.json()
                        user_ids = followers_data.get('userIds', [])
                        
                        if user_ids:
                            print(f"✅ 友達リスト取得成功！")
                            print(f"友達数: {len(user_ids)}")
                            
                            # 最初のUser IDを使用
                            first_user_id = user_ids[0]
                            print(f"🎯 User ID発見: {first_user_id}")
                            
                            # User IDをファイルに保存
                            with open('temp_user_id.txt', 'w', encoding='utf-8') as f:
                                f.write(f'LINE_USER_ID = "{first_user_id}"\n')
                                f.write(f'# 自動取得されたUser ID\n')
                                f.write(f'# Bot User ID: {bot_user_id}\n')
                            
                            return first_user_id
                        else:
                            print("❌ 友達がまだ追加されていません")
                            
                    else:
                        print(f"⚠️ 友達リスト取得失敗: {followers_response.status_code}")
                        if followers_response.status_code == 403:
                            print("   権限不足：友達リストAPIが無効化されている可能性があります")
                        
                except Exception as e:
                    print(f"⚠️ 友達リスト取得エラー: {e}")
                    
        else:
            print(f"❌ Bot情報取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        
    return None

def manual_user_id_input():
    """手動User ID入力"""
    print("\n" + "="*50)
    print("手動User ID入力")
    print("="*50)
    print("User IDの一般的な形式: U + 32文字の英数字")
    print("例: U1234567890abcdef1234567890abcdef")
    print("例: Uabcdef1234567890abcdef1234567890")
    print()
    
    # LINEアプリでUser IDを確認する方法を案内
    print("📱 User ID確認方法:")
    print("1. LINEアプリでBotのプロフィールを開く")
    print("2. 「設定」→「アカウント」→「ユーザーID」で確認")
    print("3. または開発者ツールのネットワークタブでAPI通信を確認")
    print()
    
    user_input = input("User IDを入力してください（Enterでスキップ）: ").strip()
    
    if user_input and user_input.startswith('U') and len(user_input) == 33:
        # User IDをファイルに保存
        with open('temp_user_id.txt', 'w', encoding='utf-8') as f:
            f.write(f'LINE_USER_ID = "{user_input}"\n')
            f.write(f'# 手動入力されたUser ID\n')
        
        print(f"✅ User ID保存完了: {user_input}")
        return user_input
    else:
        print("❌ 無効なUser ID形式です")
        return None

def test_user_id(user_id):
    """User IDのテスト送信"""
    print(f"\n=== User ID テスト送信 ===")
    print(f"User ID: {user_id}")
    
    headers = {
        'Authorization': f'Bearer {config.LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': '🎉 User ID取得成功！\n\nLINE Bot APIの設定が完了しました。\nPhase 2自動化システムの準備が整いました！'
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

def main():
    print("LINE Bot User ID 簡単取得ツール")
    print("=" * 50)
    
    # 自動検出を試行
    detected_user_id = try_common_user_ids()
    
    if detected_user_id:
        print(f"\n🎯 User ID自動検出成功: {detected_user_id}")
        
        # テスト送信
        if test_user_id(detected_user_id):
            print("\n✅ 設定完了！次のステップに進めます。")
            return detected_user_id
    
    # 手動入力
    manual_user_id = manual_user_id_input()
    
    if manual_user_id:
        if test_user_id(manual_user_id):
            print("\n✅ 設定完了！次のステップに進めます。")
            return manual_user_id
    
    print("\n❌ User ID取得に失敗しました")
    print("📋 代替方法:")
    print("1. ngrokでHTTPS Webhookを設定")
    print("2. LINE Developers Console のログ確認")
    print("3. Botにメッセージ送信後、ブラウザの開発者ツールでネットワーク通信確認")
    
    return None

if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n🎉 取得成功: {result}")
        print("次のコマンドで自動化システムをテストできます:")
        print("python automation\\auto_processor.py --test-line")
