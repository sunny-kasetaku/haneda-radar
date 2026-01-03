import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # 【最重要】v1beta窓口で、models/gemini-1.5-flash を指名します
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={K}"
    
    prompt = "羽田空港のT1/T2/T3別の現在（16時台）の到着便数と、タクシー需要予測をベテランのセオリーに基づいて短く解説して。"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200:
            # 成功！Geminiの回答を取り出す
            report_content = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # 失敗した場合の理由を表示
            err_msg = res_json.get('error', {}).get('message', '不明なエラー')
            report_content = f"APIエラー: {response.status_code}\n理由: {err_msg}"

    except Exception as e:
        report_content = f"実行エラー: {str(e)}"

    h = f"""
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style='background:#121212;color:#FFD700;padding:20px;font-family:sans-serif;'>
        <h1 style='border-bottom:2px solid #FFD700;'>🚖 羽田需要レーダー</h1>
        <pre style='white-space:pre-wrap;color:#fff;background:#1e1e1e;padding:15px;border-radius:10px;line-height:1.6;'>{report_content}</pre>
        <p style='text-align:right;color:#888;font-size:0.8rem;'>更新:{ns} (JST)</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
