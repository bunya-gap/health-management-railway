"""
監視・アラート機能 - Phase 2自動化システム
サーバー稼働状況・データ品質監視
"""

import os
import sys
import time
import psutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from automation.line_bot_notifier import notifier
from automation.config import config

class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.health_data_dir = self.base_dir / config.HEALTH_DATA_DIR
        self.reports_dir = self.base_dir / "reports"
        self.server_port = 5000
        self.server_url = f"http://192.168.0.9:{self.server_port}"
        
    def check_server_status(self) -> Dict[str, any]:
        """HAEサーバーの稼働状況をチェック"""
        try:
            # ポート監視
            port_active = self._check_port_listening(self.server_port)
            
            # プロセス監視
            server_process = self._find_server_process()
            
            # HTTP応答チェック
            http_responsive = self._check_http_response()
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "port_active": port_active,
                "process_running": server_process is not None,
                "http_responsive": http_responsive,
                "process_info": server_process,
                "overall_status": port_active and server_process and http_responsive
            }
            
            return status
            
        except Exception as e:
            print(f"[ERROR] サーバー状況チェックエラー: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "port_active": False,
                "process_running": False,
                "http_responsive": False,
                "overall_status": False,
                "error": str(e)
            }
            
    def _check_port_listening(self, port: int) -> bool:
        """指定ポートがLISTENING状態かチェック"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except Exception:
            return False
            
    def _find_server_process(self) -> Optional[Dict]:
        """health_data_server.pyプロセスを検索"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'health_data_server.py' in cmdline:
                        return {
                            "pid": proc.info['pid'],
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_mb": proc.info['memory_info'].rss / 1024 / 1024,
                            "cmdline": cmdline
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except Exception:
            return None
            
    def _check_http_response(self) -> bool:
        """HTTPエンドポイントの応答チェック"""
        try:
            response = requests.get(f"{self.server_url}/health-check", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
            
    def check_data_quality(self) -> Dict[str, any]:
        """データ品質チェック"""
        try:
            quality_report = {
                "timestamp": datetime.now().isoformat(),
                "hae_data_status": self._check_hae_data_freshness(),
                "csv_data_status": self._check_csv_data_integrity(),
                "analysis_status": self._check_recent_analysis()
            }
            
            # 総合判定
            quality_report["overall_quality"] = all([
                quality_report["hae_data_status"]["is_fresh"],
                quality_report["csv_data_status"]["is_valid"],
                quality_report["analysis_status"]["is_recent"]
            ])
            
            return quality_report
            
        except Exception as e:
            print(f"[ERROR] データ品質チェックエラー: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_quality": False,
                "error": str(e)
            }
            
    def _check_hae_data_freshness(self) -> Dict[str, any]:
        """HAEデータの新鮮さチェック"""
        try:
            if not self.health_data_dir.exists():
                return {"is_fresh": False, "reason": "HAEデータディレクトリが存在しません"}
                
            json_files = list(self.health_data_dir.glob("health_data_*.json"))
            
            if not json_files:
                return {"is_fresh": False, "reason": "HAEデータファイルが見つかりません"}
                
            # 最新ファイル取得
            latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
            file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
            age_hours = (datetime.now() - file_time).total_seconds() / 3600
            
            return {
                "is_fresh": age_hours <= config.MAX_DATA_AGE_HOURS,
                "latest_file": latest_file.name,
                "age_hours": round(age_hours, 1),
                "last_update": file_time.strftime("%m/%d %H:%M")
            }
            
        except Exception as e:
            return {"is_fresh": False, "reason": f"チェックエラー: {e}"}
            
    def _check_csv_data_integrity(self) -> Dict[str, any]:
        """CSVデータの整合性チェック"""
        try:
            daily_data_file = self.reports_dir / "日次データ.csv"
            
            if not daily_data_file.exists():
                return {"is_valid": False, "reason": "日次データ.csvが存在しません"}
                
            # ファイル更新時刻
            file_time = datetime.fromtimestamp(daily_data_file.stat().st_mtime)
            age_hours = (datetime.now() - file_time).total_seconds() / 3600
            
            # ファイル行数（簡易チェック）
            with open(daily_data_file, 'r', encoding='utf-8-sig') as f:
                lines = sum(1 for line in f)
                
            return {
                "is_valid": lines > 50,  # 50行以上あれば有効とみなす
                "last_update": file_time.strftime("%m/%d %H:%M"),
                "age_hours": round(age_hours, 1),
                "total_lines": lines
            }
            
        except Exception as e:
            return {"is_valid": False, "reason": f"チェックエラー: {e}"}
            
    def _check_recent_analysis(self) -> Dict[str, any]:
        """最近の分析実行状況チェック"""
        try:
            # 分析レポートファイル検索
            report_files = list(self.reports_dir.glob("analysis_report_*.json"))
            
            if not report_files:
                return {"is_recent": False, "reason": "分析レポートが見つかりません"}
                
            # 最新レポート取得
            latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
            file_time = datetime.fromtimestamp(latest_report.stat().st_mtime)
            age_hours = (datetime.now() - file_time).total_seconds() / 3600
            
            return {
                "is_recent": age_hours <= 6,  # 6時間以内なら有効
                "latest_report": latest_report.name,
                "age_hours": round(age_hours, 1),
                "last_analysis": file_time.strftime("%m/%d %H:%M")
            }
            
        except Exception as e:
            return {"is_recent": False, "reason": f"チェックエラー: {e}"}
            
    def generate_status_report(self) -> str:
        """システム状況レポート生成"""
        try:
            server_status = self.check_server_status()
            data_quality = self.check_data_quality()
            
            # ステータス絵文字
            server_emoji = "✅" if server_status["overall_status"] else "❌"
            data_emoji = "✅" if data_quality["overall_quality"] else "❌"
            
            report = f"""🔍 システム状況レポート
{datetime.now().strftime("%m/%d %H:%M")}

【サーバー状況】{server_emoji}
・ ポート5000: {'稼働中' if server_status['port_active'] else '停止中'}
・ プロセス: {'実行中' if server_status['process_running'] else '停止中'}
・ HTTP応答: {'正常' if server_status['http_responsive'] else '異常'}

【データ品質】{data_emoji}
・ HAEデータ: {'最新' if data_quality['hae_data_status']['is_fresh'] else '古い'}
・ CSVデータ: {'正常' if data_quality['csv_data_status']['is_valid'] else '異常'}
・ 最新分析: {'実行済み' if data_quality['analysis_status']['is_recent'] else '未実行'}

総合状況: {'正常稼働' if server_status['overall_status'] and data_quality['overall_quality'] else '要確認'}"""

            return report
            
        except Exception as e:
            return f"ステータスレポート生成エラー: {e}"
            
    def send_status_alert_if_needed(self) -> bool:
        """必要に応じてアラート送信"""
        try:
            server_status = self.check_server_status()
            data_quality = self.check_data_quality()
            
            # アラート条件チェック
            alerts = []
            
            if not server_status["overall_status"]:
                alerts.append("HAEサーバーが応答しません")
                
            if not data_quality["overall_quality"]:
                if not data_quality["hae_data_status"]["is_fresh"]:
                    alerts.append(f"HAEデータが古い: {data_quality['hae_data_status']['age_hours']}時間前")
                    
                if not data_quality["analysis_status"]["is_recent"]:
                    alerts.append(f"分析が古い: {data_quality['analysis_status']['age_hours']}時間前")
                    
            # アラート送信
            if alerts and config.is_line_configured():
                alert_message = "🚨 システムアラート\n\n" + "\n".join(f"・ {alert}" for alert in alerts)
                return notifier.send_alert("SYSTEM_ALERT", alert_message)
                
            return True
            
        except Exception as e:
            print(f"[ERROR] アラートチェックエラー: {e}")
            return False

# グローバルインスタンス
monitor = SystemMonitor()

if __name__ == "__main__":
    print("=== システム監視テスト ===")
    
    print("\n1. サーバー状況:")
    server_status = monitor.check_server_status()
    print(json.dumps(server_status, indent=2, ensure_ascii=False))
    
    print("\n2. データ品質:")
    data_quality = monitor.check_data_quality()
    print(json.dumps(data_quality, indent=2, ensure_ascii=False))
    
    print("\n3. ステータスレポート:")
    report = monitor.generate_status_report()
    print(report)
    
    print("\n4. アラートチェック:")
    alert_result = monitor.send_status_alert_if_needed()
    print(f"アラート結果: {'送信' if alert_result else '不要/失敗'}")
