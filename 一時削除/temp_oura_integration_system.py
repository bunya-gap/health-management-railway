"""
Oura Ring総消費カロリー統合モジュール
既存システムへの統合実装
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
import json

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from temp_oura_api_client import OuraAPIClient


class OuraTotalCaloriesIntegrator:
    """Oura Ring総消費カロリーをシステムに統合"""
    
    def __init__(self):
        self.oura_client = OuraAPIClient()
        
    def get_total_calories_for_integration(self, date: str) -> Optional[Dict]:
        """
        システム統合用の総消費カロリーデータを取得
        
        Args:
            date: 対象日 (YYYY-MM-DD)
            
        Returns:
            統合用データ辞書 {
                'date': 日付,
                'total_calories': 総消費カロリー,
                'active_calories': 活動カロリー,
                'calculated_basal': 推定基礎代謝,
                'source': データソース,
                'integration_notes': 統合時の注意事項
            }
        """
        if not self.oura_client.enabled:
            return None
            
        calories_data = self.oura_client.get_total_calories_for_date(date)
        
        if not calories_data:
            return None
            
        # 総消費カロリーから基礎代謝を逆算
        total_calories = calories_data.get('total_calories')
        active_calories = calories_data.get('active_calories')
        
        calculated_basal = None
        if total_calories and active_calories:
            calculated_basal = total_calories - active_calories
            
        integration_data = {
            'date': date,
            'total_calories': total_calories,
            'active_calories': active_calories,
            'calculated_basal': calculated_basal,
            'source': 'Oura Ring API v2',
            'integration_notes': f'Oura直接取得。推定基礎代謝={calculated_basal}kcal'
        }
        
        print(f"[SUCCESS] Oura総消費カロリー統合データ取得: {date}")
        print(f"  - 総消費: {total_calories} kcal")
        print(f"  - 活動: {active_calories} kcal")
        print(f"  - 推定基礎代謝: {calculated_basal} kcal")
        
        return integration_data
    
    def compare_with_current_calculation(self, date: str) -> Dict:
        """
        現在のシステム計算値とOuraデータを比較
        
        Args:
            date: 対象日 (YYYY-MM-DD)
            
        Returns:
            比較結果データ
        """
        oura_data = self.get_total_calories_for_integration(date)
        
        if not oura_data:
            return {'error': 'Ouraデータ取得失敗'}
            
        # 現在のシステム計算値（サンプル：実際は既存システムから取得）
        current_calculation = {
            'renpho_basal': 1490,  # RENPHO基礎代謝
            'oura_active': 909.5,  # Oura活動カロリー
            'total_current': 1490 + 909.5  # 現在の総消費カロリー
        }
        
        comparison = {
            'date': date,
            'current_system': current_calculation,
            'oura_direct': oura_data,
            'difference': {
                'total_calories_diff': oura_data['total_calories'] - current_calculation['total_current'],
                'active_calories_diff': oura_data['active_calories'] - current_calculation['oura_active'],
                'basal_comparison': {
                    'renpho_basal': current_calculation['renpho_basal'],
                    'oura_calculated_basal': oura_data['calculated_basal'],
                    'basal_diff': oura_data['calculated_basal'] - current_calculation['renpho_basal'] if oura_data['calculated_basal'] else None
                }
            },
            'recommendation': self._generate_recommendation(oura_data, current_calculation)
        }
        
        return comparison
    
    def _generate_recommendation(self, oura_data: Dict, current_calculation: Dict) -> str:
        """統合推奨方式を生成"""
        total_diff = oura_data['total_calories'] - current_calculation['total_current']
        
        if abs(total_diff) > 400:  # 400kcal以上の差異
            return "変更案A: Oura総消費カロリー完全採用（大幅な精度向上期待）"
        elif abs(total_diff) > 200:  # 200kcal以上の差異
            return "変更案B: Oura安静時+活動カロリーの透明計算（中程度改善）"
        else:
            return "現在の計算方式継続（差異が小さく変更不要）"
    
    def update_csv_with_oura_total_calories(self, csv_file_path: str, date_column: str = 'date') -> bool:
        """
        CSVファイルの総消費カロリーをOuraデータで更新
        
        Args:
            csv_file_path: 更新対象CSVファイルパス
            date_column: 日付カラム名
            
        Returns:
            更新成功フラグ
        """
        try:
            # CSVを読み込み
            df = pd.read_csv(csv_file_path)
            print(f"[INFO] CSV読み込み: {len(df)}行")
            
            # 新しいカラム追加
            df['oura_total_calories'] = None
            df['oura_calculated_basal'] = None
            df['total_calories_updated'] = df.get('total_calories', 0)  # 既存値をバックアップ
            
            updated_count = 0
            
            # 各行のOuraデータを取得・更新
            for index, row in df.iterrows():
                date_str = row[date_column]
                
                # 日付形式を統一（YYYY-MM-DD）
                try:
                    if isinstance(date_str, str):
                        # 既に正しい形式の場合はそのまま
                        if len(date_str) == 10 and date_str.count('-') == 2:
                            formatted_date = date_str
                        else:
                            # その他の形式の場合は変換
                            date_obj = pd.to_datetime(date_str)
                            formatted_date = date_obj.strftime('%Y-%m-%d')
                    else:
                        date_obj = pd.to_datetime(date_str)
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                except:
                    print(f"[WARNING] 日付変換失敗: {date_str}")
                    continue
                
                # Ouraデータ取得
                oura_data = self.get_total_calories_for_integration(formatted_date)
                
                if oura_data:
                    df.at[index, 'oura_total_calories'] = oura_data['total_calories']
                    df.at[index, 'oura_calculated_basal'] = oura_data['calculated_basal']
                    df.at[index, 'total_calories_updated'] = oura_data['total_calories']
                    updated_count += 1
                    
                    print(f"[UPDATE] {formatted_date}: {oura_data['total_calories']} kcal")
            
            # 更新されたCSVを保存
            backup_path = csv_file_path.replace('.csv', '_backup_before_oura_integration.csv')
            df_original = pd.read_csv(csv_file_path)
            df_original.to_csv(backup_path, index=False)
            print(f"[BACKUP] 元データバックアップ: {backup_path}")
            
            df.to_csv(csv_file_path, index=False)
            print(f"[SUCCESS] CSV更新完了: {updated_count}行更新")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] CSV更新エラー: {e}")
            return False


def test_integration():
    """統合テスト実行"""
    integrator = OuraTotalCaloriesIntegrator()
    
    print("=== Oura総消費カロリー統合テスト ===")
    
    # 1. 8/9データの統合テスト
    test_date = "2025-08-09"
    integration_data = integrator.get_total_calories_for_integration(test_date)
    
    if integration_data:
        print(f"\n=== {test_date} 統合データ取得成功 ===")
        print(f"総消費カロリー: {integration_data['total_calories']} kcal")
        print(f"活動カロリー: {integration_data['active_calories']} kcal")
        print(f"推定基礎代謝: {integration_data['calculated_basal']} kcal")
        print(f"データソース: {integration_data['source']}")
        print(f"統合メモ: {integration_data['integration_notes']}")
    
    # 2. 現在システムとの比較
    print(f"\n=== {test_date} システム比較分析 ===")
    comparison = integrator.compare_with_current_calculation(test_date)
    
    if 'error' not in comparison:
        current = comparison['current_system']
        oura = comparison['oura_direct']
        diff = comparison['difference']
        
        print(f"現在システム: {current['total_current']} kcal")
        print(f"Oura直接取得: {oura['total_calories']} kcal")
        print(f"差異: {diff['total_calories_diff']:+.1f} kcal")
        print(f"推奨方式: {comparison['recommendation']}")
        
        print(f"\n=== 基礎代謝比較 ===")
        print(f"RENPHO基礎代謝: {current['renpho_basal']} kcal")
        print(f"Oura推定基礎代謝: {oura['calculated_basal']} kcal")
        print(f"基礎代謝差異: {diff['basal_comparison']['basal_diff']:+.1f} kcal")


if __name__ == "__main__":
    test_integration()
