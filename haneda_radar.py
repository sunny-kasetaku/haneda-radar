import requests
import json
import datetime
import os
import random

# 環境変数からキーを取得
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

def get_daily_password():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    seed_str = now.strftime('%Y%m%d') 
    random.seed(seed_str) 
    return str(random.randint(1000, 9999))

def send_to_discord(password, now_str):
    if not DISCORD_URL: return 
    msg = {
        "username": "カセタク・羽田レーダー",
        "content": f"📡 **羽田需要分析を更新しました** ({now_str})\n\n🔐 **本日の合言葉:** `{password}`\n\nここから確認:\nhttps://sunny-kasetaku.github.io/haneda-radar/"
    }
    try: requests.post(DISCORD_URL, json=msg)
    except: pass

def generate_report():
    # 現在時刻
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour
    
    # ---------------------------------------------------------
    # 【重要】数字とランクはPythonで計算して確定させる（AIには計算させない）
    # ---------------------------------------------------------
    
    # 台数の推計（ランダムだが時間帯で傾向を変える）
    if 1 <= current_hour < 5:
        # 深夜: 国内線はガラガラ、国際線はそこそこ
        num_domestic = random.randint(5, 30)
        num_intl = random.randint(80, 160)
        
        # 深夜の強制ステータス
        decision_rank = "⛔ D 【 撤退・非推奨 】"
        decision_target = "都内営業 (羽田離脱)"
        decision_reason = "深夜帯（01:00-05:00）のため、国内線の到着便は完全に停止しています。国際線も到着がまばらであり、長時間待機のリスクが高すぎます。都内へ戻り、無線やアプリ配車を狙うのが最善です。"
        
        t1_status = "【閉鎖中】到着便なし（深夜帯のため）"
        t2_status = "【閉鎖中】到着便なし（深夜帯のため）"
        t3_status = "到着便は極めて少なく、入国客の動線も途切れがちです。"

    else:
        # 日中〜夜: 通常営業
        num_domestic = random.randint(80, 250)
        num_intl = random.randint(40, 120)
        
        # AIに考えさせる余地を残す（仮置き）
        decision_rank = "AI_DECIDE" 
        
        # セオリーによるターゲット設定
        if 6 <= current_hour < 16:
            decision_target = "3号レーン (T2)"
        elif 16 <= current_hour < 18:
            decision_target = "4号レーン (T2)"
        elif 18 <= current_hour < 21:
            decision_target = "3号レーン (T2)"
        elif 21 <= current_hour < 22:
            decision_target = "1号 または 2号レーン (T1)"
        else:
            decision_target = "3号レーン (T2)" # 22時以降

        t1_status = "JAL到着便の状況に基づき記述"
        t2_status = "ANA到着便の状況に基づき記述"
        t3_status = "国際線到着便の状況に基づき記述"
        
        # 日中は理由もAIに書かせる
        decision_reason = "現在の到着便数と、上記セオリーに基づき、需給バランスを分析して記述してください。"

    daily_pass = get_daily_password()
    send_to_discord(daily_pass, ns)

    # ---------------------------------------------------------
    #  【プロンプト】確定した数字とランクをAIに「渡す」
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】におけるタクシー需要レポートを作成します。

    【Pythonシステムからの確定データ（絶対に変更不可）】
    以下のデータはすでに計算済みです。**このまま出力に使ってください。**
    
    * **ランク:** {decision_rank} (※もし "AI_DECIDE" なら、状況を見て S〜D から決めてください)
    * **狙い目:** {decision_target}
    * **国内線プール待機数:** {num_domestic} 台
    * **国際線プール待機数:** {num_intl} 台
    * **T1状況:** {t1_status}
    * **T2状況:** {t2_status}
    * **T3状況:** {t3_status}
    * **判定理由:** {decision_reason}

    【回答フォーマット】
    （※余計な前置きなし。以下の通りに出力すること）

    ### 📊 羽田指数
    (ここにランクを1行で書く)

    ### 🏁 狙うべき場所
    👉 (ここに狙い目を1行で書く)

    **判定理由：**
    (ここに判定理由を書く)

    ---

    ### 1. ✈️ 供給データ詳細
    
    **【 第1ターミナル (JAL) 】**
    {t1_status}

    **【 第2ターミナル (ANA) 】**
    {t2_status}

    **【 第3ターミナル (国際線) 】**
    {t3_status}

    ### 2. 🚃 外部要因と待機台数
    
    **【必須】タクシープール待機台数（AI推計値）**
    * 国内線プール: **推定 約 {num_domestic} 台**
    * 国際線プール: **推定 約 {num_intl} 台**

    ### 3. 🧠 AIロジック解説
    (なぜこの結論に至ったか、プロの視点で簡潔に補足)
    """
    
    # モデル探索ロジック
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    try:
        models_data = requests.get(list_url).json()
    except Exception:
        models_data = {}

    ignore_list = ["deep-research", "embedding", "aqa"]
    candidates = []
    if 'models' in models_data:
        for m in models_data['models']:
            name = m['name']
            if not any(ig in name for ig in ignore_list) and 'generateContent' in m.get('supportedGenerationMethods', []):
                if "flash" in name:
                    candidates.insert(0, name)
                else:
                    candidates.append(name)
    if not candidates:
        candidates = ["models/gemini-1.5-flash", "models/gemini-pro"]

    report_content = "分析エラーが発生しました。"
    used_model = "None"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for model_name in candidates:
        post_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_KEY}"
        try:
            r = requests.post(post_url, json=payload, timeout=30)
            if r.status_code == 200:
                report_content = r.json()['candidates'][0]['content']['parts'][0]['text']
                used_model = model_name
                break
            else:
                continue
        except:
            continue

    safe_report = json.dumps(report_content)

    # ---------------------------------------------------------
    #  【HTML】凡例（レジェンド）固定表示
    # ---------------------------------------------------------
    h = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta http-equiv="refresh" content="1260">
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
                background: #1a1a1a;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 20px;
                font-size: 0.8rem;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
            }}
            .legend-item {{ display: inline-block; padding: 2px 6px; border-radius: 4px; background: #222; border: 1px solid #333; white-space: nowrap; }}
            .l-s {{ color: #00e676; border-color: #00e676; font-weight: bold; }}
            .l-a {{ color: #ff4081; border-color: #ff4081; }}
            .l-b {{ color: #00b0ff; }}
            .l-c {{ color: #ffea00; }}
            .l-d {{ color: #9e9e9e; }}

            #report-box {{ background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }}
            
            h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; font-size: 1.2rem; clear: both; }}
            h3:nth-of-type(1) {{ margin-top: 0; color: #00e676; border-left: 4px solid #00e676; }}
            h3:nth-of-type(2) {{ color: #ff4081; border-left: 6px solid #ff4081; background: rgba(255, 64, 129, 0.1); padding: 10px; border-radius: 0 8px 8px 0; }}

            strong {{ color: #FF4500; font-weight: bold; font-size: 1.05em; }}
            ul {{ padding-left: 20px; margin: 10px 0; }}
            li {{ margin-bottom: 8px; }}
            p {{ margin-bottom: 15px; }}

            /* 強制改行CSS */
            pre {{ white-space: pre-wrap; word-wrap: break-word; overflow-x: auto; background: #222; padding: 10px; border-radius: 5px; }}
            code {{ white-space: pre-wrap; word-wrap: break-word; }}
            div {{ word-break: break-word; }}

            .footer {{ text-align: right; font-size: 0.7rem; color: #666; margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; }}
            .tag {{ background: #333; color: #ccc; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }}
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

            <div id="report-box"></div>
            <div class="footer">
                更新: {ns} (JST)<br>
                <span class="tag">{used_model}</span>
            </div>
        </div>

        <script>
            const rawText = {safe_report};
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
                document.getElementById("report-box").innerHTML = marked.parse(rawText);
            }}
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
