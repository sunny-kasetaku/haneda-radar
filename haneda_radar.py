import requests
import json
import datetime
import os

# APIキーを読み込み
API_KEY = os.getenv("GEMINI_API_KEY")

def get_prompt(now_time):
    return f"""
【羽田空港・リアルタイム需要分析依頼】
最高顧問、現在の最新データ（フライト到着数・ゲート配分・鉄道運行状況・天気）を収集し、分析ダッシュボードを更新してください。
14時〜16時の到着便数と予測降機人数をターミナル別（T1/T2/T3）に算出。
現在の時刻：{now_time}
"""

def generate_report():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # 【最終兵器】URLを1文字ずつのリストにして結合。
    # これによりGitHubの「自動リンク機能」が絶対に発動しません。
    u_parts = [
        'h','t','t','p','s',':','/','/','g','e','n','e','r','a','t','i','v','e',
        'l','a','n','g','u','a','g','e','.','g','o','o','g','l','e','a','p','i','s',
        '.','c','o','m','/','v','1','b','e','t','a','/','m','o','d','e','l','s','/',
        'g','e','m','i','n','i','-','1','.','5','-','f','l','a','s','h',':','g','e','n','e','r','a','t','e','C','o','n','t','e','n','t'
    ]
    full_url = "".join(u_parts) + "?key=" + str(API_KEY)
    
    payload = {
        "contents": [{"parts": [{"text": get_prompt(now_str)}]}]
    }
    headers = {'Content-Type': 'application/json'}

    try:
        # 通信実行
        response = requests.post(full_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200:
            report_content = res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            report_content = f"APIエラー (Status: {response.status_code})\n{json.dumps(res_json, ensure_ascii=False)}"
            
    except Exception as e:
        # エラー発生時は、変な記号を徹底的に排除して表示
        err_msg = str(e).replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        report_content = f"実行エラーが発生しました。\n原因: {err_msg}"
    
    # HTML生成
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
