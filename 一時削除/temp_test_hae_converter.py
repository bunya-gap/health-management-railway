#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAEDataConverter実行テスト
"""

import sys
sys.path.append('.')
from hae_data_converter import HAEDataConverter
from pathlib import Path

def test_hae_converter():
    """HAEDataConverterの実行テスト"""
    
    # HAEDataConverterで最新ファイルを処理
    data_dir = Path(r"C:\Users\terada\Desktop\apps\体組成管理app\health_api_data")
    converter = HAEDataConverter(data_dir)
    
    # 最新HAEファイルを取得
    latest_file = converter.get_latest_hae_file()
    print(f"最新HAEファイル: {latest_file}")
    
    if latest_file:
        # CSVに変換（ログ出力あり）
        csv_row = converter.convert_hae_to_csv_row(latest_file)
        if csv_row:
            print("\n=== 変換結果 ===")
            print(f"活動カロリー: {csv_row.get('活動カロリー_kcal')}kcal")
            print(f"歩数: {csv_row.get('歩数')}歩")
            print(f"基礎代謝: {csv_row.get('基礎代謝_kcal')}kcal")
            print(f"日付: {csv_row.get('date')}")
        else:
            print("変換に失敗しました")
    
if __name__ == "__main__":
    test_hae_converter()
