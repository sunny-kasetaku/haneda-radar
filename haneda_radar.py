import requests
import json
import datetime
import os
import random

# 環境変数からキーを取得
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

def get_daily_password():
    """
    今日の日付を「種（シード）」にして、ランダムな4桁のパスワードを作る。
    これなら、同じ日なら何度実行しても同じパスワードになり、
    日付が変わると勝手に新しいパスワードに切り替わる。
    """
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    seed_str = now.strftime('%Y%m%d') # 例: 20260103
    random.seed(seed_str) # 日付で固定
    return str(random.randint(1000, 9999))

def send_to_discord(password, now_str):
    """Discordにパスワードと更新通知を送る"""
    if not DISCORD_URL:
        return # URLが設定されてなければ何もしない

    # メッセージの中身
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
    
    # 日替わりパスワード生成
    daily_pass = get_daily_password()
    
    # Discordに通知（毎回通知がいきます。ウザければここを調整可能）
    send_to_discord(daily_pass, ns)

    # ---------------------------------------------------------
    #  プロンプト（デザイン強化版維持）
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】におけるタクシー需要を分析し、レポートを作成してください。

    【重要：書き方のルール】
    * **Markdown形式**を使って、見やすく装飾してください。
    * 重要な数字（台数や便数）や「結論」は、**太字** (例: **約200台**) にしてください。
    * 見出しには `###` を使ってください。

    【分析条件】
    1. 直近1時間の到着便を推測。特にT2の「3号(北)」vs「4号(南)」の偏りを具体的に。
    2. タクシープール待機台数は、状況からの「推計値」を算出し、必ず数値で書くこと。（※推計である旨の注釈を入れること）

    【回答フォーマット】

    ### 1. ✈️ 供給データ（到着便・詳細ゲート配分）
    (T1/T2/T3の状況。T2の南北の偏りを強調)

    ### 2. 🚃 外部要因と待機台数
    (鉄道・天気)
    
    **【必須】タクシープール待機台数（AI推計値）**
    ※過去の傾向からの予測であり、実測値ではありません。
    * 国内線プール (P1/P2): **推定 約 〇〇〇 台** (コメント)
    * 国際線プール (P3): **推定 約 〇〇〇 台** (コメント)

    ### 3. 🧠 AIロジック解説
    (プロの視点での根拠)

    ### 4. 🏁 最終推奨アクション
    👉 推奨乗り場： **【 〇〇ターミナル・〇〇番 】**
    (具体的な立ち回りアドバイス)
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

    # HTML生成（自動更新機能付き）
    # 日替わりパスワードを埋め込みます
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
            h3 {{ color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; font-size: 1.2rem; }}
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
            // Pythonで作られた「今日の日替わりパスワード」
            const correctPass = "{daily_pass}";

            // 以前入力したパスワードをブラウザに覚えさせておく
            window.onload = function() {{
                const savedPass = localStorage.getItem("haneda_pass");
                if (savedPass === correctPass) {{
                    showContent();
                }}
            }};

            function check() {{
                const val = document.getElementById("pass").value;
                if (val === correctPass) {{
                    // 正解ならブラウザに保存（今日一日は再入力不要）
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
