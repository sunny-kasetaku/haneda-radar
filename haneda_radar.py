import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # URLをわざと2つに分けて合体させ、GitHubの自動リンク機能を完全に殺します
    u1 = "https://generativelanguage.googleapis.com/v1beta/models/"
    u2 = "gemini-1.5-flash:generateContent?key="
    url = u1 + u2 + str(K)
    
    p = {"contents": [{"parts": [{"text": "羽田空港のT1/T2/T3別の14時〜16時の到着便数と需要予測を短く教えて。"}]}]}
    
    try:
        r = requests.post(url, json=p, timeout=30)
        j = r.json()
        if r.status_code == 200:
            res = j['candidates'][0]['content']['parts'][0]['text']
        else:
            res = "API Error: " + str(r.status_code)
    except Exception as e:
        res = "Error: " + str(e)

    h = f"<html><body style='background:#121212;color:#FFD700;padding:20px;'><h1>羽田需要分析</h1><pre style='white-space:pre-wrap;color:#fff;'>{res}</pre><p>更新:{ns}</p></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
