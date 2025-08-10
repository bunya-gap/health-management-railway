"""
LINE Bot API通知機能 - Phase 2自動化システム（LINE Notify代替）
LINE Messaging APIを使用した健康指標分析結果の自動通知
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .config import config

class LineBotNotifier:
    """LINE Bot API連携クラス（LINE Notify代替）"""
    
    def __init__(self):
        self.channel_access_token = config.get_line_bot_token()
        self.user_id = config.get_line_user_id()
        self.api_url = "https://api.line.me/v2/bot/message/push"
        
    def send_message(self, message: str) -> bool:
        """LINEメッセージを送信（LINE Bot API使用）
        
        Args:
            message: 送信するメッセージ
            
        Returns:
            成功: True, 失敗: False
        """
        if not self.channel_access_token:
            print("[ERROR] LINE Bot Channel Access Tokenが設定されていません")
            return False
            
        if not self.user_id:
            print("[ERROR] LINE User IDが設定されていません")
            return False
            
        headers = {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'to': self.user_id,
            'messages': [
                {
                    'type': 'text',
                    'text': message
                }
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"[SUCCESS] LINE Bot通知送信完了: {len(message)}文字")
                return True
            else:
                print(f"[ERROR] LINE Bot通知送信失敗: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] LINE Bot通知送信エラー: {e}")
            return False
            
    def send_rich_message(self, title: str, summary: str, details: Dict[str, Any]) -> bool:
        """リッチメッセージ送信（Flex Message使用）"""
        if not self.channel_access_token or not self.user_id:
            return False
            
        # Flex Messageでリッチな健康レポートを作成
        flex_message = self._create_health_flex_message(title, summary, details)
        
        headers = {
            'Authorization': f'Bearer {self.channel_access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'to': self.user_id,
            'messages': [flex_message]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"[SUCCESS] LINE Bot リッチメッセージ送信完了")
                return True
            else:
                print(f"[ERROR] LINE Bot リッチメッセージ送信失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] LINE Bot リッチメッセージ送信エラー: {e}")
            return False
            
    def _create_health_flex_message(self, title: str, summary: str, details: Dict[str, Any]) -> Dict:
        """健康レポート用Flex Message作成"""
        flex_message = {
            "type": "flex",
            "altText": f"{title} - {summary}",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🏥 ボディリコンプ進捗レポート",
                            "weight": "bold",
                            "color": "#ffffff",
                            "size": "lg"
                        },
                        {
                            "type": "text",
                            "text": datetime.now().strftime("%m/%d %H:%M"),
                            "color": "#ffffff",
                            "size": "sm"
                        }
                    ],
                    "backgroundColor": "#27ACB2",
                    "paddingAll": "15px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": []
                }
            }
        }
        
        # 動的にコンテンツを追加
        body_contents = flex_message["contents"]["body"]["contents"]
        
        # 総合成績
        if "total_performance" in details:
            total = details["total_performance"]
            body_contents.extend([
                {
                    "type": "text",
                    "text": "【総合成績】",
                    "weight": "bold",
                    "color": "#333333",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"体脂肪率: {total.get('body_fat_rate_start', 0)}% → {total.get('body_fat_rate_latest', 0)}%",
                    "size": "sm",
                    "color": "#666666"
                },
                {
                    "type": "text",
                    "text": f"体脂肪量: {total.get('body_fat_mass_start', 0)}kg → {total.get('body_fat_mass_latest', 0)}kg",
                    "size": "sm",
                    "color": "#666666"
                }
            ])
            
        # 7日間成績
        if "last_7days" in details:
            days7 = details["last_7days"]
            body_contents.extend([
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "【7日間成績】",
                    "weight": "bold",
                    "color": "#333333",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"カロリー収支: {days7.get('calorie_balance_total', 0):.0f}kcal",
                    "size": "sm",
                    "color": "#666666"
                },
                {
                    "type": "text",
                    "text": f"減少ペース: {days7.get('body_fat_reduction_rate_per_day', 0):.3f}kg/日",
                    "size": "sm",
                    "color": "#666666"
                }
            ])
            
        return flex_message
        
    def send_health_report(self, analysis_report: Dict[str, Any]) -> bool:
        """ボディリコンプ特化健康分析レポートをLINE送信
        
        Args:
            analysis_report: health_analytics_engine.pyの分析結果
            
        Returns:
            送信成功: True, 失敗: False
        """
        try:
            # ボディリコンプ特化メッセージを作成
            message = self.format_health_message(analysis_report)
            
            # 設定に応じてリッチメッセージまたはテキストメッセージを送信
            if config.USE_RICH_MESSAGES:
                # リッチメッセージは複雑すぎるので、シンプルテキストに統一
                return self.send_message(message)
            else:
                return self.send_message(message)
                
        except Exception as e:
            print(f"[ERROR] ボディリコンプレポート送信エラー: {e}")
            return False
            
    def format_health_message(self, report: Dict[str, Any]) -> str:
        """新カード式レポートフォーマット（LINE Bot版）"""
        if not report:
            return "データ分析に失敗しました。サーバーの状態を確認してください。"
            
        try:
            # 健康分析エンジンから直接フォーマット済みメッセージを取得
            from health_analytics_engine import HealthAnalyticsEngine
            analytics = HealthAnalyticsEngine()
            
            # 新フォーマットメッセージを生成
            formatted_message = analytics.format_notification_message(report)
            
            return formatted_message
            
        except Exception as e:
            print(f"[ERROR] LINE用メッセージ生成エラー: {e}")
            # フォールバック：基本情報のみ表示
            try:
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                kgi = report.get('kgi_progress', {})
                
                fallback_message = f"""🎯 体脂肪率進捗 | {timestamp}

