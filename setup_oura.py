#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oura Ring体表温データ統合 - 初回設定ツール
Personal Access Tokenの設定を行います
"""

import os
import webbrowser
from datetime import datetime

def setup_oura_integration():
    """Oura統合の初回設定"""
    
    print("=== Oura Ring 体表温データ統合 - 初回設定 ===")
    print()
    print("このツールは、Oura RingのAPIから体表温データを自動取得し、")
    print("体組成管理アプリに統合するための設定を行います。")
    print()
    
    # 前提条件の確認
    print("【前提条件】")
    print("✓ Oura Ring（第3世代またはOura Ring 4）を所有")
    print("✓ 有効なOuraメンバーシップ（サブスクリプション）")
    print("✓ Ouraアカウントでのログイン可能")
    print()
    
    confirm = input("上記の条件を満たしていますか？ (y/N): ").strip().lower()
    if confirm != 'y':
        print("前提条件を満たしてから再度実行してください。")
        return False
    
    # Personal Access Token取得の案内
    print()
    print("【Personal Access Token の取得】")
    print("1. Oura Personal Access Token ページを開きます")
    print("2. Ouraアカウントでログインしてください")
    print("3. 「Create Personal Access Token」をクリック")
    print("4. Token名を入力（例：体組成管理アプリ）")
    print("5. 生成されたTokenをコピーしてください")
    print()
    
    open_browser = input("Personal Access Token ページを開きますか？ (Y/n): ").strip().lower()
    if open_browser != 'n':
        webbrowser.open('https://cloud.ouraring.com/personal-access-tokens')
        print("ブラウザでページを開きました。")
        input("Tokenを取得したらEnterを押してください...")
    
    # Tokenの入力
    print()
    token = input("Personal Access Token を入力してください: ").strip()
    
    if len(token) < 10:
        print("エラー: 正しいTokenを入力してください。")
        return False
    
    # 設定ファイルの更新
    config_path = "oura_config.py"
    try:
        # 現在の設定ファイルを読み込み
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Tokenを設定
        new_config = config_content.replace(
            'OURA_ACCESS_TOKEN = ""',
            f'OURA_ACCESS_TOKEN = "{token}"'
        )
        
        # 設定を有効化
        new_config = new_config.replace(
            'OURA_ENABLED = True',
            'OURA_ENABLED = True'
        )
        
        # ファイルに保存
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(new_config)
        
        print(f"✓ 設定ファイル更新完了: {config_path}")
        
    except Exception as e:
        print(f"エラー: 設定ファイルの更新に失敗しました: {e}")
        return False
    
    # 接続テスト
    print()
    print("【接続テスト】")
    try:
        import requests
        
        url = "https://api.ouraring.com/v2/usercollection/personal_info"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print("Oura APIに接続中...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()
            print("✓ 接続成功！")
            
            if 'age' in user_info:
                print(f"  ユーザー情報: 年齢 {user_info['age']}歳")
            
        else:
            print(f"✗ 接続失敗: HTTP {response.status_code}")
            print("Tokenを確認してください。")
            return False
            
    except Exception as e:
        print(f"✗ 接続テスト失敗: {e}")
        print("インターネット接続またはTokenを確認してください。")
        return False
    
    # 完了案内
    print()
    print("🎉 Oura Ring体表温データ統合の設定が完了しました！")
    print()
    print("【次のステップ】")
    print("1. unified_processor.py を実行")
    print("2. reports/ フォルダに以下のデータが追加されます：")
    print("   - 体表温変化_celsius（基準値からの変化）")
    print("   - 体表温偏差_celsius（日次偏差）") 
    print("   - 体表温トレンド_celsius（3日移動平均トレンド）")
    print("   - 体表温変化インデックス（インデックスデータに追加）")
    print()
    print("【データについて】")
    print("• 体表温変化: 0°Cが基準値、+/-は個人基準値からの変化")
    print("• 測定タイミング: 夜間睡眠中の平均値")
    print("• 更新頻度: unified_processor.py実行時に自動取得")
    print()
    
    return True

def test_connection():
    """既存設定での接続テスト"""
    try:
        from oura_config import is_oura_configured, OURA_ACCESS_TOKEN
        
        if not is_oura_configured():
            print("Oura設定が未完了です。setup_oura_integration()を実行してください。")
            return False
        
        import requests
        
        url = "https://api.ouraring.com/v2/usercollection/personal_info"
        headers = {
            'Authorization': f'Bearer {OURA_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✓ Oura API接続正常")
            return True
        else:
            print(f"✗ Oura API接続失敗: HTTP {response.status_code}")
            return False
            
    except ImportError:
        print("oura_config.py が見つかりません。")
        return False
    except Exception as e:
        print(f"接続テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("【選択してください】")
    print("1. 初回設定を行う")
    print("2. 接続テストのみ実行")
    
    choice = input("選択 (1 or 2): ").strip()
    
    if choice == "1":
        setup_oura_integration()
    elif choice == "2":
        test_connection()
    else:
        print("無効な選択です。")
