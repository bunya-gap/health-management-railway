"""
LINE Bot User ID取得用 一時Webhookサーバー
ユーザーがBotにメッセージを送信した時のUser IDを取得
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """LINE Bot Webhookエンドポイント"""
    try:
        body = request.get_json()
        print("\n" + "="*50)
        print(f"Webhook受信: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)
        
        # イベント処理
        for event in body.get('events', []):
            event_type = event.get('type')
            user_id = event.get('source', {}).get('userId')
            
            print(f"イベントタイプ: {event_type}")
            print(f"User ID: {user_id}")
            
            if event_type == 'message':
                message_text = event.get('message', {}).get('text', '')
                print(f"メッセージ: {message_text}")
                
            # User IDをファイルに保存
            if user_id:
                with open('temp_user_id.txt', 'w', encoding='utf-8') as f:
                    f.write(f"LINE_USER_ID = \"{user_id}\"\n")
                    f.write(f"# 取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# メッセージ: {message_text}\n")
                
                print(f"\n🎉 User ID取得成功！")
                print(f"User ID: {user_id}")
                print(f"ファイル保存: temp_user_id.txt")
                
        return jsonify({'status': 'OK'})
        
    except Exception as e:
        print(f"Webhookエラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """ステータス確認"""
    return jsonify({
        'status': 'User ID取得用Webhookサーバー稼働中',
        'time': datetime.now().isoformat(),
        'endpoint': '/webhook'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("LINE Bot User ID取得用 Webhookサーバー")
    print("=" * 60)
    print("1. このサーバーを起動します")
    print("2. LINE Official Account Manager でWebhook URLを設定:")
    print("   URL: http://192.168.0.9:5001/webhook")
    print("3. Botと友達になってメッセージを送信")
    print("4. User IDが temp_user_id.txt に保存されます")
    print("5. Ctrl+C で停止")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