📍現在: {kgi.get('current_bf_rate', 0)}%  🎯目標: {kgi.get('target_bf_rate', 12)}%
📊 進捗率: {kgi.get('progress_rate', 0)}%

※詳細レポート生成に失敗しました
エラー: {e}"""
                
                return fallback_message
                
            except:
                return f"レポート生成エラー: {e}"
            
    def _format_change(self, value: float) -> str:
        """変化量をフォーマット（+/-付き）"""
        if value > 0:
            return f"+{value:.2f}"
        else:
            return f"{value:.2f}"
            
    def _format_change_safe(self, value) -> str:
        """変化量を安全にフォーマット（None対応）"""
        if value is None:
            return "データ不足"
        return f"{value:+.2f}"
            
    def _generate_trend_emoji(self, days7: Dict, days14: Dict, days28: Dict) -> str:
        """トレンド分析絵文字を生成（3期間対応）"""
        try:
            # 7日間のカロリー収支
            cal_7days = days7.get('calorie_balance_total', 0)
            
            # 体脂肪減少傾向
            bf_7days = days7.get('body_fat_mass_change')
            bf_14days = days14.get('body_fat_mass_change')
            bf_28days = days28.get('body_fat_mass_change')
            
            trend_msgs = []
            
            # カロリー収支判定
            if cal_7days < -500:
                trend_msgs.append("✨ 良好なカロリー管理")
            elif cal_7days > 1000:
                trend_msgs.append("⚠️ カロリー収支要注意")
            else:
                trend_msgs.append("📊 カロリー収支安定")
                
            # 体脂肪トレンド判定
            if bf_7days is not None and bf_14days is not None:
                if bf_7days < -0.2 and bf_14days < -0.4:
                    trend_msgs.append("💪 順調な減量ペース")
                elif bf_7days > 0.1:
                    trend_msgs.append("🔄 体重管理見直し推奨")
                else:
                    trend_msgs.append("📈 安定したペース")
            else:
                trend_msgs.append("📊 体組成データ蓄積中")
                
            return " | ".join(trend_msgs)
            
        except Exception as e:
            return "📊 トレンド分析中"
            
    def _get_fat_loss_status_emoji(self, metabolism: dict) -> str:
        """脂肪減少状況の絵文字判定"""
        fat_loss_7d = metabolism.get('fat_loss_7d', 0)
        fat_loss_14d = metabolism.get('fat_loss_14d', 0)
        
        if fat_loss_7d is None or fat_loss_14d is None:
            return "📊 データ蓄積中"
        
        if fat_loss_14d <= 0 and fat_loss_7d <= 0:
            return "停滞中 🔴"
        elif fat_loss_7d < -0.2:
            return "順調 ✅"
        else:
            return "緩やか 🟡"
            
    def _get_metabolism_status_emoji(self, metabolism: dict) -> str:
        """代謝状況の絵文字判定"""
        temp_change = metabolism.get('body_temp_change')
        
        if temp_change is None:
            return "データ不足 📊"
        elif temp_change < -0.2:
            return "代謝低下の可能性 🟡"
        elif temp_change < -0.1:
            return "要注意 🟡"
        else:
            return "✅"
            
    def _get_fat_burn_status_emoji(self, metabolism: dict) -> str:
        """脂肪燃焼状況の絵文字"""
        if metabolism.get('metabolism_status') == 'stopped':
            return "🔴"
        else:
            return "✅"
            
    def _get_fat_burn_status_text(self, metabolism: dict) -> str:
        """脂肪燃焼状況のテキスト"""
        if metabolism.get('metabolism_status') == 'stopped':
            return "完全停滞"
        else:
            return "維持中"
            
    def _get_metabolism_status_text(self, metabolism: dict) -> str:
        """代謝効率のテキスト"""
        temp_change = metabolism.get('body_temp_change')
        
        if temp_change is None:
            return "データ不足"
        elif temp_change < -0.2:
            return "低下傾向"
        else:
            return "安定"
            
    def _get_cheat_day_reason(self, metabolism: dict) -> str:
        """チートデイ推奨理由"""
        if metabolism.get('cheat_day_recommended', False):
            return "理由: 脂肪停滞2週間 + 体表温低下"
        else:
            return "理由: 現状維持で経過観察"
            
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
        test_message = f"""🧪 LINE Bot 通知テスト

