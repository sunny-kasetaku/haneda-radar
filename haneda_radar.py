import requests
import json
import datetime
import os
import random
import re
from bs4 import BeautifulSoup

# =========================================================
#   設定 & 環境変数
# =========================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# (中略: THEORY_DATA, HTML_TEMPLATE, fetch_flight_data, determine_facts は維持)

def call_gemini(prompt):
    if not GEMINI_KEY: return "⚠️ APIキー未設定"
    
    # 🌟 2026年最新仕様: Gemini 2.0 Flash を直接叩くURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in res_json:
            return f"AI通信エラー(API): {res_json['error']['message']}"
        else:
            return "AI返答なし"
    except Exception as e:
        return f"AI通信エラー(通信): {str(e)}"

# (以下、generate_report などは維持)
