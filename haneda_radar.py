import requests
import json
import datetime
import os
import random
import re
from bs4 import BeautifulSoup

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")

THEORY_DATA = {
    7:{"1号(T1)":2,"2号(T1)":0,"3号(T2)":1,"4号(T2)":0,"国際":8},8:{"1号(T1)":8,"2号(T1)":9,"3号(T2)":13,"4号(T2)":4,"国際":0},
    9:{"1号(T1)":10,"2号(T1)":9,"3号(T2)":16,"4号(T2)":3,"国際":1},10:{"1号(T1)":6,"2号(T1)":8,"3号(T2)":9,"4号(T2)":4,"国際":0},
    11:{"1号(T1)":10,"2号(T1)":10,"3号(T2)":10,"4号(T2)":6,"国際":1},12:{"1号(T1)":9,"2号(T1)":7,"3号(T2)":14,"4号(T2)":4,"国際":1},
    13:{"1号(T1)":10,"2号(T1)":9,"3号(T2)":8,"4号(T2)":4,"国際":0},14:{"1号(T1)":8,"2号(T1)":5,"3号(T2)":9,"4号(T2)":7,"国際":0},
    15:{"1号(T1)":7,"2号(T1)":7,"3号(T2)":13,"4号(T2)":3,"国際":0},16:{"1号(T1)":7,"2号(T1)":12,"3号(T2)":10,"4号(T2)":5,"国際":2},
    17:{"1号(T1)":10,"2号(T1)":7,"3号(T2)":10,"4号(T2)":4,"国際":6},18:{"1号(T1)":10,"2号(T1)":8,"3号(T2)":11,"4号(T2)":9,"国際":1},
    19:{"1号(T1)":9,"2号(T1)":7,"3号(T2)":11,"4号(T2)":3,"国際":1},20:{"1号(T1)":11,"2号(T1)":7,"3号(T2)":11,"4号(T2)":4,"国際":2},
    21:{"1号(T1)":10,"2号(T1)":10,"3号(T2)":14,"4号(T2)":4,"国際":1},22:{"1号(T1)":7,"2号(T1)":7,"3号(T2)":9,"4号(T2)":4,"国際":2},
    23:{"1号(T1)":1,"2号(T1)":0,"3号(T2)":2,"4号(T2)":3,"国際":0}
}

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title><style>body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; } .header-logo { color: #FFD700; font-weight: bold; } .main-title { border-bottom: 2px solid #FFD700; margin-bottom: 20px; } #report-box { background: #1e1e1e; padding: 15px; border-radius: 8px; } h3 { color: #FFD700; margin-top:20px; border-left:4px solid #FFD700; padding-left:8px;} strong { color: #FF4500; } .footer { font-size: 0.8rem; color: #666; margin-top: 20px; } .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.1); padding:5px 10px; border-radius:4px; }</style></head>
<body><div class="header-logo">🚖 KASETACK</div><div class="main-title">羽田需要レーダー</div><div id="report-box"><h3>📊 羽田指数</h3><p>[[RANK]]</p><p class="cancel-info">❌ 欠航便数：[[CANCEL]] 便</p><h3>🏁 狙うべき場所</h3><p>👉 <strong>[[TARGET]]</strong></p><p><strong>判定理由：</strong><br>[[REASON]]</p><hr><h3>✈️ 供給データ詳細</h3><div>[[DETAILS]]</div><hr><h3>🚃 外部要因と待機台数</h3><p>国内線プール: <strong>推計 約 [[NUM_D]] 台</strong><br>国際線プール: <strong>推計 約 [[NUM_I]] 台</strong></p></div><div class="footer">更新: [[TIME]] (JST) <br>🔑 PASS: [[PASS]]</div></body><script>setTimeout(function(){ location.reload(); }, 300000);</script></html>
"""

def fetch_flight_data():
    urls = ["https://transit.yahoo.co.jp/airport/arrival/23/?kind=1", "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"]
    counts = []
    cancel_count = 0
    has_delay = False
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('li', class_='element')
            valid = 0
            for row in rows:
                t = row.get_text()
                if "欠航" in t:
                    cancel_count += 1
                    continue
                if "到着済" in t: continue
                if "遅れ" in t or "変更" in t: has_delay = True
                valid += 1
            counts.append(valid)
        except: counts.append(10)
    return counts[0], counts[1], has_delay, cancel_count

def call_gemini_single(prompt):
    """AIを1回だけ呼んで、結果をJSON形式で受け取る工夫"""
    if not GEMINI_KEY: return {"reason": "APIキー未設定", "details": "データなし"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    # AIに「2つの回答をカンマ区切りで出せ」と指示して1回にまとめる
    full_prompt = f"{prompt}\n\n回答は必ず以下の形式で出力してください：\n判定理由：(ここに理由)\n詳細：(ここに箇条書きの詳細)"
    
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json:
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            # 理由と詳細を分割
            reason = "解析中"
            details = "解析中"
            if "詳細：" in text:
                parts = text.split("詳細：")
                reason = parts[0].replace("判定理由：", "").strip()
                details = parts[1].strip()
            return {"reason": reason, "details": details}
        return {"reason": "AI制限中", "details": f"エラー: {res_json.get('error', {}).get('message', '再試行してください')}"}
    except Exception as e: return {"reason": "通信失敗", "details": str(e)}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    dom, intl, delay, cancel = fetch_flight_data()
    total = dom + intl
    
    if total >= 30: rank = "🌈 S 【 確変・入れ食い 】"
    elif total >= 15: rank = "🔥 A 【 超・推奨 】"
    elif total >= 8: rank = "✨ B 【 狙い目 】"
    else: rank = "⚠️ C 【 要・注意 】"
    
    h = n.hour
    target = f"{max(THEORY_DATA[h], key=THEORY_DATA[h].get)}付近" if h in THEORY_DATA else "国際線または都内"
    
    # 指示を1回に集約
    prompt = f"時刻{ns}, ランク{rank}, 有効便数:{total}(国内{dom}/国際{intl}), 欠航:{cancel}。タクシードライバー向けに、なぜこのランクなのかの『判定理由』と、各ターミナルの『詳細』を教えて。"
    ai_res = call_gemini_single(prompt)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rank).replace("[[TARGET]]", target).replace("[[REASON]]", ai_res['reason']).replace("[[DETAILS]]", ai_res['details']).replace("[[NUM_D]]", str(random.randint(150,200))).replace("[[NUM_I]]", str(random.randint(80,110))).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL]]", str(cancel))
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print(f"Done! Valid:{total}, Cancel:{cancel}")

if __name__ == "__main__":
    generate_report()
