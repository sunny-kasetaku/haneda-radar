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
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    daily_pass = get_daily_password()
    send_to_discord(daily_pass, ns)

    # ---------------------------------------------------------
    #  【修正】回答フォーマットから「リスト」を完全撤去
    #   AIに「答え」だけを書かせるスタイルに変更
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】（※24時間表記）におけるタクシー需要を分析し、レポートを作成してください。

    【重要：前提知識】
    * **時刻認識:** 02:00は「深夜」です。14:00は「午後」です。今の時間を正しく認識してください。
    * **場所の定義:**
      - 第1ターミナル (T1/JAL) = **1号・2号レーン**
      - 第2ターミナル (T2/ANA) = **3号・4号レーン**
      - 第3ターミナル (国際線) = **国際線プール**
    * **禁止事項:** - 「空港の運営方針」や「便数を増やすべき」などの政策提言は書かないでください。ドライバーはただ「どこに行けば乗せられるか」を知りたいだけです。

    【分析プロセス（頭の中で考えてください）】
    1. 以下の5段階からランクを1つ決定する。
       (S:入れ食い / A:推奨 / B:狙い目 / C:注意 / D:撤退)
    2. 以下の5箇所から「狙うべき場所」を1つ決定する。
       (1号 / 2号 / 3号 / 4号 / 国際線)

    【回答フォーマット】
    ※ここには選択肢リストを表示せず、**決定した答えだけ**を記入すること。

    ### 📊 羽田指数
    (ここに決定したランク表記を1行だけ書く)
    (参考: S > A > B > C > D)

    ### 🏁 狙うべき場所
    (ここに決定した場所表記を1行だけ書く)
    👉 **「 [決定した場所] 」**

    **判定理由：**
    (現在の時間帯と到着便の状況から、なぜそこを選んだのか、ドライバー向けに簡潔に解説)

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
    (※必ず具体的な数値を推測して入れること)
    * 国内線プール: **推定 約 [数値] 台**
    * 国際線プール: **推定 約 [数値] 台**

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
