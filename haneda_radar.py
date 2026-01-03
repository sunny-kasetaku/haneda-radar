import requests
import json
import datetime
import os

# APIキーを取得
API_KEY = os.getenv("GEMINI_API_KEY")

def get_prompt(now_time):
    return f"""
羽田空港のリアルタイム需要分析を行ってください。
14時〜16時の到着便数と予測降機人数をターミナル別（T1/T2/T3）に算出してください。
現在の時刻：{now_time}
"""

def generate_report():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # 【変更点】バージョンを v1 にし、モデル名を gemini-pro に変更。
    # これが最も多くのAPIキーで「確実に」動く組み合わせです。
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": get_prompt(now_str)}]}]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200:
            report_content = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # 404が出る場合は、予備のモデル（gemini-1.5-flash）で再試行
            url_alt = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            response = requests.post(url_alt, json=payload, timeout=30)
            res_json = response.json()
            if response.status_code == 200:
                report_content = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                report_content = f"APIエラー (Status: {response.status_code})\n{json.dumps(res_json, ensure_ascii=False)}"
            
    except Exception as e:
        report_content = f"実行中にエラーが発生しました。\n原因: {str(e)}"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>カセタク・羽田レーダー</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: sans-serif; padding: 20px; }}
            h1 {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.2rem; }}
            pre {{ background: #1e1e1e; padding: 15px; border-radius: 10px; white-space: pre-wrap; color: #fff; border: 1px solid #333; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div style="font-weight:bold;">🚖 KASETACK</div>
        <h1>羽田空港需要分析</h1>
        <pre>{report_content}</pre>
        <div style="text-align:right; font-size:0.7rem; color:#888; margin-top:20px;">最終更新: {now_str}</div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_report()
