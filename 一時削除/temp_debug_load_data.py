"""
load_latest_data 詳細デバッグスクリプト
"""

import sys
from pathlib import Path
import pandas as pd
import traceback

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

def debug_load_data():
    """load_latest_data メソッドの詳細デバッグ"""
    print("=== load_latest_data 詳細デバッグ ===")
    
    try:
        # 1. HealthAnalyticsEngine初期化
        from health_analytics_engine import HealthAnalyticsEngine
        analytics = HealthAnalyticsEngine()
        
        # 2. reports_dir パス確認
        reports_dir = analytics.reports_dir
        print(f"[DEBUG] reports_dir: {reports_dir}")
        print(f"[DEBUG] reports_dir exists: {reports_dir.exists()}")
        
        # 3. 7日移動平均データファイルパス確認
        ma7_file = reports_dir / "7日移動平均データ.csv"
        print(f"[DEBUG] ma7_file: {ma7_file}")
        print(f"[DEBUG] ma7_file exists: {ma7_file.exists()}")
        
        if ma7_file.exists():
            print(f"[DEBUG] file size: {ma7_file.stat().st_size} bytes")
            
            # 4. 手動でファイル読み込みテスト
            print("[DEBUG] 手動ファイル読み込みテスト...")
            try:
                df_manual = pd.read_csv(ma7_file, encoding='utf-8-sig')
                print(f"[SUCCESS] 手動読み込み成功: {len(df_manual)}行")
                print(f"[DEBUG] カラム数: {len(df_manual.columns)}")
                print(f"[DEBUG] 最初の5行:\n{df_manual.head()}")
                
                # 5. date列の変換テスト
                try:
                    df_manual['date'] = pd.to_datetime(df_manual['date'])
                    print(f"[SUCCESS] date列変換成功")
                    print(f"[DEBUG] 日付範囲: {df_manual['date'].min()} ~ {df_manual['date'].max()}")
                except Exception as e:
                    print(f"[ERROR] date列変換失敗: {e}")
                
            except Exception as e:
                print(f"[ERROR] 手動読み込み失敗: {e}")
                traceback.print_exc()
        
        # 6. analytics.load_latest_data() の実行
        print("[DEBUG] analytics.load_latest_data() 実行...")
        df = analytics.load_latest_data()
        print(f"[RESULT] load_latest_data() 結果: {len(df)}行")
        
        if not df.empty:
            print(f"[DEBUG] カラム: {list(df.columns)}")
            print(f"[DEBUG] 最新日付: {df['date'].max()}")
        
        return len(df) > 0
        
    except Exception as e:
        print(f"[ERROR] デバッグ全体エラー: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_load_data()
    print(f"\n=== デバッグ結果: {'成功' if success else '失敗'} ===")
