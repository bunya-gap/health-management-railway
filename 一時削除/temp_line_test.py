"""
LINE Bot API 接続テスト - 直接実行版
"""

import requests
import json
from datetime import datetime

# 設定（config.pyから直接コピー）
LINE_BOT_CHANNEL_ACCESS_TOKEN = "GGuEAJ5NWDI4TmcU2FdUp0pr+kTm+hh6d3Rsaxh1wOQVUgGAaBCB2zb68pADZbDlSjsekL3GyeXLldaXws+56ZbPURItuFUK4sH9yCP0S2m8F5cb29UKQyEBh5NGJPif1KdeHIAP1tEL5WOnchAa0wdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U352695f9f7d6ee3e869b4b636f4e4864"

def test_line_bot():
    """LINE Bot API テスト"""
    print("=== LINE Bot API 接続テスト ===")
    print(f"User ID: {LINE_USER_ID}")
    
    headers = {
        'Authorization': f'Bearer {LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # テストメッセージ
    test_message = f"""🎉 LINE Bot API 接続テスト成功！

Phase 2自動化システムの設定が完了しました。

時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
システム: 体組成管理アプリ
通知方式: LINE Bot API ✨

これで完全ハンズフリー健康管理システムの準備が整いました！"""

    data = {
        'to': LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': test_message
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ テストメッセージ送信成功！")
            print("✅ LINE Bot API設定完了！")
            print("📱 LINEアプリでメッセージを確認してください")
            return True
        else:
            print(f"❌ 送信失敗: {response.status_code}")
            print(f"エラー詳細: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def test_health_report_format():
    """健康レポート形式のテスト"""
    print("\n=== 健康レポート形式テスト ===")
    
    # サンプル分析データ
    sample_report = {
        'total_performance': {
            'start_date': '2025-06-04',
            'analysis_date': '2025-08-09',
            'body_fat_rate_start': 18.8,
            'body_fat_rate_latest': 17.7,
            'body_fat_rate_change': -1.1,
            'body_fat_mass_start': 12.2,
            'body_fat_mass_latest': 11.2,
            'body_fat_mass_change': -1.0,
            'muscle_mass_start': 52.7,
            'muscle_mass_latest': 52.1,
            'muscle_mass_change': -0.6
        },
        'last_7days': {
            'actual_data_days': 7,
            'body_fat_mass_change': -0.2,
            'body_fat_reduction_rate_per_day': -0.029,
            'calorie_balance_total': 3184
        },
        'last_30days': {
            'actual_data_days': 30,
            'body_fat_mass_change': -0.3,
            'body_fat_reduction_rate_per_day': -0.010,
            'calorie_balance_total': 5975
        }
    }
    
    # 健康レポートメッセージ作成
    timestamp = datetime.now().strftime("%m/%d %H:%M")
    total = sample_report['total_performance']
    days30 = sample_report['last_30days']
    days7 = sample_report['last_7days']
    
    health_message = f"""🏥 健康レポート ({timestamp})

【総合成績】({total['start_date']}～{total['analysis_date']})
体脂肪率: {total['body_fat_rate_start']}% → {total['body_fat_rate_latest']}% ({total['body_fat_rate_change']:+.1f}%)
体脂肪量: {total['body_fat_mass_start']}kg → {total['body_fat_mass_latest']}kg ({total['body_fat_mass_change']:+.1f}kg)
筋肉量: {total['muscle_mass_start']}kg → {total['muscle_mass_latest']}kg ({total['muscle_mass_change']:+.1f}kg)

【7日間】(データ{days7['actual_data_days']}日分)
体脂肪変化: {days7['body_fat_mass_change']:+.1f}kg
減少ペース: {days7['body_fat_reduction_rate_per_day']:.3f}kg/日
カロリー収支: {days7['calorie_balance_total']:.0f}kcal

【30日間】(データ{days30['actual_data_days']}日分)
体脂肪変化: {days30['body_fat_mass_change']:+.1f}kg
減少ペース: {days30['body_fat_reduction_rate_per_day']:.3f}kg/日
カロリー収支: {days30['calorie_balance_total']:.0f}kcal

✨ 良好なカロリー管理 | 💪 順調な減量ペース"""

    headers = {
        'Authorization': f'Bearer {LINE_BOT_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'to': LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': health_message
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 健康レポート形式テスト送信成功！")
            print("📱 LINEで健康レポートの表示を確認してください")
            return True
        else:
            print(f"❌ 健康レポート送信失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 健康レポート送信エラー: {e}")
        return False

if __name__ == "__main__":
    print("LINE Bot API 総合テスト")
    print("=" * 50)
    
    # 基本接続テスト
    basic_test = test_line_bot()
    
    if basic_test:
        print("\n" + "="*50)
        
        # 健康レポート形式テスト
        health_test = test_health_report_format()
        
        if health_test:
            print("\n🎉 LINE Bot API設定完了！")
            print("次のステップ:")
            print("1. python automation\\auto_processor.py --test-line")
            print("2. python automation\\auto_processor.py --manual")  
            print("3. start_phase2_automation.bat")
        else:
            print("\n⚠️ 健康レポート形式に問題があります")
    else:
        print("\n❌ LINE Bot API基本設定に問題があります")
        print("Channel Access Token・User IDを確認してください")
