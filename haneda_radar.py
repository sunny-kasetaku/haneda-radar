import requests
import json
import datetime
import os
import random

# 環境変数からキーを取得
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

def get_daily_password():
    """今日の日付を元に4桁のパスワードを生成"""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    seed_str = now.strftime('%Y%m%d') 
    random.seed(seed_str) 
    return str(random.randint(1000, 9999))

def send_to_discord(password, now_str):
    """Discordに通知"""
    if not DISCORD_URL:
        return 
    msg = {
        "username": "カセタク・羽田レーダー",
        "content": f"📡 **羽田需要分析を更新しました** ({now_str})\n\n🔐 **本日の合言葉:** `{password}`\n\nここから確認:\nhttps://sunny-kasetaku.github.io/haneda-radar/"
    }
    try:
        requests.post(DISCORD_URL, json=msg)
    except:
        pass

def generate_report():
    # 現在時刻の取得と「深夜判定」
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour

    # 時間帯による強制モード設定
    if 0 <= current_hour < 5:
        mode_instruction = """
        【現在は深夜(AM 02:00〜05:00)です】
        * 国内線(T1/T2): 到着便はゼロです。需要なし。
        * 国際線(T3): 到着便はまばらです。
        * 判定: 基本的にランクは「C」か「D」になります。「S」や「A」はあり得ません。
        * 推奨: 「国際線プール」一択、または「都内営業推奨」です。
        """
    else:
        mode_instruction = f"""
        【現在は日中(AM {current_hour}:00)です】
        * 通常のフライトスケジュール通りに分析してください。
        """
    
    daily_pass = get_daily_password()
    send_to_discord(daily_pass, ns)

    # ---------------------------------------------------------
    #  【最終修正】「穴埋めタグ方式」に変更
    #   AIに {} の部分を必ず書き換えさせる指示
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】におけるタクシー需要を分析し、レポートを作成してください。

    【重要：現在の状況認識】
    {mode_instruction}

    【記述ルール：穴埋め】
    以下のフォーマットの `{{ }}` で囲まれた部分を、あなたの分析結果に**書き換えて**出力してください。
    * `{{RANK}}` -> 以下のリストから1つ選んで書き換える。
        - 🌈 S 【 確変・入れ食い 】
        - 🔥 A 【 超・推奨 】
        - ✨ B 【 狙い目 】
        - ⚠️ C 【 要・注意 】
        - ⛔ D 【 撤退・非推奨 】
    
    * `{{TARGET}}` -> 以下のリストから1つ選んで書き換える。
        - 👉 「 1 号 レーン (T1) 」
        - 👉 「 2 号 レーン (T1) 」
        - 👉 「 3 号 レーン (T2) 」
        - 👉 「 4 号 レーン (T2) 」
        - 👉 「 国際線プール 」
        - 👉 「 都内営業 (羽田離脱) 」

    * `{{NUM_D}}` -> 国内線プールの待機台数を「数字」で書く (例: 120)。「[数値]」という文字は禁止。
    * `{{NUM_I}}` -> 国際線プールの待機台数を「数字」で書く (例: 50)。「[数値]」という文字は禁止。

    【出力するフォーマット】
    (※ここから下を完成させて出力すること)

    ### 📊 羽田指数
    {{RANK}}
    (参考: S > A > B > C > D)

    ### 🏁 狙うべき場所
    {{TARGET}}

    **判定理由：**
    (ここに、時間帯と需給バランスに基づいた理由を簡潔な文章で書く)

    ---

    ### 1. ✈️ 供給データ詳細
    
    **【 第1ターミナル (JAL) / 1・2号 】**
    (現在の到着便状況を文章で記述)
    
    **【 第2ターミナル (ANA) / 3・4号 】**
    (現在の到着便状況を文章で記述)
    
    **【 第3ターミナル (国際線) 】**
    (現在の到着便状況を文章で記述)

    ### 2. 🚃 外部要因と待機台数
    
    **【必須】タクシープール待機台数（AI推計値）**
    * 国内線プール: **推定 約 {{NUM_D}} 台**
    * 国際線プール: **推定 約 {{NUM_I}} 台**

    ### 3. 🧠 AIロジック解説
    (プロの視点での根拠)
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
