import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # ---------------------------------------------------------
    #  【改修ポイント】プール台数は「推計（目安）」であることを強調する指示を追加
    # ---------------------------------------------------------
    prompt = f"""
    あなたはハイヤー・タクシー業界の「最高戦略顧問」です。
    羽田空港の現在の時刻【{ns}】におけるタクシー需要を分析し、以下のフォーマットを厳守してレポートを作成してください。

    【分析条件】
    1. 現在時刻から「直近1時間」の到着便を、標準的なフライトスケジュールに基づいて推測すること。
    2. 特に第2ターミナル（T2）は、ANAの到着便が「3号（北）」と「4号（南）」のどちらに偏っているかを、便名（NHxxxなど）を挙げて具体的に推測すること。
    3. タクシープール待機台数は、現在の状況から算出した「推計値」を記載し、実測値ではないことを注釈として添えること。

    【回答フォーマット（この構成・絵文字を必ず守ること）】

    1. ✈️ 供給データ（到着便・詳細ゲート配分）
    --------------------------------------------------
    ここにT1/T2/T3それぞれの到着便数、予測客数、期待度（高・極高など）を記載。
    【重要】T2については「3号乗り場（北）」と「4号乗り場（南）」のどちらに大型機が着くか、便名を挙げて詳細に書くこと。

    2. 🚃 外部要因（ライバル・待機状況）
    --------------------------------------------------
    ・鉄道運行状況：遅延リスクや混雑状況。
    ・天候状況：天気と気温。
    
    【必須】タクシープール待機台数（AI推計値）
    ※以下は過去の傾向からの予測であり、リアルタイムの実測値ではありません。
    ・国内線プール (P1/P2): 推定 約 〇〇〇 台（回転状況のコメント）
    ・国際線プール (P3): 推定 約 〇〇〇 台（待機時間の目安）

    3. 🧠 AIのロジック解説（判断の根拠）
    --------------------------------------------------
    「セオリーではこうだが、今日はここが違う」というプロの視点での解説。
    ゲートの偏りや、人の流れ（吐き出し）のタイミングを考慮したロジックを展開。

    4. 🏁 最終推奨アクション
    --------------------------------------------------
    👉 推奨乗り場：【 ターミナル名・乗り場番号 】
    具体的な立ち回りアドバイス。
    """
    # ---------------------------------------------------------

    # モデル探索ロジック
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={K}"
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
        post_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={K}"
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

    # HTML生成（パスワード: 777）
    h = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>KASETACK RADAR</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; margin: 0; }}
            #login-screen {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
            input {{ padding: 10px; font-size: 1.2rem; border-radius: 5px; border: none; text-align: center; margin-bottom: 20px; width: 60%; }}
            button {{ padding: 10px 30px; font-size: 1rem; background: #FFD700; color: #000; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }}
            #main-content {{ display: none; }}
            h1 {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.4rem; letter-spacing: 2px; }}
            pre {{ background: #1e1e1e; padding: 15px; border-radius: 10px; white-space: pre-wrap; color: #fff; border: 1px solid #333; line-height: 1.6; font-size: 0.9rem; font-family: sans-serif; }}
            .footer {{ text-align: right; font-size: 0.7rem; color: #666; margin-top: 20px; }}
            .tag {{ background: #333; color: #ccc; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; }}
        </style>
    </head>
    <body>
        <div id="login-screen">
            <div style="font-size: 3rem; margin-bottom: 20px;">🔒</div>
            <div style="color: #FFD700; margin-bottom: 20px; font-weight: bold;">KASETACK MEMBER</div>
            <input type="password" id="pass" placeholder="Password" />
            <button onclick="check()">UNLOCK</button>
            <p id="msg" style="color: red; margin-top: 10px;"></p>
        </div>
        <div id="main-content">
            <div style="font-weight:900; font-size: 1.2rem;">🚖 KASETACK</div>
            <h1>羽田需要レーダー</h1>
            <pre>{report_content}</pre>
            <div class="footer">更新: {ns} (JST)<br><span class="tag">{used_model}</span></div>
        </div>
        <script>
            function check() {{
                if (document.getElementById("pass").value === "777") {{
                    document.getElementById("login-screen").style.display = "none";
                    document.getElementById("main-content").style.display = "block";
                }} else {{
                    document.getElementById("msg").innerText = "パスワードが違います";
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
