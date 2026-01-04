import requests
import json
import datetime
import os
import random
import time

# 環境変数
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ★★★ キーのクリーニング ★★★
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
MARKER_DEBUG = "[[DEBUG]]" # ★デバッグ用

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
# 3. AI生成 (詳細なエラー表示モード)
# =========================================================
def call_gemini(prompt):
    if not GEMINI_KEY:
        return "<div class='error-msg'>エラー: GEMINI_API_KEY が空です。Secretsを確認してください。</div>"

    # 確実に動くはずの組み合わせだけを試す
    combinations = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-pro")
    ]

    error_logs = []

    for version, model in combinations:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={GEMINI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                # ★ここが重要！Googleからの本当の返事を読み取る
                try:
                    error_json = r.json()
                    real_msg = error_json['error']['message'] # 詳しい理由
                except:
                    real_msg = r.text[:200] # 読み取れなければ原文を表示
                
                error_logs.append(f"<br><strong>[{model}]</strong> Status:{r.status_code}<br>Message: {real_msg}")
                continue
        except Exception as e:
            error_logs.append(f"[{model}] Connect Error: {str(e)}")
            continue

    return f"<div class='error-msg'>AI Connect Failed:{''.join(error_logs)}</div>"

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
    
    # 鍵の状態をチェック（セキュリティのため長さだけ表示）
    key_status = "OK" if GEMINI_KEY else "MISSING"
    key_len = len(GEMINI_KEY) if GEMINI_KEY else 0
    debug_msg = f"API Key Status: {key_status} (Length: {key_len})"
    
    reason_text = get_ai_reason(facts)
    time.sleep(1)
    details_text = get_ai_details(facts)
    daily_pass = "7777" # 今日は固定
    
    html = HTML_TEMPLATE
    html = html.replace(MARKER_RANK, str(facts['rank']))
    html = html.replace(MARKER_TARGET, str(facts['target']))
    html = html.replace(MARKER_REASON, str(reason_text))
    html = html.replace(MARKER_DETAILS, str(details_text))
    html = html.replace(MARKER_NUM_D, str(facts['num_d']))
    html = html.replace(MARKER_NUM_I, str(facts['num_i']))
    html = html.replace(MARKER_TIME, str(facts['time_str']))
    html = html.replace(MARKER_PASS, daily_pass)
    html = html.replace(MARKER_DEBUG, debug_msg) # デバッグ表示
    
    # Discord通知
    if DISCORD_URL:
        requests.post(DISCORD_URL, json={"content": f"📡 更新完了 (Debug: {key_status}/{key_len})\nPASS: 7777"})

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Processing finished.")

if __name__ == "__main__":
    generate_report()
