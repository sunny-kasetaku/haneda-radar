import google.generativeai as genai
from google.generativeai.types import RequestOptions
import datetime
import os

# APIの設定
api_key = os.getenv("GEMINI_API_KEY")

# 【修正ポイント】APIのバージョンを強制的に "v1" (安定版) に固定します
genai.configure(
    api_key=api_key,
    transport='rest',
    client_options={'api_version': 'v1'}
)

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
    # 日本時間を取得
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    # モデルの指定（安定版のパスを指定）
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # リクエスト時にもオプションを念押しで指定
        response = model.generate_content(
            get_prompt(now_str)
        )
        report_content = response.text
    except Exception as e:
        report_content = f"分析中にエラーが発生しました。\n(Error: {e})"
    
    # HTMLの生成
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>カセタク・羽田レーダー</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: sans-serif; padding: 20px; }}
            h1 {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.2rem; color: #FFD700; }}
            pre {{ background: #1e1e1e; padding: 15px; border-radius: 10px; white-space: pre-wrap; color: #fff; border: 1px solid #333; line-height: 1.6; font-size: 0.9rem; }}
            .footer {{ text-align: right; font-size: 0.7rem; color: #888; margin-top: 20px; }}
            .logo {{ font-weight: bold; color: #FFD700; margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="logo">🚖 KASETACK</div>
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
