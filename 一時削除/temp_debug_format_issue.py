"""
古いフォーマット問題のデバッグスクリプト
HAE自動連携時のエラー原因を特定
"""

import sys
from pathlib import Path
import traceback

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

def debug_format_issue():
    """古いフォーマット問題をデバッグ"""
    print("=== 古いフォーマット問題デバッグ ===")
    
    try:
        # 1. health_analytics_engine.pyのインポートテスト
        print("[DEBUG] health_analytics_engine.pyインポート中...")
        from health_analytics_engine import HealthAnalyticsEngine
        analytics = HealthAnalyticsEngine()
        print("[SUCCESS] HealthAnalyticsEngine インポート成功")
        
        # 2. データ読み込みテスト
        print("[DEBUG] データ読み込みテスト...")
        try:
            df = analytics.load_latest_data()
            print(f"[SUCCESS] データ読み込み成功: {len(df)}行")
        except Exception as e:
            print(f"[ERROR] データ読み込み失敗: {e}")
            traceback.print_exc()
            return False
            
        # 3. 分析レポート生成テスト
        print("[DEBUG] 分析レポート生成テスト...")
        try:
            report = analytics.run_scheduled_analysis()
            print(f"[SUCCESS] 分析レポート生成成功: {len(str(report))}文字")
        except Exception as e:
            print(f"[ERROR] 分析レポート生成失敗: {e}")
            traceback.print_exc()
            return False
            
        # 4. 新フォーマット生成テスト
        print("[DEBUG] 新フォーマット生成テスト...")
        try:
            message = analytics.format_notification_message(report)
            print(f"[SUCCESS] 新フォーマット生成成功: {len(message)}文字")
            print(f"[DEBUG] メッセージ先頭50文字: {message[:50]}")
        except Exception as e:
            print(f"[ERROR] 新フォーマット生成失敗: {e}")
            traceback.print_exc()
            
            # 5. フォールバック処理テスト
            print("[DEBUG] フォールバック処理テスト...")
            try:
                from automation.line_bot_notifier import notifier
                fallback_message = notifier.format_health_message(report)
                print(f"[INFO] フォールバック処理実行: {len(fallback_message)}文字")
                print(f"[DEBUG] フォールバック先頭50文字: {fallback_message[:50]}")
                
                return False  # 新フォーマットが失敗したのでFalse
            except Exception as e2:
                print(f"[ERROR] フォールバック処理も失敗: {e2}")
                return False
                
        return True
        
    except Exception as e:
        print(f"[ERROR] 全体処理失敗: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_format_issue()
    print(f"\n=== デバッグ結果: {'成功' if success else '失敗（古いフォーマット原因特定）'} ===")