Phase 2自動化システムのテスト通知です。

時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
システム: 体組成管理アプリ
通知方式: LINE Bot API
状態: Phase 2実装中 ✨"""

        return self.send_message(test_message)
        
    def get_user_profile(self) -> Optional[Dict]:
        """ユーザープロフィール取得（設定確認用）"""
        if not self.channel_access_token or not self.user_id:
            return None
            
        headers = {
            'Authorization': f'Bearer {self.channel_access_token}'
        }
        
        try:
            response = requests.get(
                f"https://api.line.me/v2/bot/profile/{self.user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] ユーザープロフィール取得失敗: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] ユーザープロフィール取得エラー: {e}")
            return None

# グローバルインスタンス
notifier = LineBotNotifier()

if __name__ == "__main__":
    # テスト実行
    print("=== LINE Bot 通知テスト ===")
    if config.is_line_bot_configured():
        print("LINE Bot設定確認中...")
        
        # ユーザープロフィール確認
        profile = notifier.get_user_profile()
        if profile:
            print(f"接続ユーザー: {profile.get('displayName', '不明')}")
            
        # テストメッセージ送信
        result = notifier.send_test_message()
        print(f"テスト結果: {'成功' if result else '失敗'}")
    else:
        print("LINE Bot設定を完了してください")
        print("設定方法:")
        print("1. LINE Developers Console (https://developers.line.biz/) でBot作成")
        print("2. Channel Access Token取得")
        print("3. User ID取得（Botと友達になってメッセージ送信）")
        print("4. automation/config.py で設定")