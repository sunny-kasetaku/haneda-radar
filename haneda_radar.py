import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import random
import time
import re

# 環境変数
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

if GEMINI_KEY:
    GEMINI_KEY = GEMINI_KEY.strip()

# =========================================================
#  設定 & 宝の地図データ (サニーさんのExcelデータ)
# =========================================================
THEORY_DATA = {
    7:  {"1号(T1)": 2,  "2号(T1)": 0,  "3号(T2)": 1,  "4号(T2)": 0,  "国際": 8},
    8:  {"1号(T1)": 8,  "2号(T1)": 9,  "3号(T2)": 13, "4号(T2)": 4,  "国際": 0},
    9:  {"1号(T1)": 10, "2号(T1)": 9,  "3号(T2)": 16, "4号(T2)": 3,  "国際": 1},
    10: {"1号(T1)": 6,  "2号(T1)": 8,  "3号(T2)": 9,  "4号(T2)": 4,  "国際": 0},
    11: {"1号(T1)": 10, "2号(T1)": 10, "3号(T2)": 10, "4号(T2)": 6,  "国際": 1},
    12: {"1号(T1)": 9,  "2号(T1)": 7,  "3号(T2)": 14, "4号(T2)": 4,  "国際": 1},
    13: {"1号(T1)": 10, "2号(T1)": 9,  "3号(T2)": 8,  "4号(T2)": 4,  "国際": 0},
    14: {"1号(T1)": 8,  "2号(T1)": 5,  "3号(T2)": 9,  "4号(T2)": 7,  "国際": 0},
    15: {"1号(T1)": 7,  "2号(T1)": 7,  "3号(T2)": 13, "4号(T2)": 3,  "国際": 0},
    16: {"1号(T1)": 7,  "2号(T1)": 12, "3号(T2)": 10, "4号(T2)": 5,  "国際": 2},
    17: {"1号(T1)": 10, "2号(T1)": 7,  "3号(T2)": 10, "4号(T2)": 4,  "国際": 6},
    18: {"1号(T1)": 10, "2号(T1)": 8,  "3号(T2)": 11, "4号(T2)": 9,  "国際": 1},
    19: {"1号(T1)": 9,  "2号(T1)": 7,  "3号(T2)": 11, "4号(T2)": 3,  "国際": 1},
    20: {"1号(T1)": 11, "2号(T1)": 7,  "3号(T2)": 11, "4号(T2)": 4,  "国際": 2},
    21: {"1号(T1)": 10, "2号(T1)": 10, "3号(T2)": 14, "4号(T2)": 4,  "国際": 1},
    22: {"1号(T1)": 7,  "2号(T1)": 7,  "3号(T2)": 9,  "4号(T2)": 4,  "国際": 2},
    23: {"1号(T1)": 1,  "2号(T1)": 0,  "3号(T2)": 2,  "4号(T2)": 3,  "国際": 0}
}

