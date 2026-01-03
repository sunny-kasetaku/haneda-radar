import requests
import json
import datetime
import os

# GitHubのSecretsからAPIキーを取得
API_KEY = os.getenv("GEMINI_API_KEY")

def get_prompt(now_time):
    return f"""
【羽田空港・リアルタイム需要分析依頼】
最高顧問、現在の最新データを収集し、分析ダッシュボードを更新してください。
14時〜16時の到着便数と予測降機人数をターミナル別（T1/T2/T3）に算出すること。
回答はすべて一つのコードブロック（ ``` ）内に記述すること。
現在の時刻：{now_time}
"""

def generate_report():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # 【修正のキモ】
    # 高級なプレビュー版を避け、確実に無料で動く「gemini-1.5-flash」を直接、
    # かつ余計な記号が入らないように慎重にURLを組み立てます。
    base_url = "[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent)"
    full_url = f"{base_url}?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": get_prompt(now_str)}]}]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        # タイムアウトを長めに設定し、json引数を使って安全に送信
        response = requests.post(full_url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        
        if response.status_code == 200:
            # 成功！
            report_content = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # エラーの詳細を分かりやすく表示
            error_msg = res_json.get('error', {}).get('message', '不明なエラー')
            report_content = f"APIエラーが発生しました。\n状態: {response.status_code}\n内容: {error_msg}"
            
    except Exception as e:
        report_content = f"通信中にエラーが発生しました。\n原因: {str(e)}"
    
    # 見やすいHTMLに流し込む
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>カセタク・羽田レーダー</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: sans-serif; padding: 20px; line-height: 1.6; }}
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
