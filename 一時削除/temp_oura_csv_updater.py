"""
Oura Ring総消費カロリー実装ツール
実際のCSVデータをOura APIデータで更新
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from oura_config import OURA_ACCESS_TOKEN, OURA_API_BASE_URL


class OuraCalorieUpdater:
    """Oura Ring総消費カロリーでCSVを更新"""
    
    def __init__(self):
        self.access_token = OURA_ACCESS_TOKEN
        self.base_url = OURA_API_BASE_URL
        self.project_root = Path(__file__).parent
        self.reports_dir = self.project_root / "reports"
        
    def get_oura_calories_for_date(self, date: str) -> dict:
        """指定日のOura総消費カロリーを取得"""
        if not self.access_token:
            return {'error': 'Oura APIトークンが設定されていません'}
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{self.base_url}/usercollection/daily_activity"
            params = {'start_date': date}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return {'error': f'API失敗: {response.status_code}'}
            
            data = response.json()
            
            if 'data' in data and data['data']:
                for activity in data['data']:
                    if activity.get('day') == date:
                        total_cal = activity.get('total_calories')
                        active_cal = activity.get('active_calories')
                        estimated_basal = total_cal - active_cal if total_cal and active_cal else None
                        
                        return {
                            'success': True,
                            'date': date,
                            'total_calories': total_cal,
                            'active_calories': active_cal,
                            'estimated_basal': estimated_basal
                        }
            
            return {'error': f'{date}のデータなし'}
            
        except Exception as e:
            return {'error': f'API呼び出しエラー: {str(e)}'}
    
    def update_csv_with_oura_calories(self, csv_path: str, backup: bool = True) -> dict:
        """CSVファイルをOura総消費カロリーで更新"""
        try:
            # バックアップ作成
            if backup:
                backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                shutil.copy2(csv_path, backup_path)
                print(f"[BACKUP] バックアップ作成: {backup_path}")
            
            # CSV読み込み
            df = pd.read_csv(csv_path)
            print(f"[INFO] CSV読み込み: {len(df)}行")
            
            # 新しい列を追加
            df['oura_total_calories'] = None
            df['oura_estimated_basal'] = None
            df['total_calories_updated'] = df['消費カロリー_kcal'].copy()  # 既存値をバックアップ
            df['calculation_method'] = 'RENPHO+Oura'  # 現在の計算方式をマーク
            
            updated_count = 0
            failed_count = 0
            
            # 各行を処理
            for index, row in df.iterrows():
                date_str = str(row['date'])
                
                # 空データやNaNをスキップ
                if pd.isna(date_str) or date_str == 'nan':
                    continue
                
                # Ouraデータ取得
                oura_result = self.get_oura_calories_for_date(date_str)
                
                if 'success' in oura_result and oura_result['success']:
                    # Ouraデータで更新
                    df.at[index, 'oura_total_calories'] = oura_result['total_calories']
                    df.at[index, 'oura_estimated_basal'] = oura_result['estimated_basal']
                    df.at[index, 'total_calories_updated'] = oura_result['total_calories']
                    df.at[index, 'calculation_method'] = 'Oura_API'
                    
                    # 既存列も更新（オプション）
                    df.at[index, '消費カロリー_kcal'] = oura_result['total_calories']
                    df.at[index, '基礎代謝_kcal'] = oura_result['estimated_basal']
                    df.at[index, '活動カロリー_kcal'] = oura_result['active_calories']
                    
                    updated_count += 1
                    print(f"[UPDATE] {date_str}: {oura_result['total_calories']} kcal")
                else:
                    failed_count += 1
                    print(f"[FAILED] {date_str}: {oura_result.get('error', '不明なエラー')}")
            
            # 更新されたCSVを保存
            df.to_csv(csv_path, index=False)
            
            result = {
                'success': True,
                'csv_path': csv_path,
                'backup_path': backup_path if backup else None,
                'total_rows': len(df),
                'updated_count': updated_count,
                'failed_count': failed_count,
                'improvement_summary': self._calculate_improvement_summary(df)
            }
            
            print(f"[SUCCESS] CSV更新完了")
            print(f"  - 更新行数: {updated_count}")
            print(f"  - 失敗行数: {failed_count}")
            print(f"  - 総行数: {len(df)}")
            
            return result
            
        except Exception as e:
            return {'error': f'CSV更新エラー: {str(e)}'}
    
    def _calculate_improvement_summary(self, df: pd.DataFrame) -> dict:
        """改善効果の要約を計算"""
        try:
            # Oura更新されたデータのみ抽出
            oura_updated = df[df['calculation_method'] == 'Oura_API'].copy()
            
            if len(oura_updated) == 0:
                return {'no_oura_data': True}
            
            # 改善効果計算
            improvement_per_day = (oura_updated['total_calories_updated'] - 
                                 oura_updated['total_calories_updated'].shift(1)).fillna(0)
            
            # 最新データでの改善効果（例: 8/9データ）
            latest_data = oura_updated.tail(1)
            
            if len(latest_data) > 0:
                latest_total = latest_data['total_calories_updated'].iloc[0]
                latest_oura_basal = latest_data['oura_estimated_basal'].iloc[0]
                latest_active = latest_data['活動カロリー_kcal'].iloc[0]
                
                return {
                    'updated_dates_count': len(oura_updated),
                    'latest_total_calories': latest_total,
                    'latest_estimated_basal': latest_oura_basal,
                    'latest_active_calories': latest_active,
                    'calculation_method': 'Oura API v2 Integration'
                }
            
            return {'summary_calculation_failed': True}
            
        except Exception as e:
            return {'summary_error': str(e)}
    
    def run_full_update(self) -> dict:
        """完全な更新プロセスを実行"""
        print("=== Oura Ring総消費カロリー統合実装開始 ===")
        
        # 日次データCSV更新
        daily_csv_path = str(self.reports_dir / "日次データ.csv")
        
        if not Path(daily_csv_path).exists():
            return {'error': f'日次データCSVが見つかりません: {daily_csv_path}'}
        
        print(f"\n1. 日次データCSV更新開始")
        daily_result = self.update_csv_with_oura_calories(daily_csv_path)
        
        if 'error' in daily_result:
            return daily_result
        
        # 7日移動平均データCSV更新
        avg_csv_path = str(self.reports_dir / "7日移動平均データ.csv")
        
        print(f"\n2. 7日移動平均データCSV更新開始")
        if Path(avg_csv_path).exists():
            avg_result = self.update_csv_with_oura_calories(avg_csv_path)
        else:
            avg_result = {'skipped': '7日移動平均データCSVが見つかりません'}
        
        return {
            'success': True,
            'daily_csv_result': daily_result,
            'average_csv_result': avg_result,
            'implementation_completed': True
        }


def main():
    """メイン実行関数"""
    updater = OuraCalorieUpdater()
    
    # 実装確認
    print("Oura Ring総消費カロリー統合を開始しますか？")
    print("この操作により、CSVデータが更新されます（バックアップは自動作成）")
    
    # テスト実行（実際は確認待ち）
    result = updater.run_full_update()
    
    if 'error' in result:
        print(f"[ERROR] 実装失敗: {result['error']}")
        return
    
    print(f"\n=== 実装完了サマリー ===")
    
    # 日次データ結果
    daily = result['daily_csv_result']
    print(f"日次データ更新: {daily['updated_count']}行更新 / {daily['total_rows']}行")
    
    # 7日移動平均データ結果
    avg = result['average_csv_result']
    if 'updated_count' in avg:
        print(f"7日移動平均データ更新: {avg['updated_count']}行更新")
    else:
        print(f"7日移動平均データ: {avg.get('skipped', 'スキップ')}")
    
    # 改善効果
    improvement = daily.get('improvement_summary', {})
    if 'updated_dates_count' in improvement:
        print(f"\n=== 改善効果 ===")
        print(f"Oura API統合日数: {improvement['updated_dates_count']}日")
        print(f"最新総消費カロリー: {improvement['latest_total_calories']} kcal")
        print(f"最新推定基礎代謝: {improvement['latest_estimated_basal']} kcal")
        print(f"計算方式: {improvement['calculation_method']}")
    
    print(f"\n[SUCCESS] Oura Ring総消費カロリー統合実装完了！")


if __name__ == "__main__":
    main()
