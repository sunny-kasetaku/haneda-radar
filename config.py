# ==========================================
# Project: KASETACK - config.py
# ==========================================
import os

CONFIG = {
    # 航空データAPIキー
    "API_KEY": "76e04028a66e0e2d2b42d7d9c75462e7",
    
    # Discord / サイト連携設定 (GitHub Secrets等から取得)
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL", ""),
    "SITE_URL": os.environ.get("SITE_URL", "https://your-site-url.com"),
    
    # ファイル設定
    "DATA_FILE": "haneda_raw.json",
    "RESULT_FILE": "analysis_result.json",
    "RESULT_JSON": "analysis_result.json",
    "REPORT_FILE": "index.html",
    "CACHE_LIMIT_SEC": 300
}
