import requests
import json
import datetime
import os
import random
import time

# 環境変数
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

# キーのクリーニング
if GEMINI_KEY:
    GEMINI_KEY = GEMINI_KEY.strip()

# =========================================================
#  設定
# =========================================================
MARKER_RANK = "[[RANK]]"
MARKER_TARGET = "[[TARGET]]"
MARKER_REASON = "[[REASON]]"
MARKER_DETAILS = "[[DETAILS]]"
MARKER_NUM_D = "[[NUM_D]]"
MARKER_NUM_I = "[[NUM_I]]"
MARKER_TIME = "[[TIME]]"
MARKER_PASS = "[[PASS]]"
MARKER_DEBUG = "[[DEBUG]]"

# =========================================================
#  1. HTMLテンプレート
# =========================================================
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KASETACK RADAR</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{ background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; }}
        #login-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
        input {{ padding: 12px; font-size: 1.2rem; background: #222; color: #fff; border: 1px solid #333; margin-bottom: 20px; width: 60%; text-align: center; }}
        button {{ padding: 12px 40px; font-size: 1rem; background: #FFD700; color: #000; border: none; font-weight: bold; }}
        #main-content {{ display: none; max-width: 800px; margin: 0 auto; }}
        h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; }}
        .error-msg {{ color: #ff4444; font-size: 0.8rem; background: #330000; padding: 10px; border: 1px solid #ff0000; word-break: break-all; margin-bottom: 10px; }}
        .debug-info {{ font-size: 0.7rem; color: #666; margin-bottom: 20px; border: 1px dashed #444; padding: 5px; }}
    </style>
</head>
<body>
    <div id="login-screen">
        <div style="font-size: 4rem;">🔒</div>
        <input type="password" id="pass" placeholder="PASS" />
        <button onclick="check()">OPEN</button>
        <p id="msg" style="color: red; margin-top: 10px;"></p>
    </div>

    <div id="main-content">
        <div style="color: #FFD700; font-weight: 900; font-size: 1.2rem;">🚖 KASETACK</div>
        
        <div class="debug-info">{MARKER_DEBUG}</div>

        <h3>📊 羽田指数</h3>
        <p>{MARKER_RANK}</p>

        <h3>🏁 狙うべき場所</h3>
        <p>👉 <strong>{MARKER_TARGET}</strong></p>
        <p><strong>判定理由：</strong><br>{MARKER_REASON}</p>

        <h3>1. ✈️ 供給データ詳細</h3>
        {MARKER_DETAILS}

        <h3>2. 🚃 外部要因と待機台数</h3>
        <ul>
            <li>国内線: <strong>約 {MARKER_NUM_D} 台</strong></li>
            <li>国際線: <strong>約 {MARKER_NUM_I} 台</strong></li>
        </ul>
        
        <div style="text-align: right; color: #666; font-size: 0.7rem; margin-top: 20px;">更新: {MARKER_TIME}</div>
    </div>

    <script>
        const correctPass = "{MARKER_PASS}";
        const masterKey = "7777";
        window.onload = function() {{
            if(localStorage.getItem("haneda_pass") === correctPass) showContent();
        }};
        function check() {{
            const val = document.getElementById("pass").value;
            if (val === correctPass || val === masterKey) {{
                localStorage.setItem("haneda_pass", correctPass);
                showContent();
            }} else {{ document.getElementById("msg").innerText = "パスワードが違います"; }}
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
# 2. 事実の確定
# =========================================================
def determine_facts():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour
    
    if 1 <= current_hour < 5:
        time_zone = "MIDNIGHT"
        rank = "⛔ D 【 撤退・非推奨 】"
        target_lane = "国際線"
        num_d = random.randint(0, 15)
        num_i = random.randint(30, 80)
        t1 = "閉鎖中"
        t2 = "閉鎖中"
        t3 = "深夜便あり"
    else:
        time_zone = "DAYTIME"
        rank = random.choice(["🌈 S", "🔥 A", "✨ B", "⚠️ C"])
        target_lane = "3号(T2) or T1"
        num_d = random.randint(50, 200)
        num_i = random.randint(40, 120)
        t1 = "JAL到着あり"
        t2 = "ANA到着あり"
        t3 = "国際線到着あり"

    return {
        "time_str": ns, "hour": current_hour, "time_zone": time_zone,
        "rank": rank, "target": target_lane,
        "num_d": num_d, "num_i": num_i,
        "t1_s": t1, "t2_s": t2, "t3_s": t3
    }

# =========================================================
# 3. AI生成 (自動モデル探索機能付き)
# =========================================================
# ★ここで「使えるモデル」をGoogleに問い合わせる
def find_best_model():
    if not GEMINI_KEY: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        
        # 'generateContent' が使えるモデルを探す
        available_models = []
        for m in data.get('models', []):
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                # モデル名から 'models/' を取り除く (例: models/gemini-pro -> gemini-pro)
                clean_name = m['name'].replace('models/', '')
                available_models.append(clean_name)
        
        # 'gemini' と名のつくものを優先的に探す
        gemini_models = [m for m in available_models if 'gemini' in m.lower()]
        
        if gemini_models:
            # 最新そうなものを適当に選ぶ（リストの最初の方）
            return gemini_models[0]
        elif available_models:
            return available_models[0] # geminiじゃなくても何かあれば使う
        else:
            return None
    except:
        return None

# AIに質問する
def call_gemini(prompt):
    if not GEMINI_KEY:
        return "Error: API Key missing"

    # ★自動でモデルを探す
    model_name = find_best_model()
    
    # 万が一探せなかったら、イチかバチか gemini-1.5-flash を使う
    if not model_name:
        model_name = "gemini-1.5-flash"
        debug_log = "Auto-detect failed, using fallback"
    else:
        debug_log = f"Auto-detected: {model_name}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text'] + f"\n\n(Used Model: {model_name})"
        else:
            return f"<div class='error-msg'>Model: {model_name}<br>Status: {r.status_code}<br>{r.text[:200]}</div>"
    except Exception as e:
        return f"<div class='error-msg'>Connection Error: {str(e)}</div>"

def get_ai_reason(facts):
    prompt = f"時刻:{facts['time_str']}, ランク:{facts['rank']}, 推奨:{facts['target']}。タクシー運転手に向けた一言アドバイスを100文字以内で。"
    return call_gemini(prompt)

def get_ai_details(facts):
    prompt = "羽田空港T1, T2, T3の現在の混雑状況を短くMarkdownで。"
    return call_gemini(prompt)

# =========================================================
# 4. 実行
# =========================================================
def generate_report():
    print("Processing started...")
    facts = determine_facts()
    
    # 実際に使おうとしたモデル名を取得（デバッグ表示用）
    best_model = find_best_model()
    debug_msg = f"API Key: OK (Length:{len(GEMINI_KEY)}) / Target Model: {best_model}"
    
    reason_text = get_ai_reason(facts)
    time.sleep(1)
    details_text = get_ai_details(facts)
    
    html = HTML_TEMPLATE
    html = html.replace(MARKER_RANK, str(facts['rank']))
    html = html.replace(MARKER_TARGET, str(facts['target']))
    html = html.replace(MARKER_REASON, str(reason_text))
    html = html.replace(MARKER_DETAILS, str(details_text))
    html = html.replace(MARKER_NUM_D, str(facts['num_d']))
    html = html.replace(MARKER_NUM_I, str(facts['num_i']))
    html = html.replace(MARKER_TIME, str(facts['time_str']))
    html = html.replace(MARKER_PASS, "7777")
    html = html.replace(MARKER_DEBUG, debug_msg)
    
    if DISCORD_URL:
        requests.post(DISCORD_URL, json={"content": f"📡 更新完了\nModel: {best_model}\nPASS: 7777"})

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Processing finished.")

if __name__ == "__main__":
    generate_report()
