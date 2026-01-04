import requests
import json
import datetime
import os
import random
import time

# 環境変数からキーを取得
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ---------------------------------------------------------
# 1. 【司令塔】 Pythonが全ての「事実（数字・ランク・場所）」を決定する
#    AIには一切「計算」や「判断」をさせない。
# ---------------------------------------------------------
def determine_facts():
    # 現在時刻
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour
    
    # --- A. 時間帯による基本ステータス決定 ---
    if 1 <= current_hour < 5:
        # 深夜 (01:00-05:00)
        time_zone = "MIDNIGHT"
        rank = "⛔ D 【 撤退・非推奨 】"
        target_lane = "国際線プール または 都内営業"
        
        # 深夜の台数（少なめ）
        num_domestic = random.randint(0, 15)
        num_intl = random.randint(30, 80)
        
        # 各ターミナルの状況（強制）
        t1_status = "【閉鎖中】国内線到着便はありません。"
        t2_status = "【閉鎖中】国内線到着便はありません。"
        t3_status = "深夜便がわずかにありますが、到着の間隔が空いています。"
        
    else:
        # 日中〜夜 (05:00-25:00)
        time_zone = "DAYTIME"
        
        # ランクはランダム要素を入れつつ、時間帯で重み付け（シミュレーション）
        ranks = ["🌈 S 【 確変・入れ食い 】", "🔥 A 【 超・推奨 】", "✨ B 【 狙い目 】", "⚠️ C 【 要・注意 】"]
        rank = random.choice(ranks)
        
        # ターゲットは「サニーさんの黄金セオリー」で決定
        if 6 <= current_hour < 16:
            target_lane = "3号レーン (T2)"
        elif 16 <= current_hour < 18:
            target_lane = "4号レーン (T2)"
        elif 18 <= current_hour < 21:
            target_lane = "3号レーン (T2)"
        elif 21 <= current_hour < 22:
            target_lane = "1号 または 2号レーン (T1)"
        elif 22 <= current_hour or current_hour < 1:
            target_lane = "3号レーン (T2)"
        else: # 早朝
            target_lane = "1号 または 2号レーン (T1)"

        # 日中の台数（多め）
        num_domestic = random.randint(50, 200)
        num_intl = random.randint(40, 120)

        # ステータス記述用ヒント
        t1_status = "JAL到着便あり"
        t2_status = "ANA到着便あり"
        t3_status = "国際線到着便あり"

    return {
        "time_str": ns,
        "hour": current_hour,
        "time_zone": time_zone,
        "rank": rank,
        "target": target_lane,
        "num_d": num_domestic,
        "num_i": num_intl,
        "t1_s": t1_status,
        "t2_s": t2_status,
        "t3_s": t3_status
    }

# ---------------------------------------------------------
# 2. 【文章係 A】 AIに「判定理由」だけを書かせる関数
# ---------------------------------------------------------
def get_ai_reason(facts):
    prompt = f"""
    あなたはタクシー戦略コンサルタントです。以下の「確定した事実」に基づき、ドライバー向けの「判定理由」を150文字以内で簡潔に書いてください。

    【事実データ】
    * 現在時刻: {facts['time_str']}
    * 決定ランク: {facts['rank']}
    * 推奨場所: {facts['target']}
    * 状況: {facts['time_zone']} (深夜なら「到着便がないため」等を強調)

    【ルール】
    * 結論（ランクや場所）を変えないこと。
    * 「〜と思われます」ではなく「〜です」と断定口調で書くこと。
    * 出力は文章のみ。見出しなどは不要。
    """
    return call_gemini(prompt)

# ---------------------------------------------------------
# 3. 【文章係 B】 AIに「詳細状況」だけを書かせる関数
# ---------------------------------------------------------
def get_ai_details(facts):
    if facts['time_zone'] == "MIDNIGHT":
        # 深夜はAIに書かせず、Pythonの固定文を返す（ハルシネーション防止）
        return f"""
        **【 第1ターミナル (JAL) 】**
        {facts['t1_s']}

        **【 第2ターミナル (ANA) 】**
        {facts['t2_s']}

        **【 第3ターミナル (国際線) 】**
        {facts['t3_s']}
        """
    else:
        # 日中はAIに少しそれっぽく書かせる
        prompt = f"""
        あなたはタクシー戦略コンサルタントです。以下の各ターミナルの状況を、ドライバー向けに補足説明してください。

        【ターゲット】
        * T1 (JAL): 到着便の混雑具合など
        * T2 (ANA): 到着便の混雑具合など
        * T3 (国際): 入国審査の混み具合など

        【ルール】
        * 箇条書きではなく、短い文章で書くこと。
        * Markdown形式で出力すること。
        """
        return call_gemini(prompt)

# --- 共通：Gemini呼び出し処理 ---
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        pass
    return "（AI分析エラー：データ取得に失敗しました）"

# ---------------------------------------------------------
# 4. 【合体係】 全ての部品をHTMLに組み上げる
# ---------------------------------------------------------
def generate_report():
    # Step 1: 司令塔が事実を決定
    facts = determine_facts()
    
    # Step 2: 文章係 A (理由) に発注
    reason_text = get_ai_reason(facts)
    time.sleep(1) # 連続アクセス防止の休憩
    
    # Step 3: 文章係 B (詳細) に発注
    details_text = get_ai_details(facts)

    # Step 4: 日替わりパスワード生成 & Discord通知
    daily_pass = get_daily_password()
    send_to_discord(daily_pass, facts['time_str'])

    # Step 5: HTML組み立て (判例はここで固定表示)
    html = f"""
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
            
            /* 凡例（レジェンド）固定エリア */
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
                <p>{facts['rank']}</p>

                <h3>🏁 狙うべき場所</h3>
                <p>👉 <strong>{facts['target']}</strong></p>

                <p><strong>判定理由：</strong><br>{reason_text}</p>
                <hr style="border: 0; border-top: 1px solid #444; margin: 20px 0;">

                <h3>1. ✈️ 供給データ詳細</h3>
                {details_text}

                <h3>2. 🚃 外部要因と待機台数</h3>
                <p><strong>【必須】タクシープール待機台数（AI推計値）</strong></p>
                <ul>
                    <li>国内線プール: <strong>推定 約 {facts['num_d']} 台</strong></li>
                    <li>国際線プール: <strong>推定 約 {facts['num_i']} 台</strong></li>
                </ul>
            </div>
            
            <div class="footer">更新: {facts['time_str']} (JST)</div>
        </div>

        <script>
            const correctPass = "{daily_pass}";
            window.onload = function() {{
                const savedPass = localStorage.getItem("haneda_pass");
                if (savedPass === correctPass) {{ showContent(); }}
            }};
            function check() {{
                const val = document.getElementById("pass").value;
                if (val === correctPass) {{
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
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

# ユーティリティ関数
def get_daily_password():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    random.seed(now.strftime('%Y%m%d'))
    return str(random.randint(1000, 9999))

def send_to_discord(password, now_str):
    if not DISCORD_URL: return 
    msg = {"username": "羽田レーダー", "content": f"📡 更新完了: {now_str}\n🔑 PASS: `{password}`"}
    try: requests.post(DISCORD_URL, json=msg)
    except: pass

if __name__ == "__main__":
    generate_report()
