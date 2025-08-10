"""
Phase 2統合テストスイート
自動化システム全体の動作確認・診断
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from automation.auto_processor import auto_processor
from automation.line_bot_notifier import notifier
from automation.monitoring import monitor
from automation.config import config

class Phase2TestSuite:
    """Phase 2システム統合テスト"""
    
    def __init__(self):
        self.test_results = {}
        self.base_dir = Path(__file__).parent.parent
        
    def run_all_tests(self) -> Dict[str, bool]:
        """全テスト実行"""
        print("=" * 50)
        print("    Phase 2自動化システム 統合テスト")
        print("=" * 50)
        print()
        
        tests = [
            ("設定チェック", self.test_configuration),
            ("LINE通知テスト", self.test_line_notification),
            ("サーバー監視テスト", self.test_server_monitoring),
            ("データ品質テスト", self.test_data_quality),
            ("自動処理テスト", self.test_auto_processing),
            ("ファイル構成テスト", self.test_file_structure)
        ]
        
        for test_name, test_func in tests:
            print(f"[TEST] {test_name}...")
            try:
                result = test_func()
                self.test_results[test_name] = result
                status = "PASS" if result else "FAIL"
                print(f"       {status}")
            except Exception as e:
                self.test_results[test_name] = False
                print(f"       ERROR: {e}")
            print()
            
        # 結果サマリー
        self.print_test_summary()
        return self.test_results
        
    def test_configuration(self) -> bool:
        """設定テスト"""
        try:
            print("    ・ LINE Bot API設定確認...")
            line_configured = config.is_line_bot_configured()
            
            if not line_configured:
                print("      [WARNING] LINE Bot APIが未設定です")
                print("      [SETUP] 設定方法:")
                print("          1. LINE Developers Console (https://developers.line.biz/) でBot作成")
                print("          2. Channel Access Token取得")
                print("          3. User ID取得（Botと友達になってメッセージ送信）")
                print("          4. automation/config.py でLINE_BOT_CHANNEL_ACCESS_TOKEN・LINE_USER_IDを設定")
                
            print(f"    ・ 自動分析: {'有効' if config.AUTO_ANALYSIS_ENABLED else '無効'}")
            print(f"    ・ 自動通知: {'有効' if config.AUTO_NOTIFICATION_ENABLED else '無効'}")
            print(f"    ・ データ監視間隔: {config.MAX_DATA_AGE_HOURS}時間")
            
            return True  # 設定チェックは情報表示のため常にPass
            
        except Exception as e:
            print(f"      設定チェックエラー: {e}")
            return False
            
    def test_line_notification(self) -> bool:
        """LINE Bot通知テスト"""
        try:
            if not config.is_line_bot_configured():
                print("    ・ LINE Bot APIが未設定のため、スキップ")
                return False
                
            print("    ・ テスト通知送信中...")
            result = notifier.send_test_message()
            
            if result:
                print("    ・ テスト通知が正常に送信されました")
                print("    ・ LINEアプリで通知を確認してください")
            else:
                print("    ・ テスト通知送信に失敗しました")
                
            return result
            
        except Exception as e:
            print(f"      LINE Bot通知テストエラー: {e}")
            return False
            
    def test_server_monitoring(self) -> bool:
        """サーバー監視テスト"""
        try:
            print("    ・ HAEサーバー状況確認中...")
            server_status = monitor.check_server_status()
            
            print(f"    ・ ポート5000: {'稼働中' if server_status['port_active'] else '停止中'}")
            print(f"    ・ プロセス: {'実行中' if server_status['process_running'] else '停止中'}")
            print(f"    ・ HTTP応答: {'正常' if server_status['http_responsive'] else '異常'}")
            
            if not server_status['overall_status']:
                print("    [WARNING] HAEサーバーが正常に稼働していません")
                print("    [SETUP] 対処方法:")
                print("          python health_data_server.py でサーバーを起動")
                
            return server_status['overall_status']
            
        except Exception as e:
            print(f"      サーバー監視テストエラー: {e}")
            return False
            
    def test_data_quality(self) -> bool:
        """データ品質テスト"""
        try:
            print("    ・ データ品質確認中...")
            quality_status = monitor.check_data_quality()
            
            hae_status = quality_status['hae_data_status']
            csv_status = quality_status['csv_data_status']
            analysis_status = quality_status['analysis_status']
            
            print(f"    ・ HAEデータ: {'最新' if hae_status['is_fresh'] else '古い'}")
            if not hae_status['is_fresh']:
                print(f"      最終更新: {hae_status.get('last_update', '不明')}")
                
            print(f"    ・ CSVデータ: {'正常' if csv_status['is_valid'] else '異常'}")
            if csv_status['is_valid']:
                print(f"      データ行数: {csv_status.get('total_lines', '不明')}")
                
            print(f"    ・ 分析レポート: {'最新' if analysis_status['is_recent'] else '古い'}")
            if not analysis_status['is_recent']:
                print(f"      最終分析: {analysis_status.get('last_analysis', '不明')}")
                
            return quality_status['overall_quality']
            
        except Exception as e:
            print(f"      データ品質テストエラー: {e}")
            return False
            
    def test_auto_processing(self) -> bool:
        """自動処理テスト"""
        try:
            print("    ・ 新データ検出テスト...")
            has_new_data = auto_processor.check_and_process_new_data()
            
            if has_new_data:
                print("    ・ 新しいHAEデータが検出され、処理されました")
            else:
                print("    ・ 新しいHAEデータは検出されませんでした（正常）")
                
            print("    ・ データ鮮度チェック...")
            freshness = auto_processor.check_data_freshness()
            
            if freshness:
                print("    ・ データの鮮度は正常です")
            else:
                print("    ・ データが古い可能性があります")
                
            return True  # 自動処理機能が動作すればPass
            
        except Exception as e:
            print(f"      自動処理テストエラー: {e}")
            return False
            
    def test_file_structure(self) -> bool:
        """ファイル構成テスト"""
        try:
            print("    ・ 必須ファイル確認中...")
            
            required_files = [
                "health_data_server.py",
                "health_analytics_engine.py",
                "csv_data_integrator.py",
                "automation/auto_processor.py",
                "automation/config.py",
                "automation/line_bot_notifier.py",
                "automation/monitoring.py"
            ]
            
            missing_files = []
            for file_path in required_files:
                full_path = self.base_dir / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
                    
            if missing_files:
                print("    [ERROR] 不足ファイル:")
                for file in missing_files:
                    print(f"      ・ {file}")
                return False
            else:
                print(f"    ・ 必須ファイル {len(required_files)}個 すべて存在")
                
            # ディレクトリ確認
            required_dirs = ["health_api_data", "reports", "automation"]
            missing_dirs = []
            for dir_path in required_dirs:
                full_path = self.base_dir / dir_path
                if not full_path.exists():
                    missing_dirs.append(dir_path)
                    
            if missing_dirs:
                print("    [ERROR] 不足ディレクトリ:")
                for dir_name in missing_dirs:
                    print(f"      ・ {dir_name}")
                return False
            else:
                print(f"    ・ 必須ディレクトリ {len(required_dirs)}個 すべて存在")
                
            return True
            
        except Exception as e:
            print(f"      ファイル構成テストエラー: {e}")
            return False
            
    def print_test_summary(self):
        """テスト結果サマリー表示"""
        print("=" * 50)
        print("                テスト結果")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:<20} {status}")
            
        print("-" * 50)
        print(f"合計: {total_tests}個   合格: {passed_tests}個   不合格: {failed_tests}個")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n[SUCCESS] Phase 2システムは正常に動作可能です！")
        elif success_rate >= 60:
            print("\n[WARNING] 一部に問題がありますが、基本動作は可能です")
        else:
            print("\n[ERROR] 重要な問題があります。設定を確認してください")
            
        print("\n[NEXT] 次のステップ:")
        if not config.is_line_bot_configured():
            print("   1. LINE Bot APIを設定")
        if not self.test_results.get("サーバー監視テスト", False):
            print("   2. HAEサーバーを起動: python health_data_server.py")
        print("   3. 自動化システム開始: start_phase2_automation.bat")
        
    def generate_diagnostic_report(self) -> str:
        """診断レポート生成"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report = {
                "timestamp": timestamp,
                "test_results": self.test_results,
                "system_status": monitor.check_server_status(),
                "data_quality": monitor.check_data_quality(),
                "configuration": {
                    "line_bot_configured": config.is_line_bot_configured(),
                    "auto_analysis_enabled": config.AUTO_ANALYSIS_ENABLED,
                    "auto_notification_enabled": config.AUTO_NOTIFICATION_ENABLED
                }
            }
            
            # レポートファイル保存
            report_file = self.base_dir / f"temp_phase2_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            return str(report_file)
            
        except Exception as e:
            print(f"診断レポート生成エラー: {e}")
            return ""

def main():
    """メイン実行"""
    test_suite = Phase2TestSuite()
    results = test_suite.run_all_tests()
    
    # 診断レポート生成
    report_file = test_suite.generate_diagnostic_report()
    if report_file:
        print(f"\n[REPORT] 診断レポート保存: {Path(report_file).name}")

if __name__ == "__main__":
    main()
