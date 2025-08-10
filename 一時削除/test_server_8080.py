"""
ポート8080でのテスト用サーバー
"""
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/health-data', methods=['POST'])
def receive_health_data():
    """最小限のPOST受信テスト"""
    try:
        print(f"[{datetime.now()}] POST request received on port 8080!")
        
        # ヘッダー情報をログ出力
        session_id = request.headers.get('session-id', 'unknown')
        content_type = request.headers.get('content-type', 'unknown')
        
        print(f"Session ID: {session_id}")
        print(f"Content-Type: {content_type}")
        
        # 即座に200を返す
        return jsonify({
            'status': 'success',
            'message': 'Data received on port 8080',
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
        'status': 'Test server running on port 8080',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """ルートアクセス確認"""
    return "Health Auto Export Test Server on Port 8080!"

if __name__ == '__main__':
    print("=== Health Auto Export Test Server (Port 8080) ===")
    print("Starting on 0.0.0.0:8080")
    print("Test URL: http://192.168.0.9:8080/health-data")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
