import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import random
import time
import re
import google.generativeai as genai

# =========================================================
#   設定 & 環境変数
# =========================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 統計データ
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

# =========================================================
#  1. HTMLテンプレート (強力な強制リロード版)
# =========================================================
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KASETACK RADAR</title>
    <style>
        body {{ background: #121212; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; margin: 0; line-height: 1.6; }}
        #login-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
        input {{ padding: 12px; font-size: 1.2rem; border-radius: 8px; border: 1px solid #333; background: #222; color: #fff; text-align: center; margin-bottom: 20px; width: 60%; }}
        button {{ padding: 12px 40px; font-size: 1rem; background: #FFD700; color: #000; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }}
        
        #main-content {{ display: none; max-width: 800px; margin: 0 auto; }}
        .header-logo {{ font-weight: 900; font-size: 1.2rem; color: #FFD700; margin-bottom: 5px; }}
        .main-title {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.5rem; letter-spacing: 1px; color: #fff; margin-bottom: 20px; }}
        
        .legend-box {{
            background: #1a1a1a; border: 1px solid #444; border-radius: 8px; padding: 10px; margin-bottom: 20px;
            font-size: 0.8rem; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
        }}
        .legend-item {{ display: inline-block; padding: 2px 6px; border-radius: 4px; background: #222; border: 1px solid #333; white-space: nowrap; }}
        .l-s {{ color: #00e676; border-color: #00e676; font-weight: bold; }}
        .l-a {{ color: #ff4081; border-color: #ff4081; }}
        .l-b {{ color: #00b0ff; }}
        .l-c {{ color: #ffea00; }}
        .l-d {{ color: #9e9e9e; }}

        #report-box {{ background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }}
        h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; font-size: 1.2rem; clear: both; }}
        strong {{ color: #FF4500; font-weight: bold; font-size: 1.1em; }}
        .ai-text {{ font-size: 0.95rem; line-height: 1.8; }}
        .footer {{ text-align: right; font-size: 0.7rem; color: #666; margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; }}
    </style>
</head>
<body>
    <div id="login-screen">
        <div style="font-size: 4rem; margin-bottom: 10px;">🔒</div>
        <div style="color: #FFD700; margin-bottom: 20px; font-weight: bold; letter-spacing: 2px;">KASETACK</div>
        <input type="password" id="pass" placeholder="TODAY'S PASS" />
        <button onclick="check()">OPEN</button>
        <p id="msg" style="color: #ff4444; margin-top: 15px; font-size: 0.9rem;"></p>
    </div>

    <div id="main-content">
        <div class="header-logo">🚖 KASETACK</div>
        <div class="main-title">羽田需要レーダー</div>
        
        <div class="legend-box">
            <span class="legend-item l-s">🌈 S:入れ食い</span>
            <span class="legend-item l-a">🔥 A:超推奨</span>
            <span class="legend-item l-b">✨ B:狙い目</span>
            <span class="legend-item l-c">⚠️ C:要注意</span>
            <span class="legend-item l-d">⛔ D:撤退</span>
        </div>

        <div id="report-box">
            <h3>📊 羽田指数</h3>
            <p>{MARKER_RANK}</p>

            <h3>🏁 狙うべき場所</h3>
            <p>👉 <strong>{MARKER_TARGET}</strong></p>

            <p><strong>判定理由：</strong><br><span class="ai-text">{MARKER_REASON}</span></p>
            <hr style="border: 0; border-top: 1px solid #444; margin: 20px 0;">

            <h3>1. ✈️ 供給データ詳細</h3>
            <div class="ai-text">{MARKER_DETAILS}</div>

            <h3>2. 🚃 外部要因と待機台数</h3>
            <p><strong>【必須】タクシープール待機台数（需要予測計算値）</strong></p>
            <ul>
                <li>国内線プール: <strong>推計 約 {MARKER_NUM_D} 台</strong></li>
                <li>国際線プール: <strong>推計 約 {MARKER_NUM_I} 台</strong></li>
            </ul>
        </div>
        
        <div class="footer">更新: {MARKER_TIME} (JST) <br>📺 自動更新モード: 強制リロードON</div>
    </div>

    <script>
        const correctPass = "{MARKER_PASS}";
        const masterKey = "7777";
        setTimeout(function() {{
            window.location.href = window.location.pathname + "?t=" + new Date().getTime();
        }}, 300000); 

        window.onload = function() {{
            const savedPass = localStorage.getItem("haneda_pass");
            if (savedPass === correctPass) {{ showContent(); }}
        }};
        function check() {{
            const val = document.getElementById("pass").value;
            if (val === correctPass || val === masterKey) {{
                localStorage.setItem("haneda_pass", correctPass);
                showContent();
            }} else {{
                document.getElementById("msg").innerText = "パスワードが違います";
            }}
        }}
        function showContent() {{
            document.getElementById("login-screen").style.display = "none";
            document.getElementById("main-content").style.display = "block";
        }}
    </script>
</body>
</html>
"""

# =========================================================
# 2. 【左脳】データ収集・計算ロジック
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
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
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
        target = f"{best} （統計上の到着予定：{data[best]}便）"
        hint = f"統計データによると、{h}時台は{best}が最も多くの便数を記録しています。"
    else:
        target, hint = "国際線 または 都内", "深夜帯のセオリーに基づきます。"

    if delay: hint += " ※現在、遅延便の影響でピークが変動する可能性があります。"

    base_d, base_i = 180, 100
    m = {"HIGH": 0.4, "MID-HIGH": 0.6, "MID": 0.8, "LOW": 0.95}
    mult = m.get(level, 0.8)
    pd, pi = int(base_d * mult) + random.randint(-10,10), int(base_i * mult) + random.randint(-5,5)

    return {"time_str": ns, "hour": h, "rank": rank, "target": target, "num_d": pd, "num_i": pi, "dom": dom, "intl": intl, "delay": delay, "hint": hint}

# =========================================================
# 3. 【右脳】AI & パスワード
# =========================================================
def call_gemini(prompt):
    if not GEMINI_KEY:
        return "⚠️ APIキーが設定されていません"
    try:
        genai.configure(api_key=GEMINI_KEY)
        # ▼▼▼ ここを修正しました（2.5 -> 1.5） ▼▼▼
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI通信エラー: {str(e)}"

def generate_report():
    print("Starting update...")
    
    # 1. 前回のパスワードをこっそり盗み見る
    old_pass = ""
    if os.path.exists("index.html"):
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                content = f.read()
                # HTMLの中から 'const correctPass = "1234";' を探す
                match = re.search(r'const correctPass = "(\d{4})";', content)
                if match:
                    old_pass = match.group(1)
        except:
            pass # 読み込めなくても気にしない

    # 2. データを集める
    f = determine_facts()
    
    # 3. AIに書かせる
    reason_prompt = f"""
    タクシー運転手へ140字以内で助言をしてください。
    【条件】挨拶や前置きは禁止。「はい、承知しました」等は不要。いきなり本文から始めること。
    状況: 時刻{f['time_str']}, ランク{f['rank']}, 推奨{f['target']}, 便数:国内{f['dom']}/国際{f['intl']}, 遅延:{f['delay']}, 根拠:{f['hint']}
    """
    reason = call_gemini(reason_prompt)
    
    details_prompt = f"""
    国内{f['dom']}便, 国際{f['intl']}便、遅延{'あり' if f['delay'] else 'なし'}。
    各ターミナルの状況を簡潔な箇条書きで出力してください。
    【条件】「Markdown形式で記述します」等の挨拶や前置きは一切禁止。いきなり箇条書きから始めること。
    """
    details = call_gemini(details_prompt)
    
    # 4. 新しいパスワードを決める（朝6時に切り替わる）
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    if now.hour < 6: now = now - datetime.timedelta(days=1)
    random.seed(now.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    # 5. HTMLを保存する
    html = HTML_TEMPLATE.replace(MARKER_RANK, f['rank']).replace(MARKER_TARGET, f['target']).replace(MARKER_REASON, reason).replace(MARKER_DETAILS, details).replace(MARKER_NUM_D, str(f['num_d'])).replace(MARKER_NUM_I, str(f['num_i'])).replace(MARKER_TIME, f['time_str']).replace(MARKER_PASS, pw)
    
    with open("index.html", "w", encoding="utf-8") as file: file.write(html)
    
    # 6. 【ここが重要】パスワードが変わった時だけ Discord 通知する！
    if DISCORD_URL and old_pass != pw:
        requests.post(DISCORD_URL, json={"content": f"📡 **KASETACK 羽田レーダー**\n🌞 **今日のパスワード:** `{pw}`\n(パスワードが更新されました)\nhttps://sunny-kasetaku.github.io/haneda-radar/"})
    
    print("Done!")

if __name__ == "__main__":
    generate_report()
