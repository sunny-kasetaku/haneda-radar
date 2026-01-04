import requests
from bs4 import BeautifulSoup
import datetime
import os
import google.generativeai as genai
import re

# 環境変数
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_haneda_data():
    """
    羽田空港のフライト情報を簡易的に取得
    """
    now = datetime.datetime.now()
    hour = now.hour

    # 簡易シミュレーション
    estimated_arrivals = 10 if 6 <= hour <= 22 else 2
    
    pool_d = 160 - (hour * 2) + estimated_arrivals * 3
    pool_i = 90 - (hour * 1) + estimated_arrivals * 2
    
    info_text = f"""
    【現在時刻: {now.strftime('%H:%M')}】
    到着便数(直近1H): 約{estimated_arrivals}便
    国内線タクシープール(推計): {pool_d}台
    国際線タクシープール(推計): {pool_i}台
    天候: 晴れまたは曇り
    """
    return info_text

def analyze_with_gemini(traffic_info):
    """
    Geminiで分析する（自動モデル検索機能付き）
    """
    if not GEMINI_API_KEY:
        return "⛔ 【設定エラー】 APIキーが GitHub Secrets に登録されていません。"

    genai.configure(api_key=GEMINI_API_KEY)

    prompt = f"""
    あなたは羽田空港のタクシー需要予測のプロです。以下の情報を元に、運転手へのアドバイスを作成してください。
    
    【状況】
    {traffic_info}
    
    【出力フォーマット】
    🚖 KASETACK 羽田需要レーダー
    (ここに S/A/B/C/D のランク付けとアイコン)
    
    📊 羽田指数: (ランク)
    🏁 狙い目: (T1/T2/T3 具体的に)
    👉 理由: (短く鋭く)
    
    (最後に一言、励ましの言葉)
    """

    # ▼▼▼ ここが新機能：使えるモデルを片っ端から試す！ ▼▼▼
    
    # 試す順番リスト
    candidate_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-pro',
        'gemini-1.0-pro'
    ]

    last_error = ""

    # 1. まずは候補リストから試す
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text # 成功したらここで終了！
        except Exception as e:
            last_error = str(e)
            continue # ダメなら次へ

    # 2. 全滅した場合、Googleに「使えるリスト」を聞き出す
    try:
        available_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_list.append(m.name)
        
        return f"""
        ⛔ 【モデルが見つかりません】
        
        指定したモデルが全てエラーでした。
        しかし、現在あなたのアカウントで使えるモデル一覧を取得しました：
        
        ------------------------
        {', '.join(available_list)}
        ------------------------
        
        ※このリストの中に正解があります。
        最後のエラー詳細: {last_error}
        """
    except Exception as e:
        return f"""
        ⛔ 【完全にお手上げ】
        モデル一覧の取得にも失敗しました。APIキー自体が無効な可能性があります。
        エラー詳細: {str(e)}
        """

def update_html(content):
    now = datetime.datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M')
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
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Yu Gothic", sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
            h1 {{ color: #58a6ff; text-align: center; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
            .content {{ white-space: pre-wrap; font-size: 1.1em; background-color: #0d1117; padding: 15px; border-radius: 6px; border: 1px solid #30363d; }}
            .footer {{ margin-top: 25px; text-align: center; font-size: 0.8em; color: #8b949e; }}
            .live-badge {{ display: inline-block; background-color: #238636; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-left: 10px; vertical-align: middle; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚖 羽田需要レーダー <span class="live-badge">LIVE</span></h1>
            <div class="content">
{content}
            </div>
            <div class="footer">
                更新: {time_str} (JST)<br>
                📺 自動更新モード: ON (5分間隔)
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    print("Fetching data...")
    traffic_info = get_haneda_data()
    
    print("Analyzing with Gemini...")
    analysis = analyze_with_gemini(traffic_info)
    
    print("Updating HTML...")
    update_html(analysis)
    print("Done!")

if __name__ == "__main__":
    main()
