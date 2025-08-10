"""
リッチ分析システム提案 - 現在の分析を大幅強化
19カラムデータをフル活用した包括的健康分析エンジン

現在の制限:
- 体組成とカロリーのみ使用（2/19カテゴリ）
- 短期トレンド分析のみ
- 予測・推奨機能なし

提案システム:
- 全19カラムデータ活用（100%データ利用）
- 多次元統合分析
- AIトレンド予測
- パーソナライズド推奨
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json

class RichHealthAnalytics:
    """リッチ健康分析エンジン - 全データ活用版"""
    
    def __init__(self, data_file: str = "reports/日次データ.csv"):
        self.data_file = data_file
        
    def load_comprehensive_data(self) -> pd.DataFrame:
        """19カラム全データ読み込み"""
        df = pd.read_csv(self.data_file, encoding='utf-8-sig')
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date')
        
    def analyze_comprehensive_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """包括的健康分析（全19指標活用）"""
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': self._get_data_summary(df),
            
            # 現在の分析（継続）
            'body_composition': self._analyze_body_composition(df),
            'calorie_analysis': self._analyze_calories(df),
            
            # 新規分析（大幅強化）
            'activity_analysis': self._analyze_activity_patterns(df),
            'sleep_analysis': self._analyze_sleep_quality(df),
            'body_temperature': self._analyze_body_temperature(df),
            'nutrition_analysis': self._analyze_nutrition_balance(df),
            
            # 統合分析
            'wellness_score': self._calculate_wellness_score(df),
            'trend_predictions': self._predict_trends(df),
            'personalized_recommendations': self._generate_recommendations(df),
            
            # アラート・注意喚起
            'health_alerts': self._check_health_alerts(df),
            'data_quality': self._assess_data_quality(df)
        }
        
        return analysis
        
    def _get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """データ概要統計"""
        return {
            'total_days': len(df),
            'data_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            },
            'data_completeness': {
                col: f"{(~df[col].isna()).sum()}/{len(df)} ({((~df[col].isna()).sum()/len(df)*100):.1f}%)"
                for col in df.columns if col != 'date'
            }
        }
        
    def _analyze_body_composition(self, df: pd.DataFrame) -> Dict[str, Any]:
        """体組成分析（現在の機能継続・強化）"""
        latest = df.iloc[-1]
        first_valid = df.dropna(subset=['体重_kg']).iloc[0] if not df.dropna(subset=['体重_kg']).empty else latest
        
        return {
            'current_metrics': {
                'weight': latest.get('体重_kg', 0),
                'body_fat_rate': latest.get('体脂肪率', 0),
                'muscle_mass': latest.get('筋肉量_kg', 0),
                'body_fat_mass': latest.get('体脂肪量_kg', 0)
            },
            'total_changes': {
                'weight_change': latest.get('体重_kg', 0) - first_valid.get('体重_kg', 0),
                'body_fat_change': latest.get('体脂肪率', 0) - first_valid.get('体脂肪率', 0),
                'muscle_change': latest.get('筋肉量_kg', 0) - first_valid.get('筋肉量_kg', 0)
            },
            'composition_ratios': {
                'muscle_to_weight': (latest.get('筋肉量_kg', 0) / latest.get('体重_kg', 1