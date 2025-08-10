"""
CSV Data Integrator - HAEデータを既存CSVに統合
8/9以降のデータ追加・移動平均再計算機能
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import os
from hae_data_converter import HAEDataConverter

class CSVDataIntegrator:
    """HAEデータを既存CSVに統合するクラス"""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.converter = HAEDataConverter()
        
        # CSVファイルパス
        self.daily_csv = self.reports_dir / "日次データ.csv"
        self.ma7_csv = self.reports_dir / "7日移動平均データ.csv"
        self.index_csv = self.reports_dir / "インデックスデータ.csv"
        
    def is_data_boundary_date(self, target_date: str) -> bool:
        """8/9以降のデータかチェック
        
        Args:
            target_date: "2025-08-09" 形式
            
        Returns:
            True: HAEデータ使用, False: XMLデータ使用
        """
        boundary_date = date(2025, 8, 9)
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        return target >= boundary_date
        
    def load_existing_csv(self, csv_path: Path) -> pd.DataFrame:
        """既存CSVファイルを読み込み"""
        if not csv_path.exists():
            print(f"[WARNING] CSVファイルが見つかりません: {csv_path.name}")
            return pd.DataFrame()
            
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            print(f"[INFO] CSV読み込み完了: {csv_path.name} ({len(df)}行)")
            return df
        except Exception as e:
            print(f"[ERROR] CSV読み込みエラー: {e}")
            return pd.DataFrame()
            
    def check_data_exists(self, df: pd.DataFrame, target_date: str) -> bool:
        """指定日のデータが既に存在するかチェック"""
        if df.empty:
            return False
        return target_date in df['date'].values
        
    def add_hae_data_to_csv(self, hae_row: dict, include_oura: bool = True) -> bool:
        """HAEデータを既存CSVに追加
        
        Args:
            hae_row: 変換済みHAEデータ
            include_oura: Oura体表温データを取得するか
            
        Returns:
            成功: True, 失敗: False
        """
        target_date = hae_row.get('date')
        if not target_date:
            print("[ERROR] 日付データが見つかりません")
            return False
            
        print(f"[INFO] データ追加開始: {target_date}")
        
        # データ境界チェック
        if not self.is_data_boundary_date(target_date):
            print(f"[WARNING] {target_date}はXMLデータ期間です（8/9以前）")
            return False
            
        # 既存データ読み込み
        daily_df = self.load_existing_csv(self.daily_csv)
        
        if daily_df.empty:
            print("[ERROR] 既存の日次データが見つかりません")
            return False
            
        # 重複チェック
        if self.check_data_exists(daily_df, target_date):
            print(f"[WARNING] {target_date}のデータは既に存在します。上書きします。")
            # 既存行を削除
            daily_df = daily_df[daily_df['date'] != target_date]
            
        # Oura体表温データを統合（オプション）
        if include_oura:
            oura_data = self.get_oura_temperature_data(target_date)
            if oura_data:
                hae_row.update(oura_data)
                
        # 新しい行を追加
        new_row = pd.DataFrame([hae_row])
        updated_df = pd.concat([daily_df, new_row], ignore_index=True)
        
        # 日付でソート
        updated_df['date'] = pd.to_datetime(updated_df['date'])
        updated_df = updated_df.sort_values('date')
        updated_df['date'] = updated_df['date'].dt.strftime('%Y-%m-%d')
        
        # CSV保存
        try:
            updated_df.to_csv(self.daily_csv, index=False, encoding='utf-8-sig')
            print(f"[SUCCESS] 日次データ更新完了: {len(updated_df)}行")
            
            # 移動平均再計算
            self.recalculate_moving_averages(updated_df)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] CSV保存エラー: {e}")
            return False
            
    def recalculate_moving_averages(self, daily_df: pd.DataFrame):
        """7日移動平均を全体再計算"""
        print("[INFO] 7日移動平均再計算開始...")
        
        try:
            ma_df = daily_df.copy()
            
            # 数値カラムのみ対象
            numeric_cols = [col for col in daily_df.columns 
                          if col != 'date' and daily_df[col].dtype in ['float64', 'int64']]
            
            # 7日・14日・28日移動平均計算
            for col in numeric_cols:
                # 7日移動平均
                ma_df[f'{col}_ma7'] = ma_df[col].rolling(
                    window=7, min_periods=1, center=False
                ).mean().round(2)
                
                # 14日移動平均
                ma_df[f'{col}_ma14'] = ma_df[col].rolling(
                    window=14, min_periods=1, center=False
                ).mean().round(2)
                
                # 28日移動平均
                ma_df[f'{col}_ma28'] = ma_df[col].rolling(
                    window=28, min_periods=1, center=False
                ).mean().round(2)
                
            # 移動平均CSV保存
            ma_df.to_csv(self.ma7_csv, index=False, encoding='utf-8-sig')
            print(f"[SUCCESS] 移動平均データ更新完了（7日・14日・28日）: {len(ma_df)}行")
            
            # インデックスデータ更新
            self.update_index_data(ma_df)
            
        except Exception as e:
            print(f"[ERROR] 移動平均計算エラー: {e}")
            
    def update_index_data(self, ma_df: pd.DataFrame):
        """インデックスデータを更新（既存ロジック使用）"""
        print("[INFO] インデックスデータ更新開始...")
        
        try:
            # 既存のcreate_index_data関数の簡略版
            # 実際は unified_processor.py の関数を呼び出し
            print("[INFO] インデックス計算は次版で実装予定")
            
        except Exception as e:
            print(f"[ERROR] インデックス更新エラー: {e}")
            
    def get_oura_temperature_data(self, target_date: str) -> dict:
        """Oura体表温データを取得（Oura Ring API活用）"""
        print(f"[INFO] Oura体表温データ取得: {target_date}")
        
        try:
            # oura_config.py をインポート
            try:
                import oura_config
            except ImportError:
                print("[WARNING] oura_config.py が見つかりません。体表温データをスキップします")
                return {
                    '体表温度_celsius': None,
                    '体表温変化_celsius': None,
                    '体表温偏差_celsius': None,
                    '体表温トレンド_celsius': None
                }
            
            # Oura設定チェック
            if not oura_config.is_oura_configured():
                print("[WARNING] Oura設定が未完了です。体表温データをスキップします")
                return {
                    '体表温度_celsius': None,
                    '体表温変化_celsius': None,
                    '体表温偏差_celsius': None,
                    '体表温トレンド_celsius': None
                }
            
            # Oura Ring APIから体表温データ取得
            import requests
            from datetime import datetime, timedelta
            
            # target_dateをdatetimeに変換
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # Daily Readiness APIエンドポイント  
            url = f"{oura_config.OURA_API_BASE_URL}/usercollection/daily_readiness"
            headers = {
                'Authorization': f'Bearer {oura_config.OURA_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            params = {
                'start_date': target_date,
                'end_date': target_date
            }
            
            print(f"[INFO] Oura APIから体表温データ取得中... ({target_date})")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            readiness_records = data.get('data', [])
            
            # 対象日のデータを検索
            temp_data = {
                '体表温度_celsius': None,
                '体表温変化_celsius': None,
                '体表温偏差_celsius': None,
                '体表温トレンド_celsius': None
            }
            
            for record in readiness_records:
                record_date = record.get('day')
                if record_date == target_date:
                    temp_data['体表温偏差_celsius'] = record.get('temperature_deviation')
                    temp_data['体表温トレンド_celsius'] = record.get('temperature_trend_deviation')
                    print(f"[SUCCESS] Oura体表温データ取得完了: {target_date}")
                    break
            else:
                print(f"[WARNING] 対象日のOura体表温データが見つかりません: {target_date}")
            
            return temp_data
            
        except Exception as e:
            print(f"[ERROR] Oura体表温データ取得エラー: {e}")
            return {
                '体表温度_celsius': None,
                '体表温変化_celsius': None,
                '体表温偏差_celsius': None,
                '体表温トレンド_celsius': None
            }
        
    def process_latest_hae_data(self) -> bool:
        """最新のHAEデータを処理して統合"""
        print("=== 最新HAEデータ統合処理 ===")
        
        # HAEデータ変換
        hae_row = self.converter.convert_hae_to_csv_row(
            self.converter.get_latest_hae_file()
        )
        
        if not hae_row:
            print("[ERROR] HAEデータ変換に失敗しました")
            return False
            
        # CSV統合
        return self.add_hae_data_to_csv(hae_row)
        
    def test_integration(self):
        """統合機能のテスト"""
        print("=== CSV統合テスト ===")
        
        # 現在のCSVファイル状況確認
        print(f"日次データ: {self.daily_csv.exists()} ({self.daily_csv})")
        print(f"移動平均データ: {self.ma7_csv.exists()} ({self.ma7_csv})")
        
        if self.daily_csv.exists():
            daily_df = self.load_existing_csv(self.daily_csv)
            if not daily_df.empty:
                last_date = daily_df['date'].iloc[-1]
                print(f"最終データ日付: {last_date}")
                
        # 最新HAEデータ統合テスト
        result = self.process_latest_hae_data()
        print(f"統合結果: {'成功' if result else '失敗'}")

if __name__ == "__main__":
    integrator = CSVDataIntegrator()
    integrator.test_integration()
