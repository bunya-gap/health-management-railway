# Oura API 設定ファイル
# 初回設定時にトークンを入力してください

OURA_ACCESS_TOKEN = "JQI3Z4TCC57DMDIKIPH77IFEJJS255Z3"  # ここにOura Personal Access Tokenを設定
OURA_API_BASE_URL = "https://api.ouraring.com/v2"

# Oura APIから取得するデータの設定
OURA_ENABLED = True  # False に設定するとOuraデータ取得をスキップ
OURA_START_DATE = "2025-06-01"  # 体組成アプリと同じ開始日

# 体表温データマッピング
TEMPERATURE_MAPPING = {
    'temperature_delta': '体表温変化_celsius',
    'temperature_deviation': '体表温偏差_celsius',
    'temperature_trend_deviation': '体表温トレンド偏差_celsius'
}

def is_oura_configured():
    """Oura設定が完了しているかチェック"""
    return OURA_ENABLED and OURA_ACCESS_TOKEN and len(OURA_ACCESS_TOKEN) > 10
