import requests
import json
import datetime
import os

# 設定
API_KEY = os.getenv("GEMINI_API_KEY")
# 強制的に「v1」の安定版URLを直接指定します
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def get_prompt(now_time):
    return f"""
【羽田空港・リアルタイム需要分析依頼】
最高顧問、現在の最新データ（フライト到着数・ゲート配分・鉄道運行状況・天気）を収集し、分析ダッシュボードを更新してください。

分析にあたっては以下の条件を厳守すること：
1. 14時〜16時の到着便数と予測降機人数をターミナル別（T1/T2/T3）に算出。
2. 以下の「ベテランドライバーのセオリー」をベースに、今日のリアルタイム要因（鉄道遅延やゲートの偏り）で補正を行うこと。
   [セオリー：6-16時 3号 / 16-18時 4号 / 18-21時 3号 / 21-22時 1か2号 / 22時以降 3号]
3. タクシープール待機台数（推計）と降機人数のギャップを解説に含めること。
4. 回答はすべて一つのコードブロック（ ``` ）内に記述すること。

現在の時刻：{now_time}
"""

def generate_report():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # リクエストデータの作成
    payload = {
        "contents": [{
            "parts": [{"text": get_prompt(now_str)}]
        }]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        # 直接GoogleのAPIサーバーにPOST（送信）します
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        if response.status_code == 200:
            report_content = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # エラーの詳細を表示
            report_content = f"APIエラーが発生しました。\nStatus: {response.status_code}\nMessage: {json.dumps(res_json)}"
            
    except Exception as e:
        report_content = f"通信エラーが発生しました。\n(Error: {e})"
    
    # HTMLの生成
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
            .footer {{ text-align: right; font-size: 0.7rem; color: #888; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div style="font-weight:bold;">🚖 KASETACK</div>
        <h1>羽田空港需要分析（20分更新）</h1>
        <pre>{report_content}</pre>
        <div class="footer">最終更新: {now_str} (JST)</div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_report()
