"""
Oura Ring総消費カロリー直接統合システム
APIレスポンスを直接処理
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))
from oura_config import OURA_ACCESS_TOKEN, OURA_API_BASE_URL


class DirectOuraIntegrator:
    """Oura Ring APIから直接データを取得して統合"""
    
    def __init__(self):
        self.access_token = OURA_ACCESS_TOKEN
        self.base_url = OURA_API_BASE_URL
        
    def get_oura_total_calories(self, date: str) -> dict:
        """
        指定日のOura総消費カロリーを直接取得
        
        Args:
            date: 対象日 (YYYY-MM-DD)
            
        Returns:
            結果辞書
        """
        if not self.access_token:
            return {'error': 'Oura APIトークンが設定されていません'}
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Daily Activity API呼び出し
            url = f"{self.base_url}/usercollection/daily_activity"
            params = {'start_date': date}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return {
                    'error': f'API呼び出し失敗: {response.status_code}',
                    'response': response.text
                }
            
            data = response.json()
            
            # 該当日のデータを検索
            if 'data' in data and data['data']:
                for activity in data['data']:
                    if activity.get('day') == date:
                        return {
                            'success': True,
                            'date': date,
                            'total_calories': activity.get('total_calories'),
                            'active_calories': activity.get('active_calories'),
                            'rest_calories': activity.get('rest_calories'),
                            'steps': activity.get('steps'),
                            'score': activity.get('score')
                        }
            
            return {'error': f'{date}のデータが見つかりません'}
            
        except Exception as e:
            return {'error': f'API呼び出しエラー: {str(e)}'}
    
    def compare_calculation_methods(self, date: str) -> dict:
        """
        計算方式の比較分析
        
        Args:
            date: 対象日 (YYYY-MM-DD)
            
        Returns:
            比較分析結果
        """
        oura_result = self.get_oura_total_calories(date)
        
        if 'error' in oura_result:
            return oura_result
            
        # 現在のシステム計算（サンプル値）
        current_system = {
            'renpho_basal': 1490,  # RENPHO基礎代謝
            'oura_active': 909.5,  # Oura活動カロリー（既存）
            'total_current': 1490 + 909.5  # 現在の総消費
        }
        
        # Oura推定基礎代謝を計算
        oura_calculated_basal = None
        if oura_result['total_calories'] and oura_result['active_calories']:
            oura_calculated_basal = oura_result['total_calories'] - oura_result['active_calories']
        
        # 差異計算
        total_diff = oura_result['total_calories'] - current_system['total_current']
        active_diff = oura_result['active_calories'] - current_system['oura_active']
        basal_diff = oura_calculated_basal - current_system['renpho_basal'] if oura_calculated_basal else None
        
        return {
            'date': date,
            'current_system': current_system,
            'oura_data': oura_result,
            'calculated_values': {
                'oura_estimated_basal': oura_calculated_basal
            },
            'differences': {
                'total_calories_diff': total_diff,
                'active_calories_diff': active_diff,
                'basal_calories_diff': basal_diff
            },
            'analysis': {
                'total_diff_percentage': (total_diff / current_system['total_current']) * 100,
                'recommendation': self._get_recommendation(total_diff),
                'impact_level': self._get_impact_level(abs(total_diff))
            }
        }
    
    def _get_recommendation(self, total_diff: float) -> str:
        """推奨変更方式を決定"""
        if abs(total_diff) > 400:
            return "変更案A: Oura総消費カロリー完全採用（大幅改善）"
        elif abs(total_diff) > 200:
            return "変更案B: Oura基礎代謝+活動カロリーで透明計算（中程度改善）"
        else:
            return "現在方式継続（差異小さく変更不要）"
    
    def _get_impact_level(self, abs_diff: float) -> str:
        """影響度レベルを判定"""
        if abs_diff > 500:
            return "重大（500kcal以上）"
        elif abs_diff > 300:
            return "大（300-500kcal）"
        elif abs_diff > 100:
            return "中（100-300kcal）"
        else:
            return "小（100kcal未満）"


def run_comprehensive_test():
    """包括的テスト実行"""
    integrator = DirectOuraIntegrator()
    
    print("=== Oura Ring総消費カロリー統合分析 ===")
    
    # テスト日付
    test_date = "2025-08-09"
    
    # 1. Oura APIデータ直接取得
    print(f"\n1. {test_date} Oura APIデータ取得")
    oura_data = integrator.get_oura_total_calories(test_date)
    
    if 'error' in oura_data:
        print(f"[ERROR] {oura_data['error']}")
        return
    
    print(f"[SUCCESS] Ouraデータ取得成功")
    print(f"  - 総消費カロリー: {oura_data['total_calories']} kcal")
    print(f"  - 活動カロリー: {oura_data['active_calories']} kcal")
    print(f"  - 歩数: {oura_data['steps']:,} 歩")
    print(f"  - スコア: {oura_data['score']}")
    
    # 2. システム比較分析
    print(f"\n2. システム計算方式比較分析")
    comparison = integrator.compare_calculation_methods(test_date)
    
    if 'error' in comparison:
        print(f"[ERROR] {comparison['error']}")
        return
    
    current = comparison['current_system']
    oura = comparison['oura_data']
    calc = comparison['calculated_values']
    diff = comparison['differences']
    analysis = comparison['analysis']
    
    print(f"\n=== 現在システム ===")
    print(f"RENPHO基礎代謝: {current['renpho_basal']} kcal")
    print(f"Oura活動カロリー: {current['oura_active']} kcal")
    print(f"総消費カロリー: {current['total_current']} kcal")
    
    print(f"\n=== Oura Ring直接取得 ===")
    print(f"Oura総消費カロリー: {oura['total_calories']} kcal")
    print(f"Oura活動カロリー: {oura['active_calories']} kcal")
    print(f"Oura推定基礎代謝: {calc['oura_estimated_basal']} kcal")
    
    print(f"\n=== 差異分析 ===")
    print(f"総消費カロリー差異: {diff['total_calories_diff']:+.1f} kcal ({analysis['total_diff_percentage']:+.1f}%)")
    print(f"活動カロリー差異: {diff['active_calories_diff']:+.1f} kcal")
    print(f"基礎代謝差異: {diff['basal_calories_diff']:+.1f} kcal")
    
    print(f"\n=== 分析結果 ===")
    print(f"影響度: {analysis['impact_level']}")
    print(f"推奨変更: {analysis['recommendation']}")
    
    # 3. ユーザー報告値との照合
    print(f"\n3. ユーザー報告値との照合")
    user_reported = {
        'total_calories': 2878,
        'active_calories': 910
    }
    
    total_match = oura['total_calories'] == user_reported['total_calories']
    active_match = oura['active_calories'] == user_reported['active_calories']
    
    print(f"総消費カロリー: API {oura['total_calories']} vs 報告 {user_reported['total_calories']} {'✓' if total_match else '✗'}")
    print(f"活動カロリー: API {oura['active_calories']} vs 報告 {user_reported['active_calories']} {'✓' if active_match else '✗'}")
    
    if total_match and active_match:
        print(f"[VERIFIED] ユーザー報告値とAPI取得値が完全一致！")
    
    # 4. 統合推奨事項
    print(f"\n4. 統合推奨事項")
    
    if analysis['impact_level'] in ['重大', '大']:
        print(f"🔥 即座統合推奨: {diff['total_calories_diff']:+.1f}kcalの改善効果")
        print(f"   - 方法: {analysis['recommendation']}")
        print(f"   - 効果: より正確な総消費カロリー算出")
        print(f"   - 実装: CSV更新 + 計算式変更")
    else:
        print(f"⚖️ 統合検討: 改善効果は{analysis['impact_level']}")


if __name__ == "__main__":
    run_comprehensive_test()
