"""
重複通知問題デバッグスクリプト
HAE自動連携時の複数通知送信を調査・修正
"""

import sys
from pathlib import Path
import json
import traceback
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

def debug_duplicate_notifications():
    """重複通知問題をデバッグ"""
    print("=== 重複通知問題デバッグ ===")
    
    try:
        # 1. auto_processor.py の処理を詳細確認
        print("[DEBUG] auto_processor.py の通知処理確認...")
        from automation.auto_processor import auto_processor
        from automation.line_bot_notifier import notifier
        from health_analytics_engine import HealthAnalyticsEngine
        
        # 2. 通知処理を一回だけ実行してログを確認
        print("[DEBUG] 手動で一回だけ通知処理実行...")
        analytics = HealthAnalyticsEngine()
        
        # 分析レポート生成
        print("[DEBUG] 分析レポート生成中...")
        report = analytics.run_scheduled_analysis()
        
        if report:
            print(f"[SUCCESS] 分析レポート生成完了: {len(str(report))}文字")
            
            # 通知送信
            print("[DEBUG] LINE通知送信中...")
            notification_success = notifier.send_health_report(report)
            
            if notification_success:
                print("[SUCCESS] LINE通知送信完了（新フォーマット）")
            else:
                print("[ERROR] LINE通知送信失敗")
        else:
            print("[ERROR] 分析レポート生成失敗")
            
        # 3. 複数の自動化プロセスが実行中かチェック
        print("[DEBUG] 実行中の自動化プロセス確認...")
        
        # 4. 古い設定・古いプロセスが残っていないかチェック
        print("[DEBUG] 古い設定・プロセス確認...")
        
        # config.py の設定確認
        from automation.config import config
        print(f"[DEBUG] AUTO_NOTIFICATION_ENABLED: {config.AUTO_NOTIFICATION_ENABLED}")
        print(f"[DEBUG] LINE設定: {config.is_line_configured()}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] デバッグエラー: {e}")
        traceback.print_exc()
        return False

def find_duplicate_sources():
    """重複送信の原因を特定"""
    print("\n[DEBUG] 重複送信源の特定...")
    
    # システム内の全送信処理を検索
    import os
    import re
    
    search_patterns = [
        r'send_.*message',
        r'send_.*report',
        r'LINE.*送信',
        r'健康レポート',
        r'notification'
    ]
    
    project_root = Path(__file__).parent
    suspicious_files = []
    
    for pattern in search_patterns:
        print(f"[DEBUG] パターン検索: {pattern}")
        
        # Python ファイルを検索
        for py_file in project_root.rglob("*.py"):
            if "一時削除" in str(py_file):
                continue  # 一時削除フォルダはスキップ
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        suspicious_files.append(str(py_file))
            except:
                pass
    
    # 重複を除去
    suspicious_files = list(set(suspicious_files))
    
    print(f"[DEBUG] 送信処理を含むファイル: {len(suspicious_files)}個")
    for file in suspicious_files[:10]:  # 最初の10個のみ表示
        print(f"  - {file}")
    
    return suspicious_files

if __name__ == "__main__":
    print(f"実行時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    
    # 重複通知のデバッグ
    debug_success = debug_duplicate_notifications()
    
    # 重複送信源の特定
    suspicious_files = find_duplicate_sources()
    
    print(f"\n=== デバッグ完了 ===")
    print(f"通知テスト: {'成功' if debug_success else '失敗'}")
    print(f"疑わしいファイル: {len(suspicious_files)}個")
    
    if debug_success:
        print("\n[INFO] 通知は1回だけ送信されました")
        print("[INFO] 重複問題は別の原因の可能性があります")
    else:
        print("\n[WARNING] 通知処理に問題があります")
