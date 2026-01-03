import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # 1. 成功した「最強のモデル探索ロジック」をそのまま使います
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={K}"
    try:
        models_data = requests.get(list_url).json()
    except Exception as e:
        models_data = {"error": str(e)}

    # deep-researchなどを除外
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
    
    report_content = "有効なモデルが見つかりませんでした。"
    used_model = "None"

    # プロンプト（少しリッチにしました）
    prompt = """
    羽田空港のT1/T2/T3別の現在（16時〜17時）の到着便数と、タクシー需要予測を行ってください。
    ドライバー向けに「どのターミナルを狙うべきか」の結論をズバリ書いてください。
    """
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

    # 2. HTML生成（ここにパスワードロックの仕掛けを組み込みます）
    h = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>KASETACK RADAR</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; margin: 0; }}
            
            /* ログイン画面のデザイン */
            #login-screen {{ 
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: #000; z-index: 999; display: flex; flex-direction: column; 
                justify-content: center; align-items: center; 
            }}
            input {{ padding: 10px; font-size: 1.2rem; border-radius: 5px; border: none; text-align: center; margin-bottom: 20px; width: 60%; }}
            button {{ padding: 10px 30px; font-size: 1rem; background: #FFD700; color: #000; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }}
            
            /* メイン画面のデザイン */
            #main-content {{ display: none; }}
            h1 {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.4rem; letter-spacing: 2px; }}
            pre {{ background: #1e1e1e; padding: 15px; border-radius: 10px; white-space: pre-wrap; color: #fff; border: 1px solid #333; line-height: 1.6; font-size: 0.95rem; }}
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
            <div class="footer">
                更新: {ns} (JST)<br>
                <span class="tag">{used_model}</span>
            </div>
        </div>

        <script>
            function check() {{
                const val = document.getElementById("pass").value;
                // ここでパスワードを設定（今は 777 です）
                if (val === "777") {{
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
