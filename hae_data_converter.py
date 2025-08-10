"""
HAE Data Converter - HAEデータをCSV形式に変換
8/9以降のメジャーアップデート用データ変換モジュール
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path

class HAEDataConverter:
    """HAEデータを既存CSV形式に変換するクラス"""
    
    # HAEメトリクス名 → CSVカラム名のマッピング
    METRIC_MAPPING = {
        'weight_body_mass': '体重_kg',
        'lean_body_mass': '筋肉量_kg', 
        'body_fat_percentage': '体脂肪率',
        'dietary_energy': '摂取カロリー_kcal',
        'basal_energy_burned': '基礎代謝_kcal',
        'active_energy': '活動カロリー_kcal',
        'step_count': '歩数',
        'sleep_analysis': '睡眠時間_hours',
        'protein': 'タンパク質_g',
        'carbohydrates': '糖質_g',
        'fiber': '食物繊維_g',
        'total_fat': '脂質_g'
    }
    
    def __init__(self, data_dir: str = "health_api_data"):
        self.data_dir = Path(data_dir)
        
    def get_latest_hae_file(self) -> Optional[Path]:
        """最新のHAEデータファイルを取得"""
        if not self.data_dir.exists():
            print(f"[ERROR] データディレクトリが見つかりません: {self.data_dir}")
            return None
            
        json_files = list(self.data_dir.glob("health_data_*.json"))
        
        if not json_files:
            print("[ERROR] HAEデータファイルが見つかりません")
            return None
            
        # 最新ファイルを選択（作成時刻基準）
        latest_file = max(json_files, key=lambda x: x.stat().st_ctime)
        print(f"[INFO] 最新HAEデータ: {latest_file.name}")
        return latest_file
        
    def parse_hae_date(self, date_str: str) -> str:
        """HAE日付形式をCSV形式に変換
        
        Args:
            date_str: "2025-07-31 00:00:00 +0900" 形式
            
        Returns:
            "2025-07-31" 形式
        """
        try:
            # タイムゾーン付き日付をパース
            dt = datetime.strptime(date_str.split(' +')[0], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"[ERROR] 日付変換エラー: {date_str} -> {e}")
            return date_str.split()[0]  # フォールバック
            
    def extract_metric_value(self, metric: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """メトリクスから値を抽出（累積処理対応版）"""
        name = metric.get('name', '')
        data_points = metric.get('data', [])
        
        if not data_points:
            return None
            
        # 累積処理が必要なメトリクス（分単位データを合計）
        cumulative_metrics = {
            'step_count', 'active_energy', 'basal_energy_burned',
            'dietary_energy', 'protein', 'carbohydrates', 'fiber', 'total_fat'
        }
        
        if name in cumulative_metrics:
            # 全データポイントを累積
            total_value = 0
            sample_date = None
            
            for point in data_points:
                qty = point.get('qty', 0)
                if qty is not None:
                    total_value += qty
                if sample_date is None:
                    sample_date = point.get('date', '')
                    
            print(f"[INFO] {name} 累積処理: {len(data_points)}個 → 合計 {total_value}")
            
            return {
                'name': name,
                'value': round(total_value, 1),
                'date': self.parse_hae_date(sample_date) if sample_date else '',
                'units': metric.get('units', ''),
                'source': f'HAE累積({len(data_points)}件)'
            }
        else:
            # 最新値使用（体重、体脂肪率等）
            latest_point = data_points[-1]
            
            return {
                'name': name,
                'value': latest_point.get('qty'),
                'date': self.parse_hae_date(latest_point.get('date', '')),
                'units': metric.get('units', ''),
                'source': latest_point.get('source', 'HAE')
            }
        
    def convert_hae_to_csv_row(self, hae_file: Path) -> Optional[Dict[str, Any]]:
        """HAE JSONファイルを1行のCSVデータに変換"""
        try:
            with open(hae_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            metrics = data.get('data', {}).get('metrics', [])
            
            if not metrics:
                print("[ERROR] メトリクスデータが見つかりません")
                return None
                
            # CSVカラム初期化
            csv_row = {col: None for col in [
                'date', '体重_kg', '筋肉量_kg', '体脂肪量_kg', '体脂肪率',
                'カロリー収支_kcal', '摂取カロリー_kcal', '消費カロリー_kcal',
                '基礎代謝_kcal', '活動カロリー_kcal', '歩数', '睡眠時間_hours',
                '体表温度_celsius', '体表温変化_celsius', '体表温偏差_celsius', '体表温トレンド_celsius',
                'タンパク質_g', '糖質_g', '食物繊維_g', '脂質_g'
            ]}
            
            # メトリクスデータを処理
            date_value = None
            weight_kg = None
            body_fat_rate = None
            intake_cal = None
            basal_cal = None
            active_cal = None
            
            for metric in metrics:
                extracted = self.extract_metric_value(metric)
                if not extracted:
                    continue
                    
                metric_name = extracted['name']
                value = extracted['value']
                date_value = extracted['date']  # 全メトリクス共通の日付
                
                # マッピングされているメトリクスを変換
                if metric_name in self.METRIC_MAPPING:
                    csv_column = self.METRIC_MAPPING[metric_name]
                    csv_row[csv_column] = value
                    
                    # 計算用に特別保存
                    if metric_name == 'weight_body_mass':
                        weight_kg = value
                    elif metric_name == 'body_fat_percentage':
                        body_fat_rate = value
                    elif metric_name == 'dietary_energy':
                        intake_cal = value
                    elif metric_name == 'basal_energy_burned':
                        basal_cal = value
                    elif metric_name == 'active_energy':
                        active_cal = value
                        
            # 日付設定
            csv_row['date'] = date_value
            
            # 計算項目
            if weight_kg and body_fat_rate:
                csv_row['体脂肪量_kg'] = round(weight_kg * (body_fat_rate / 100), 1)
                
            if basal_cal and active_cal:
                csv_row['消費カロリー_kcal'] = basal_cal + active_cal
                
            if intake_cal and csv_row['消費カロリー_kcal']:
                csv_row['カロリー収支_kcal'] = intake_cal - csv_row['消費カロリー_kcal']
                
            # Oura体表温データは別途取得（既存ロジック使用）
            csv_row['体表温度_celsius'] = None
            csv_row['体表温変化_celsius'] = None  
            csv_row['体表温偏差_celsius'] = None
            csv_row['体表温トレンド_celsius'] = None
            
            print(f"[SUCCESS] HAEデータ変換完了: {date_value}")
            return csv_row
            
        except Exception as e:
            print(f"[ERROR] HAEデータ変換エラー: {e}")
            return None
            
    def test_conversion(self):
        """変換機能のテスト"""
        print("=== HAEデータ変換テスト ===")
        
        latest_file = self.get_latest_hae_file()
        if not latest_file:
            return
            
        csv_row = self.convert_hae_to_csv_row(latest_file)
        if not csv_row:
            return
            
        print("\n=== 変換結果 ===")
        for key, value in csv_row.items():
            if value is not None:
                print(f"{key}: {value}")
                
        return csv_row

if __name__ == "__main__":
    converter = HAEDataConverter()
    converter.test_conversion()
