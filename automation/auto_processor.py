"""
イベント駆動自動処理 - Phase 2自動化システム
HAEデータ受信時の自動分析・通知実行
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from health_analytics_engine import HealthAnalyticsEngine
from automation.line_bot_notifier import notifier
from automation.config import config

class AutoProcessor:
    """自動処理エンジン"""
    
    def __init__(self):
        self.analytics = HealthAnalyticsEngine()
        self.health_data_dir = Path(config.HEALTH_DATA_DIR)
        self.last_processed_file = None
        self.monitoring = True
        
    def start_monitoring(self):
        """HAEデータ監視開始"""
        print("=== Phase 2自動処理システム開始 ===")
        print(f"監視ディレクトリ: {self.health_data_dir}")
        print(f"LINE通知: {'有効' if config.is_line_configured() else '無効（要設定）'}")
        
        # 初回実行
        self.check_and_process_new_data()
        
        # 監視ループ開始
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        
        print("[INFO] 自動監視開始しました。Ctrl+Cで停止できます。")
        
        try:
            # メインスレッドを維持
            while self.monitoring:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[INFO] 自動処理システムを停止します...")
            self.monitoring = False
            
    def _monitoring_loop(self):
        """データ監視ループ（別スレッド）"""
        while self.monitoring:
            try:
                self.check_and_process_new_data()
                time.sleep(30)  # 30秒ごとにチェック
            except Exception as e:
                print(f"[ERROR] 監視ループエラー: {e}")
                time.sleep(60)  # エラー時は1分待機
                
    def check_and_process_new_data(self) -> bool:
        """新しいHAEデータをチェックして処理
        
        Returns:
            新データ処理実行: True, 新データなし: False
        """
        try:
            # 最新のHAEファイルを取得
            latest_file = self._get_latest_hae_file()
            
            if not latest_file:
                return False
                
            # 新しいファイルかチェック
            if latest_file == self.last_processed_file:
                return False
                
            print(f"[INFO] 新しいHAEデータ検出: {latest_file.name}")
            
            # 自動分析実行
            success = self.execute_auto_analysis()
            
            if success:
                self.last_processed_file = latest_file
                print(f"[SUCCESS] 自動処理完了: {latest_file.name}")
                return True
            else:
                print(f"[ERROR] 自動処理失敗: {latest_file.name}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 新データチェックエラー: {e}")
            return False
            
    def _get_latest_hae_file(self) -> Optional[Path]:
        """最新のHAEデータファイルを取得"""
        if not self.health_data_dir.exists():
            return None
            
        json_files = list(self.health_data_dir.glob("health_data_*.json"))
        
        if not json_files:
            return None
            
        # 最新ファイルを取得（作成時刻基準）
        latest_file = max(json_files, key=lambda x: x.stat().st_ctime)
        return latest_file
        
    def execute_auto_analysis(self) -> bool:
        """自動分析実行（統合処理）
        
        Returns:
            処理成功: True, 失敗: False
        """
        try:
            print("[INFO] 自動分析実行開始...")
            
            # 分析実行
            report = self.analytics.run_scheduled_analysis()
            
            if not report:
                print("[ERROR] 分析レポート生成に失敗しました")
                return False
                
            # LINE通知送信（設定されている場合）
            if config.AUTO_NOTIFICATION_ENABLED and config.is_line_configured():
                print("[INFO] LINE通知送信中...")
                notification_success = notifier.send_health_report(report)
                
                if notification_success:
                    print("[SUCCESS] LINE通知送信完了")
                else:
                    print("[WARNING] LINE通知送信に失敗しました")
                    
            else:
                print("[INFO] LINE通知はスキップ（未設定または無効）")
                
            return True
            
        except Exception as e:
            print(f"[ERROR] 自動分析実行エラー: {e}")
            
            # エラー通知（LINE設定済みの場合）
            if config.is_line_configured():
                notifier.send_alert("ANALYSIS_ERROR", f"自動分析でエラーが発生しました: {e}")
                
            return False
            
    def check_data_freshness(self) -> bool:
        """データの新鮮さをチェック（監視機能）"""
        try:
            latest_file = self._get_latest_hae_file()
            
            if not latest_file:
                print("[WARNING] HAEデータファイルが見つかりません")
                return False
                
            # ファイルの最終更新時刻
            file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
            current_time = datetime.now()
            age_hours = (current_time - file_time).total_seconds() / 3600
            
            if age_hours > config.MAX_DATA_AGE_HOURS:
                alert_msg = f"HAEデータが{age_hours:.1f}時間更新されていません。\n最終データ: {file_time.strftime('%m/%d %H:%M')}"
                
                print(f"[ALERT] {alert_msg}")
                
                # アラート通知
                if config.is_line_configured():
                    notifier.send_alert("DATA_MISSING", alert_msg)
                    
                return False
                
            return True
            
        except Exception as e:
            print(f"[ERROR] データ新鮮さチェックエラー: {e}")
            return False
            
    def manual_analysis(self) -> bool:
        """手動分析実行（テスト用）"""
        print("=== 手動分析実行 ===")
        return self.execute_auto_analysis()
        
    def test_line_notification(self) -> bool:
        """LINE通知テスト"""
        print("=== LINE通知テスト ===")
        
        if not config.is_line_configured():
            print("[ERROR] LINE Notifyトークンが設定されていません")
            return False
            
        return notifier.send_test_message()

# グローバルインスタンス        
auto_processor = AutoProcessor()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2自動処理システム")
    parser.add_argument("--monitor", action="store_true", help="監視モード開始")
    parser.add_argument("--test-line", action="store_true", help="LINE通知テスト")
    parser.add_argument("--manual", action="store_true", help="手動分析実行")
    parser.add_argument("--check-data", action="store_true", help="データ新鮮さチェック")
    
    args = parser.parse_args()
    
    if args.test_line:
        auto_processor.test_line_notification()
    elif args.manual:
        auto_processor.manual_analysis()
    elif args.check_data:
        auto_processor.check_data_freshness()
    elif args.monitor:
        auto_processor.start_monitoring()
    else:
        print("使用方法:")
        print("  --monitor     : 自動監視開始")
        print("  --test-line   : LINE通知テスト")
        print("  --manual      : 手動分析実行")
        print("  --check-data  : データ鮮度チェック")
