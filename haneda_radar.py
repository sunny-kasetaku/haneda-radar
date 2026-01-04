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

# キーのクリーニング
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

# =========================================================
#  1. HTMLテンプレート
# =========================================================
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KASETACK RADAR</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
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
        strong {{ color: #FF4500; font-weight: bold; font-size: 1.05em; }}
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
        
        <div class="footer">更新: {MARKER_TIME} (JST)</div>
    </div>

    <script>
        const correctPass = "{MARKER_PASS}";
        const masterKey = "7777";
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
    url_dom = "https://transit.yahoo.co.jp/airport/arrival/23/?kind=1"
    url_intl = "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"
    
    def count_flights(url):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200: return 0, False # count, has_delay
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('li', class_='element')
            
            valid_count = 0
            has_delay = False
            
            for row in rows:
                text = row.get_text()
                # ★ここで欠航チェック！
                if "欠航" in text:
                    continue # 欠航は数えない
                
                # ★ここで遅延チェック！
                if "遅れ" in text or "変更" in text:
                    has_delay = True
                
                valid_count += 1
                
            return valid_count, has_delay
        except:
            return 10, False
            
    count_dom, delay_d = count_flights(url_dom)
    count_intl, delay_i = count_flights(url_intl)
    
    return count_dom, count_intl, (delay_d or delay_i)

def determine_facts():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour
    
    # 1. Yahooからリアルタイム便数（欠航除外・遅延検知済み）を取得
    real_dom_flights, real_intl_flights, has_delay = fetch_flight_data()
    total_flights = real_dom_flights + real_intl_flights
    
    # ランク判定
    if total_flights >= 30:
        rank = "🌈 S 【 確変・入れ食い 】"
        demand_level = "HIGH"
    elif total_flights >= 15:
        rank = "🔥 A 【 超・推奨 】"
        demand_level = "MID-HIGH"
    elif total_flights >= 8:
        rank = "✨ B 【 狙い目 】"
        demand_level = "MID"
    else:
        rank = "⚠️ C 【 要・注意 】"
        demand_level = "LOW"
        
    # 2. 【宝の地図】から最適なターゲットを抽出
    if current_hour in THEORY_DATA:
        hour_data = THEORY_DATA[current_hour]
        best_lane = max(hour_data, key=hour_data.get)
        max_val = hour_data[best_lane]
        sorted_lanes = sorted(hour_data.items(), key=lambda x:x[1], reverse=True)
        second_lane = sorted_lanes[1][0] if len(sorted_lanes) > 1 else ""
        
        target_lane = f"{best_lane} (指数:{max_val})"
        reason_hint = f"統計データによると、現時刻({current_hour}時)は{best_lane}の到着便数が最多({max_val})です。次点は{second_lane}です。"
    else:
        target_lane = "国際線 または 都内"
        reason_hint = "深夜帯のため、国際線または都内営業を推奨します。"
        
    # ★遅延がある場合の注記を追加
    if has_delay:
        reason_hint += " ※現在、遅延便が発生しています。到着客の波が後ろ倒しになる可能性があります。"

    # 3. 待機台数の予測
    base_stock_d = 180
    base_stock_i = 100
    
    if demand_level == "HIGH":
        pred_d = int(base_stock_d * 0.4)
        pred_i = int(base_stock_i * 0.4)
    elif demand_level == "MID-HIGH":
        pred_d = int(base_stock_d * 0.6)
        pred_i = int(base_stock_i * 0.6)
    elif demand_level == "MID":
        pred_d = int(base_stock_d * 0.8)
        pred_i = int(base_stock_i * 0.8)
    else:
        pred_d = int(base_stock_d * 0.95)
        pred_i = int(base_stock_i * 0.95)
        
    pred_d += random.randint(-10, 10)
    pred_i += random.randint(-5, 5)

    return {
        "time_str": ns, "hour": current_hour, "time_zone": "Active",
        "rank": rank, "target": target_lane,
        "num_d": pred_d, "num_i": pred_i,
        "flights_d": real_dom_flights, "flights_i": real_intl_flights,
        "has_delay": has_delay,
        "reason_hint": reason_hint
    }

# =========================================================
# 3. 【右脳】AI生成 (Gemini)
# =========================================================
def find_best_model():
    if not GEMINI_KEY: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        available_models = []
        for m in data.get('models', []):
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                clean_name = m['name'].replace('models/', '')
                available_models.append(clean_name)
        gemini_models = [m for m in available_models if 'gemini' in m.lower()]
        if gemini_models: return gemini_models[0]
        elif available_models: return available_models[0]
        else: return None
    except: return None

def call_gemini(prompt):
    if not GEMINI_KEY: return "Error: API Key missing"
    model_name = find_best_model()
    if not model_name: model_name = "gemini-1.5-flash"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI生成エラー: {r.status_code}"
    except Exception as e:
        return "接続エラー"

def get_ai_reason(facts):
    # 遅延情報の有無をAIに伝える
    delay_info = "【重要】遅延便が発生中。需要のピークが遅れる可能性あり。" if facts['has_delay'] else "特になし"

    prompt = f"""
    あなたはタクシー戦略コンサルタントです。
    以下の事実に基づき、ドライバー向けのアドバイスを140文字以内で作成してください。
    【事実】
    ・時刻: {facts['time_str']}
    ・ランク: {facts['rank']}
    ・推奨レーン: {facts['target']}
    ・統計根拠: {facts['reason_hint']}
    ・運行状況注記: {delay_info}
    ・リアルタイム到着数(欠航除く): 国内{facts['flights_d']} / 国際{facts['flights_i']}
    
    文体は、簡潔で頼りがいのある口調で。
    """
    return call_gemini(prompt)

def get_ai_details(facts):
    delay_text = "⚠️ **一部遅延あり**" if facts['has_delay'] else "✅ **概ね定刻**"
    
    prompt = f"""
    現在の状況：
    国内線到着便(有効): {facts['flights_d']}便
    国際線到着便(有効): {facts['flights_i']}便
    運行状況: {delay_text}
    
    これに基づき、T1, T2, T3の状況をMarkdownの箇条書きで簡潔にレポートしてください。
    """
    return call_gemini(prompt)

# =========================================================
# 4. 実行
# =========================================================
def generate_report():
    print("Processing started...")
    facts = determine_facts()
    reason_text = get_ai_reason(facts)
    time.sleep(1)
    details_text = get_ai_details(facts)
    
    daily_pass = get_daily_password()
    
    html = HTML_TEMPLATE
    html = html.replace(MARKER_RANK, str(facts['rank']))
    html = html.replace(MARKER_TARGET, str(facts['target']))
    html = html.replace(MARKER_REASON, str(reason_text))
    html = html.replace(MARKER_DETAILS, str(details_text))
    html = html.replace(MARKER_NUM_D, str(facts['num_d']))
    html = html.replace(MARKER_NUM_I, str(facts['num_i']))
    html = html.replace(MARKER_TIME, str(facts['time_str']))
    html = html.replace(MARKER_PASS, daily_pass)
    
    send_to_discord(daily_pass, facts['time_str'])

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Processing finished.")

def get_daily_password():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    random.seed(now.strftime('%Y%m%d'))
    return str(random.randint(1000, 9999))

def send_to_discord(password, now_str):
    if not DISCORD_URL: return 
    msg = {
        "username": "羽田レーダー",
        "content": f"📡 **更新完了(統計+遅延対応版)** ({now_str})\n🔑 **PASS:** `{password}`\n（マスターキー: 7777）\n\n📊 **確認はこちら:**\nhttps://sunny-kasetaku.github.io/haneda-radar/"
    }
    try: requests.post(DISCORD_URL, json=msg)
    except: pass

if __name__ == "__main__":
    generate_report()
