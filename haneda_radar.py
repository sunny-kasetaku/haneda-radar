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
    #  【最終調整】「判定理由」を詳しく語らせるように修正
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】におけるタクシー需要を分析し、レポートを作成してください。

    【ドライバーの常識（レーン知識）】
    * **国内線**には4つのレーンがあり、選択が必要です。
      - **1号・2号**：第1ターミナル (JAL系) 行き
      - **3号・4号**：第2ターミナル (ANA系) 行き (3号=北側 / 4号=南側)
    * **国際線 (T3)** には行き先別レーン番号はありません。「国際線プール」がひとつあるだけです。

    【分析条件】
    1. 現在の到着便状況から、ドライバーが向かうべき最適な場所を断定してください。
    2. 羽田指数（ランク）を以下の5段階の定義に基づいて判定し、ランク表記（🌈 S...など）を書いてください。
       - **🌈 S 【 確変・入れ食い 】** : 客があふれている。空車不足。即座に向かうべき。
       - **🔥 A 【 超・推奨 】** : 回転が非常に早い。積極的に狙うべき。
       - **✨ B 【 狙い目 】** : 需給バランスが良い。標準的な待ち時間で行ける。
       - **⚠️ C 【 要・注意 】** : 待機台数がやや多い。タイミング次第では待つ。
       - **⛔ D 【 撤退・非推奨 】** : 供給過多で動かない。都内営業推奨。

    3. **【重要】判定理由の書き方（熱量重視）**
       箇条書きや機械的なデータ列挙は禁止です。
       ベテランの戦略家として、**「なぜ今、そこが熱いのか？」**を文章で詳しく解説してください。
       「到着便がラッシュを迎えているのに、プールには車がいないため、まさに空車不足の緊急事態です」のように、**需給バランスの歪み**を強調して描写すること。

    4. **【重要】数値の書き方**
       「〇〇〇」や「xxx」といった伏せ字は絶対禁止。必ず推測した「数字（例: 120）」を書くこと。

    【回答フォーマット】
    ※Markdownを使用。重要な数字は太字。
    ※指示文（「～を書くこと」など）は出力しないこと。

    ### 📊 羽田指数：ランク S〜D
    (※ここに判定されたランク表記「🌈 S 【 確変・入れ食い 】」などを大きく書く)
    
    **判定理由：**
    (ここに、プロの視点での詳しい解説文章を書く)

    ### 🏁 【結論】狙うべき場所
    
    (※以下の5つの選択肢から1つを選んで、そのまま書くこと)
    # 👉 **「 1 号 レーン 」**
    # 👉 **「 2 号 レーン 」**
    # 👉 **「 3 号 レーン 」**
    # 👉 **「 4 号 レーン 」**
    # 👉 **「 国際線プール 」**
    (※ランクDの場合は「都内営業を推奨」と書く)

    ### 1. ✈️ 供給データ詳細
    
    **【 第1ターミナル (JAL) 】**
    (1号・2号の状況...)

    **【 第2ターミナル (ANA) 】**
    (3号・4号の状況...)

    **【 第3ターミナル (国際線) 】**
    (国際線プールの状況...)

    ### 2. 🚃 外部要因と待機台数
    (鉄道・天気)
    **【必須】タクシープール待機台数（AI推計値）**
    ※「〇〇〇」禁止。数値を予測して書く。
    * 国内線プール: **推定 約 (数値) 台**
    * 国際線プール: **推定 約 (数値) 台**

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
            
            /* 見出しのスタイル */
            h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; font-size: 1.2rem; }}
            
            /* 羽田指数（ランク）を目立たせる */
            h2 {{ font-size: 1.8rem; margin: 10px 0; }}
            
            /* 結論部分（乗り場）を目立たせる */
            h1 {{ font-size: 1.8rem; color: #ff4081; border-bottom: 2px solid #ff4081; padding-bottom: 5px; display: inline-block; }}

            strong {{ color: #FF4500; font-weight: bold; font-size: 1.05em; }}
            ul {{ padding-left: 20px; margin: 10px 0; }}
            li {{ margin-bottom: 8px; }}
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