MARKER_RANK = "[[RANK]]"
MARKER_TARGET = "[[TARGET]]"
MARKER_REASON = "[[REASON]]"
MARKER_DETAILS = "[[DETAILS]]"
MARKER_NUM_D = "[[NUM_D]]"
MARKER_NUM_I = "[[NUM_I]]"
MARKER_TIME = "[[TIME]]"
MARKER_PASS = "[[PASS]]"

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KASETACK RADAR</title>
    <style>
        body {{ background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; margin: 0; line-height: 1.6; }}
        #login-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
        input {{ padding: 12px; font-size: 1.2rem; border-radius: 8px; border: 1px solid #333; background: #222; color: #fff; text-align: center; margin-bottom: 20px; width: 60%; }}
        button {{ padding: 12px 40px; font-size: 1rem; background: #FFD700; color: #000; border: none; border-radius: 8px; font-weight: bold; }}
        #main-content {{ display: none; max-width: 800px; margin: 0 auto; }}
        .header-logo {{ font-weight: 900; font-size: 1.2rem; color: #FFD700; }}
        .main-title {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.5rem; color: #fff; margin-bottom: 20px; }}
        #report-box {{ background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }}
        h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; font-size: 1.2rem; }}
        strong {{ color: #FF4500; }}
        .footer {{ text-align: right; font-size: 0.7rem; color: #666; margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; }}
    </style>
</head>
<body>
    <div id="login-screen">
        <div style="font-size: 4rem;">🔒</div>
        <div style="color: #FFD700; margin-bottom: 20px; font-weight: bold;">KASETACK</div>
        <input type="password" id="pass" placeholder="TODAY'S PASS" />
        <button onclick="check()">OPEN</button>
        <p id="msg" style="color: #ff4444; margin-top: 15px;"></p>
    </div>
    <div id="main-content">
        <div class="header-logo">🚖 KASETACK</div>
        <div class="main-title">羽田需要レーダー</div>
        <div id="report-box">
            <h3>📊 羽田指数</h3><p>{MARKER_RANK}</p>
            <h3>🏁 狙うべき場所</h3><p>👉 <strong>{MARKER_TARGET}</strong></p>
            <p><strong>判定理由：</strong><br>{MARKER_REASON}</p>
            <hr style="border:0; border-top:1px solid #444;">
            <h3>1. ✈️ 供給データ詳細</h3><div>{MARKER_DETAILS}</div>
            <h3>2. 🚃 外部要因と待機台数</h3>
            <ul><li>国内線: <strong>推計 約 {MARKER_NUM_D} 台</strong></li><li>国際線: <strong>推計 約 {MARKER_NUM_I} 台</strong></li></ul>
        </div>
        <div class="footer">更新: {MARKER_TIME} (JST)</div>
    </div>
    <script>
        const correctPass = "{MARKER_PASS}";
        const masterKey = "7777";
        window.onload = function() {{ if (localStorage.getItem("haneda_pass") === correctPass) showContent(); }};
        function check() {{
            const val = document.getElementById("pass").value;
            if (val === correctPass || val === masterKey) {{ localStorage.setItem("haneda_pass", correctPass); showContent(); }}
            else {{ document.getElementById("msg").innerText = "パスワードが違います"; }}
        }}
        function showContent() {{ document.getElementById("login-screen").style.display = "none"; document.getElementById("main-content").style.display = "block"; }}
    </script>
</body>
</html>
"""

# =========================================================
# 2. 【左脳】データ収集ロジック (欠航・遅延を厳密に判定)
# =========================================================
def fetch_flight_data():
    urls = [
        "https://transit.yahoo.co.jp/airport/arrival/23/?kind=1",
        "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"
    ]
    counts = []
    has_delay = False
    
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('li', class_='element')
            valid = 0
            for row in rows:
                t = row.get_text()
                if "欠航" in t or "到着済" in t: continue
                if "遅れ" in t or "変更" in t: has_delay = True
                valid += 1
            counts.append(valid)
        except:
            counts.append(10)
    return counts[0], counts[1], has_delay

def determine_facts():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    h = n.hour
    
    dom, intl, delay = fetch_flight_data()
    total = dom + intl
    
    if total >= 30: rank, level = "🌈 S 【 確変・入れ食い 】", "HIGH"
    elif total >= 15: rank, level = "🔥 A 【 超・推奨 】", "MID-HIGH"
    elif total >= 8: rank, level = "✨ B 【 狙い目 】", "MID"
    else: rank, level = "⚠️ C 【 要・注意 】", "LOW"
        
    if h in THEORY_DATA:
        data = THEORY_DATA[h]
        best = max(data, key=data.get)
        target = f"{best} (指数:{data[best]})"
        hint = f"統計上、{h}時は{best}が最も強い時間帯です。"
    else:
        target, hint = "国際線 または 都内", "深夜帯のセオリーに基づきます。"

    if delay: hint += " ※遅延便により波が後ろ倒しになる可能性があります。"

    # 台数予測
    base_d, base_i = 180, 100
    m = {"HIGH": 0.4, "MID-HIGH": 0.6, "MID": 0.8, "LOW": 0.95}
    mult = m.get(level, 0.8)
    pd, pi = int(base_d * mult) + random.randint(-10,10), int(base_i * mult) + random.randint(-5,5)

    return {"time_str": ns, "hour": h, "rank": rank, "target": target, "num_d": pd, "num_i": pi, "dom": dom, "intl": intl, "delay": delay, "hint": hint}

# =========================================================
# 3. 【右脳】AI & パスワード (朝6時更新)
# =========================================================
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    try:
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "接続エラー"

def generate_report():
    f = determine_facts()
    reason = call_gemini(f"タクシー運転手に140字以内で助言。時刻:{f['time_str']}, ランク:{f['rank']}, 推奨:{f['target']}, 便数:国内{f['dom']}/国際{f['intl']}, 遅延:{f['delay']}, 根拠:{f['hint']}")
    details = call_gemini(f"国内{f['dom']}便, 国際{f['intl']}便、遅延{'あり' if f['delay'] else 'なし'}。各ターミナルの状況を簡潔なMarkdownで。")
    
    # ★朝6時更新のパスワード
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    if now.hour < 6: now = now - datetime.timedelta(days=1)
    random.seed(now.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace(MARKER_RANK, f['rank']).replace(MARKER_TARGET, f['target']).replace(MARKER_REASON, reason).replace(MARKER_DETAILS, details).replace(MARKER_NUM_D, str(f['num_d'])).replace(MARKER_NUM_I, str(f['num_i'])).replace(MARKER_TIME, f['time_str']).replace(MARKER_PASS, pw)
    
    if DISCORD_URL:
        requests.post(DISCORD_URL, json={"content": f"📡 **羽田レーダー更新**\n🔑 **PASS:** `{pw}` (朝6時まで有効)\nhttps://sunny-kasetaku.github.io/haneda-radar/"})
    
    with open("index.html", "w", encoding="utf-8") as file: file.write(html)

if __name__ == "__main__":
    generate_report()
