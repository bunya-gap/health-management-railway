"""
最小限のテスト用サーバー - HAEからの接続テスト用
"""
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/health-data', methods=['POST'])
def receive_health_data():
    """最小限のPOST受信テスト"""
    try:
        print(f"[{datetime.now()}] POST request received!")
        
        # ヘッダー情報をログ出力
        session_id = request.headers.get('session-id', 'unknown')
        content_type = request.headers.get('content-type', 'unknown')
        
        print(f"Session ID: {session_id}")
        print(f"Content-Type: {content_type}")
        
        # 即座に200を返す
        return jsonify({
            'status': 'success',
            'message': 'Data received',
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health-data', methods=['GET'])
def health_check():
    """GETでの動作確認"""
    return jsonify({
        'status': 'Test server is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """ルートアクセス確認"""
    return "Health Auto Export Test Server is Running!"

if __name__ == '__main__':
    print("=== Health Auto Export Test Server ===")
    print("Starting on 0.0.0.0:5000")
    print("Test URL: http://192.168.0.9:5000/health-data")
    print("=" * 40)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
