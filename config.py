# ==========================================
# Project: KASETACK - config.py
# ==========================================
import os

CONFIG = {
    # 航空データAPIキー
    "API_KEY": "7dd32199bfacf0d3d6f8d538b4511d29b",
    
    # Discord Webhook (GitHub Secretsから取得)
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL", ""),
    
    # サイトURL (修正：kasetack -> kasetaku)
    "SITE_URL": "https://sunny-kasetaku.github.io/haneda-radar/",
    
    # 内部ファイルパス
    "DATA_FILE": "haneda_raw.json",
    "RESULT_FILE": "analysis_result.json",
    "RESULT_JSON": "analysis_result.json",
    "REPORT_FILE": "index.html",
    "CACHE_LIMIT_SEC": 300
}
