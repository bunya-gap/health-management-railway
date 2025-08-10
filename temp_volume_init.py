"""
Railway Volume 初期化処理
初回起動時に過去データをVolumeに移行する機能を追加
"""

import os
import shutil
import requests
from pathlib import Path

def initialize_volume_data():
    """
    Railway Volume初回起動時の過去データ移行処理
    /app/reports が空の場合、過去データを作成
    """
    volume_reports_dir = Path("/app/reports")
    
    # Volumeディレクトリが存在し、かつ空でない場合はスキップ
    if volume_reports_dir.exists() and any(volume_reports_dir.iterdir()):
        print("Volume already contains data, skipping initialization")
        return
    
    # Volumeディレクトリを作成
    volume_reports_dir.mkdir(parents=True, exist_ok=True)
    
    print("Initializing volume with historical data...")
    
    # GitHub経由でのファイル取得URLs
    github_base_url = "https://raw.githubusercontent.com/bunya-gap/health-management-app/main/reports/"
    
    files_to_download = [
        "日次データ.csv",
        "7日移動平均データ.csv", 
        "インデックスデータ.csv"
    ]
    
    for filename in files_to_download:
        try:
            url = github_base_url + filename
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                file_path = volume_reports_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"Downloaded: {filename}")
            else:
                print(f"Failed to download {filename}: {response.status_code}")
                
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
    
    print("Volume initialization completed!")

if __name__ == "__main__":
    initialize_volume_data()
