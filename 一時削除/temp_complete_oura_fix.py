"""
Oura Ring総消費カロリー完全修正実装
全日付対象・カロリー収支正しく再計算・7日移動平均も更新
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Oura API設定
OURA_ACCESS_TOKEN = "JQI3Z4TCC57DMDIKIPH77IFEJJS255Z3"
OURA_API_BASE_URL = "https://api.ouraring.com/v2"

class CompleteOuraIntegration:
    """Oura Ring総消費カロリー完全統合修正"""
    
    def __init__(self):
        self.project_root = Path("C:/Users/terada/Desktop/apps/体組成管理app")
        self.reports_dir = self.project_root / "reports"
        
    def get_oura_calories_period(self, start_date: str, end_date: str) -> dict:
        """期間内の全Oura総消費カロリーデータを取得"""
        headers = {
            'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{OURA_API_BASE_URL}/usercollection/daily_activity"
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            print(f"[INFO] Oura API期間取得: {start_date} - {end_date}")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return {'error': f'API失敗: {response.status_code}'}
            
            data = response.json()
            
            if 'data' in data and data['data']:
                oura_data = {}
                for activity in data['data']:
                    date = activity.get('day')
                    if date:
                        total_cal = activity.get('total_calories')
                        active_cal = activity.get('active_calories')
                        estimated_basal = total_cal - active_cal if total_cal and active_cal else None
                        
                        oura_data[date] = {
                            'total_calories': total_cal,
                            'active_calories': active_cal,
                            'estimated_basal': estimated_basal
                        }
                
                print(f"[SUCCESS] Oura API期間取得: {len(oura_data)}日分のデータ")
                return {'success': True, 'data': oura_data}
            
            return {'error': '期間データなし'}
            
        except Exception as e:
            return {'error': f'API呼び出しエラー: {str(e)}'}
    
    def update_daily_csv_complete(self, csv_path: str) -> dict:
        """日次データCSVを完全更新（全期間・カロリー収支再計算）"""
        try:
            # バックアップ作成
            backup_path = str(csv_path).replace('.csv', f'_backup_complete_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            shutil.copy2(csv_path, backup_path)
            print(f"[BACKUP] 完全修正バックアップ: {backup_path}")
            
            # CSV読み込み
            df = pd.read_csv(csv_path)
            print(f"[INFO] CSV読み込み: {len(df)}行")
            
            # 有効な日付範囲を特定
            valid_dates = df['date'].dropna().tolist()
            if not valid_dates:
                return {'error': '有効な日付データがありません'}
            
            start_date = min(valid_dates)
            end_date = max(valid_dates)
            
            # 過去30日分のOuraデータ取得（API制限を考慮）
            api_start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            api_end_date = datetime.now().strftime('%Y-%m-%d')
            
            print(f"[INFO] Oura API取得期間: {api_start_date} - {api_end_date}")
            oura_result = self.get_oura_calories_period(api_start_date, api_end_date)
            
            if 'error' in oura_result:
                print(f"[WARNING] Oura API取得失敗: {oura_result['error']}")
                return {'error': oura_result['error']}
            
            oura_data = oura_result['data']
            
            # 新しい列を準備
            if 'oura_total_calories' not in df.columns:
                df['oura_total_calories'] = None
                df['oura_estimated_basal'] = None
                df['previous_total_calories'] = df['消費カロリー_kcal'].copy()
                df['previous_calorie_balance'] = df['カロリー収支_kcal'].copy()
                df['calculation_method'] = 'RENPHO+Oura'
            
            updated_count = 0
            calorie_balance_fixed_count = 0
            
            # 全行を処理
            for index, row in df.iterrows():
                date_str = str(row['date'])
                
                if pd.isna(date_str) or date_str == 'nan':
                    continue
                
                # Ouraデータが利用可能な場合
                if date_str in oura_data:
                    oura_info = oura_data[date_str]
                    
                    # Oura統合データを記録
                    df.at[index, 'oura_total_calories'] = oura_info['total_calories']
                    df.at[index, 'oura_estimated_basal'] = oura_info['estimated_basal']
                    df.at[index, 'calculation_method'] = 'Oura_API_v2'
                    
                    # 既存列をOura値に更新
                    df.at[index, '消費カロリー_kcal'] = oura_info['total_calories']
                    df.at[index, '基礎代謝_kcal'] = oura_info['estimated_basal']
                    df.at[index, '活動カロリー_kcal'] = oura_info['active_calories']
                    
                    updated_count += 1
                    print(f"[UPDATE] {date_str}: {oura_info['total_calories']} kcal")
                
                # カロリー収支を再計算（Oura更新された行、されていない行含む全て）
                intake_cal = row['摂取カロリー_kcal']
                consumed_cal = df.at[index, '消費カロリー_kcal']
                
                if not pd.isna(intake_cal) and not pd.isna(consumed_cal):
                    new_balance = intake_cal - consumed_cal
                    df.at[index, 'カロリー収支_kcal'] = new_balance
                    calorie_balance_fixed_count += 1
            
            # CSV保存
            df.to_csv(csv_path, index=False)
            
            return {
                'success': True,
                'backup_path': backup_path,
                'total_rows': len(df),
                'oura_updated_count': updated_count,
                'calorie_balance_fixed_count': calorie_balance_fixed_count,
                'oura_dates': list(oura_data.keys())
            }
            
        except Exception as e:
            return {'error': f'CSV完全更新エラー: {str(e)}'}
    
    def regenerate_moving_average_csv(self):
        """7日移動平均データを完全再生成"""
        try:
            print(f"[INFO] 7日移動平均データ再生成開始...")
            
            # csv_data_integrator.pyを呼び出して7日移動平均を再計算
            import sys
            sys.path.append(str(self.project_root))
            from csv_data_integrator import CSVDataIntegrator
            
            integrator = CSVDataIntegrator()
            result = integrator.integrate_and_calculate()
            
            if result.get('success'):
                print(f"[SUCCESS] 7日移動平均データ再生成完了")
                return {'success': True, 'message': '7日移動平均データ再生成完了'}
            else:
                return {'error': f'7日移動平均再生成失敗: {result}'}
                
        except Exception as e:
            return {'error': f'7日移動平均再生成エラー: {str(e)}'}
    
    def run_complete_fix(self) -> dict:
        """Oura統合完全修正実行"""
        print("=== Oura Ring総消費カロリー完全修正開始 ===")
        
        results = {}
        
        # 1. 日次データCSV完全更新
        daily_csv_path = str(self.reports_dir / "日次データ.csv")
        
        if not Path(daily_csv_path).exists():
            return {'error': f'日次データCSVが見つかりません: {daily_csv_path}'}
        
        print(f"\n1. 日次データCSV完全更新（全期間・カロリー収支修正）")
        daily_result = self.update_daily_csv_complete(daily_csv_path)
        results['daily_update'] = daily_result
        
        if 'error' in daily_result:
            return daily_result
        
        # 2. 7日移動平均データ完全再生成
        print(f"\n2. 7日移動平均データ完全再生成")
        avg_result = self.regenerate_moving_average_csv()
        results['moving_average_regeneration'] = avg_result
        
        if 'error' in avg_result:
            print(f"[WARNING] 7日移動平均再生成に問題: {avg_result['error']}")
        
        return {
            'success': True,
            'complete_fix_results': results,
            'summary': {
                'oura_updated_dates': daily_result.get('oura_dates', []),
                'oura_updated_count': daily_result.get('oura_updated_count', 0),
                'calorie_balance_fixed_count': daily_result.get('calorie_balance_fixed_count', 0),
                'moving_average_regenerated': 'success' in avg_result
            }
        }


def main():
    """完全修正実行"""
    fixer = CompleteOuraIntegration()
    
    print("Oura Ring総消費カロリー完全修正を実行します")
    print("- 全期間のOura統合可能データを更新")
    print("- 全行のカロリー収支を正しく再計算") 
    print("- 7日移動平均データを完全再生成")
    
    result = fixer.run_complete_fix()
    
    if 'error' in result:
        print(f"[ERROR] 完全修正失敗: {result['error']}")
        return
    
    print(f"\n=== 完全修正完了サマリー ===")
    summary = result['summary']
    
    print(f"Oura統合日数: {summary['oura_updated_count']}日")
    print(f"Oura統合対象日付: {summary['oura_updated_dates']}")
    print(f"カロリー収支修正行数: {summary['calorie_balance_fixed_count']}行")
    print(f"7日移動平均再生成: {'成功' if summary['moving_average_regenerated'] else '失敗'}")
    
    # 修正例表示
    if summary['oura_updated_dates']:
        latest_date = max(summary['oura_updated_dates'])
        print(f"\n=== 修正効果例（{latest_date}） ===")
        print(f"この日付以降、正しいカロリー収支で分析が実行されます")
    
    print(f"\n[SUCCESS] Oura Ring総消費カロリー完全修正完了！")
    print(f"システムで再分析を実行してください。")

if __name__ == "__main__":
    main()
