"""
LINE通知機能 - Phase 2自動化システム
LINE Notifyを使用した健康指標分析結果の自動通知
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .config import config

class LineNotifier:
    """LINE Notify連携クラス"""
    
    def __init__(self):
        self.token = config.get_line_token()
        self.api_url = config.LINE_NOTIFY_API_URL
        
    def send_message(self, message: str) -> bool:
        """LINEメッセージを送信
        
        Args:
            message: 送信するメッセージ
            
        Returns:
            成功: True, 失敗: False
        """
        if not self.token:
            print("[ERROR] LINE Notifyトークンが設定されていません")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'message': message
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                print(f"[SUCCESS] LINE通知送信完了: {len(message)}文字")
                return True
            else:
                print(f"[ERROR] LINE通知送信失敗: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] LINE通知送信エラー: {e}")
            return False
            
    def send_health_report(self, analysis_report: Dict[str, Any]) -> bool:
        """健康分析レポートをLINE送信
        
        Args:
            analysis_report: health_analytics_engine.pyの分析結果
            
        Returns:
            送信成功: True, 失敗: False
        """
        try:
            message = self.format_health_message(analysis_report)
            return self.send_message(message)
        except Exception as e:
            print(f"[ERROR] 健康レポート送信エラー: {e}")
            return False
            
    def format_health_message(self, report: Dict[str, Any]) -> str:
        """分析レポートをLINE通知用メッセージに変換"""
        if not report:
            return "データ分析に失敗しました。サーバーの状態を確認してください。"
            
        try:
            # 基本情報
            timestamp = datetime.now().strftime("%m/%d %H:%M")
            
            # 分析結果取得
            total = report.get('total_performance', {})
            days30 = report.get('last_30days', {})
            days7 = report.get('last_7days', {})
            
            # 分析日付
            analysis_date = total.get('analysis_date', '不明')
            
            # メッセージ生成
            message = f"""🏥 健康レポート ({timestamp})

【総合成績】({total.get('start_date', '開始日')}～{analysis_date})
体脂肪率: {total.get('body_fat_rate_start', 0)}% → {total.get('body_fat_rate_latest', 0)}% ({self._format_change(total.get('body_fat_rate_change', 0))}%)
体脂肪量: {total.get('body_fat_mass_start', 0)}kg → {total.get('body_fat_mass_latest', 0)}kg ({self._format_change(total.get('body_fat_mass_change', 0))}kg)
筋肉量: {total.get('muscle_mass_start', 0)}kg → {total.get('muscle_mass_latest', 0)}kg ({self._format_change(total.get('muscle_mass_change', 0))}kg)

【7日間】(データ{days7.get('actual_data_days', 0)}日分)
体脂肪変化: {self._format_change(days7.get('body_fat_mass_change', 0))}kg
減少ペース: {days7.get('body_fat_reduction_rate_per_day', 0):.3f}kg/日
カロリー収支: {days7.get('calorie_balance_total', 0):.0f}kcal

【30日間】(データ{days30.get('actual_data_days', 0)}日分)
体脂肪変化: {self._format_change(days30.get('body_fat_mass_change', 0))}kg
減少ペース: {days30.get('body_fat_reduction_rate_per_day', 0):.3f}kg/日
カロリー収支: {days30.get('calorie_balance_total', 0):.0f}kcal

{self._generate_trend_emoji(days7, days30)}"""

            return message
            
        except Exception as e:
            print(f"[ERROR] メッセージ生成エラー: {e}")
            return f"レポート生成エラー: {e}"
            
    def _format_change(self, value: float) -> str:
        """変化量をフォーマット（+/-付き）"""
        if value > 0:
            return f"+{value:.1f}"
        else:
            return f"{value:.1f}"
            
    def _generate_trend_emoji(self, days7: Dict, days30: Dict) -> str:
        """トレンド分析絵文字を生成"""
        try:
            # 7日間のカロリー収支
            cal_7days = days7.get('calorie_balance_total', 0)
            
            # 体脂肪減少ペース
            bf_rate_7days = days7.get('body_fat_reduction_rate_per_day', 0)
            bf_rate_30days = days30.get('body_fat_reduction_rate_per_day', 0)
            
            trend_msgs = []
            
            # カロリー収支判定
            if cal_7days < -500:
                trend_msgs.append("✨ 良好なカロリー管理")
            elif cal_7days > 1000:
                trend_msgs.append("⚠️ カロリー収支要注意")
            else:
                trend_msgs.append("📊 カロリー収支安定")
                
            # 体脂肪減少ペース判定
            if bf_rate_7days < -0.02:
                trend_msgs.append("💪 順調な減量ペース")
            elif bf_rate_7days > 0.01:
                trend_msgs.append("🔄 体重管理見直し推奨")
            else:
                trend_msgs.append("📈 安定したペース")
                
            return " | ".join(trend_msgs)
            
        except Exception as e:
            return "📊 トレンド分析中"
            
    def send_alert(self, alert_type: str, message: str) -> bool:
        """アラート通知を送信
        
        Args:
            alert_type: アラートタイプ（data_missing, server_error, etc）
            message: アラートメッセージ
        """
        alert_message = f"🚨 {alert_type.upper()}\n\n{message}\n\n時刻: {datetime.now().strftime('%m/%d %H:%M')}"
        return self.send_message(alert_message)
        
    def send_test_message(self) -> bool:
        """テスト用メッセージ送信"""
        test_message = f"""🧪 LINE通知テスト

Phase 2自動化システムのテスト通知です。

時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
システム: 体組成管理アプリ
状態: Phase 2実装中 ✨"""

        return self.send_message(test_message)

# グローバルインスタンス
notifier = LineNotifier()

if __name__ == "__main__":
    # テスト実行
    print("=== LINE通知テスト ===")
    if config.is_line_configured():
        result = notifier.send_test_message()
        print(f"テスト結果: {'成功' if result else '失敗'}")
    else:
        print("LINE Notifyトークンを設定してください")
        print("設定方法:")
        print("1. https://notify-bot.line.me/ でトークン取得")
        print("2. automation/config.py でLINE_NOTIFY_TOKENを設定")
