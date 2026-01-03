import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # 1. まず「使えるモデルのリスト」を取得（これは成功することが分かっています）
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={K}"
    try:
        models_data = requests.get(list_url).json()
    except Exception as e:
        models_data = {"error": str(e)}

    # 2. リストから「generateContent」が使えるモデルだけを抜き出す
    # ※有料の「deep-research」などは除外リストに入れます
    ignore_list = ["deep-research", "embedding", "aqa"]
    candidates = []
    
    if 'models' in models_data:
        for m in models_data['models']:
            name = m['name'] # 例: models/gemini-1.5-flash
            # 除外キーワードが入っていなくて、生成機能があるものを候補にする
            if not any(ig in name for ig in ignore_list) and 'generateContent' in m.get('supportedGenerationMethods', []):
                # flashを優先的にリストの先頭に持ってくる
                if "flash" in name:
                    candidates.insert(0, name)
                else:
                    candidates.append(name)
    
    # 3. 候補を上から順番に叩いて、返事が来たやつを採用する
    report_content = "有効なモデルが見つかりませんでした。\n(APIリスト取得結果: " + str(len(candidates)) + "個の候補)"
    used_model = "None"

    prompt = "羽田空港のT1/T2/T3別の現在（16時台）の到着便数と、タクシー需要予測を短く教えて。"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for model_name in candidates:
        # URLを組み立て（リストにある名前をそのまま使うので404になりません）
        post_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={K}"
        try:
            r = requests.post(post_url, json=payload, timeout=30)
            if r.status_code == 200:
                # 成功！
                report_content = r.json()['candidates'][0]['content']['parts'][0]['text']
                used_model = model_name
                break # 成功したらループ終了
            else:
                # 失敗したら次へ（エラー内容は無視）
                continue
        except:
            continue

    # HTML出力
    h = f"""
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style='background:#121212;color:#FFD700;padding:20px;font-family:sans-serif;'>
        <h1 style='border-bottom:2px solid #FFD700;'>🚖 羽田需要レーダー</h1>
        <pre style='white-space:pre-wrap;color:#fff;background:#1e1e1e;padding:15px;border-radius:10px;line-height:1.6;'>{report_content}</pre>
        <p style='text-align:right;color:#888;font-size:0.8rem;'>更新:{ns} (JST)<br>モデル:{used_model}</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
