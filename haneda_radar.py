import requests
from bs4 import BeautifulSoup
import datetime
import os
import google.generativeai as genai

# 設定
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_haneda_traffic():
    # 羽田空港のフライト情報を取得（T1, T2, T3）
    # ※簡易的なスクレイピング例です。実際のURLに合わせて調整してください
    url = "https://tokyo-haneda.com/flight/flightInfo_dms.html" # 例
    # ここではエラーにならないよう、ダミーデータで枠組みを作ります
    # 実際にはここにBeautifulSoupの解析ロジックが入ります
    return "到着便数：平年並み" 

def analyze_with_gemini(traffic_info):
    if not GEMINI_API_KEY:
        return "⚠️ 設定エラー: APIキーが見つかりません"
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    羽田空港のタクシー需要を予測してください。
    現在は {datetime.datetime.now().strftime('%H:%M')} です。
    
    【状況】
    {traffic_info}
    
    タクシードライバー向けに、以下のフォーマットで短く出力してください。
    
    🚖 KASETACK 羽田需要レーダー
    🌈 S:入れ食い / 🔥 A:超推奨 / ✨ B:狙い目 / ⚠️ C:要注意 / ⛔ D:撤退
    
    📊 羽田指数: [ここにランク]
    🏁 狙うべき場所: [T1/T2/T3のどこか]
    👉 理由: [ひとこと]
    
    (最後に励ましの言葉)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI分析エラー: {str(e)}"

def update_html(content):
    now = datetime.datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M')
    
    # ▼▼▼ ここが魔法の行です！ (content="300" は300秒=5分ごとにリロードの意味) ▼▼▼
    meta_refresh = '<meta http-equiv="refresh" content="300">'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {meta_refresh}
        <title>羽田タクシー需要レーダー</title>
        <style>
            body {{ font-family: sans-serif; background-color: #1a1a1a; color: #fff; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #2d2d2d; padding: 20px; border-radius: 10px; }}
            h1 {{ color: #4dabf7; text-align: center; }}
            .content {{ white-space: pre-wrap; font-size: 1.1em; }}
            .footer {{ margin-top: 20px; text-align: center; font-size: 0.8em; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚖 羽田需要レーダー</h1>
            <div class="content">
{content}
            </div>
            <div class="footer">
                更新: {time_str} (JST)<br>
                自動更新モード稼働中 (5分毎)
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    print("Fetching data...")
    traffic_info = get_haneda_traffic()
    
    print("Analyzing with Gemini...")
    analysis = analyze_with_gemini(traffic_info)
    
    print("Updating HTML...")
    update_html(analysis)
    print("Done!")

if __name__ == "__main__":
    main()
