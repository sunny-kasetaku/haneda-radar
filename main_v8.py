# main_v8.py
# ---------------------------------------------------------
# 羽田空港タクシー需要予測システム v8.2 Main Controller (GitHub版)
# ---------------------------------------------------------
import os
import json
import random
import requests
from datetime import datetime

# モジュール読み込み
import analyzer_v2 as analyzer
import renderer_new as renderer
import discord_bot as bot

# ==========================================
# 設定エリア
# ==========================================

# ★ GitHub ActionsのSecretsからキーを読み込みます
# ※ GitHubのSecrets名が "AVIATIONSTACK_API_KEY" である前提です。
#    もし違う名前（例: "API_KEY"）で登録している場合は、ここを書き換えてください。
API_KEY = os.environ.get("AVIATIONSTACK_API_KEY")

# ★ 有料版なので HTTPS でOK
BASE_URL = "https://api.aviationstack.com/v1/flights"

# DiscordのURLも環境変数、なければ直書き設定など、既存の設定に合わせてください
# (ここでは環境変数推奨ですが、もし動かないなら直書きでもGitHub SecretsならOKです)
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL") 
# もし環境変数に入れてないなら、以下のように書き換えてください
# DISCORD_URL = "https://discord.com/api/webhooks/..."

SECRET_FILE = "secret.json" 

def get_today_password():
    today_str = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, 'r') as f:
                data = json.load(f)
                if data.get('date') == today_str:
                    return data.get('password')
        except:
            pass
    new_pass = f"{random.randint(0, 9999):04d}"
    with open(SECRET_FILE, 'w') as f:
        json.dump({"date": today_str, "password": new_pass}, f)
    print(f"LOG: 本日の新パスワードを生成しました: {new_pass}")
    return new_pass

def get_flight_data():
    """
    Aviationstack API (有料版/HTTPS) からデータを取得
    """
    if not API_KEY:
        print("⚠️ ERROR: APIキーが読み込めません。GitHub Secretsの設定名を確認してください。")
        return []

    # APIリクエスト用パラメータ
    params = {
        'access_key': API_KEY,
        'arr_iata': 'HND',        
        'limit': 100,             
        'flight_status': 'active,landed,scheduled' 
    }

    try:
        print(f"LOG: APIデータを取得中... ({BASE_URL})")
        # タイムアウト設定を追加して安全に
        response = requests.get(BASE_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            json_data = response.json()
            if 'error' in json_data:
                print(f"❌ API Error: {json_data['error']}")
                return []
            
            flights = json_data.get('data', [])
            print(f"✅ 取得成功: {len(flights)} 件のフライトデータ")
            return flights
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text) # エラー詳細を表示
            return []

    except Exception as e:
        print(f"❌ System Error (get_flight_data): {e}")
        return []

def main():
    start_time = datetime.now()
    print(f"START: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    daily_pass = get_today_password()

    # 1. データ取得
    flights = get_flight_data()
    
    if not flights:
        print("WARNING: フライトデータが取得できなかったため、処理を中断します。")
        return

    # 2. 分析
    try:
        results = analyzer.analyze_demand(flights)
    except Exception as e:
        print(f"❌ Analyzer Error: {e}")
        return

    # 3. 描画
    try:
        renderer.generate_html_new(results, daily_pass)
        print("SUCCESS: HTML更新完了")
    except Exception as e:
        print(f"❌ Renderer Error: {e}")

    # 4. 通知 (朝6時台の定時連絡)
    # ※テスト実行（Run workflow）ですぐに通知を確認したい場合は、
    #   一時的にこの if文をコメントアウトして bot.send_daily_info を強制実行させると便利です。
    if start_time.hour == 6 and 0 <= start_time.minute < 15:
        print("LOG: 定時連絡の時間です。Discordに通知を送ります。")
        bot.send_daily_info(DISCORD_URL, daily_pass)
    else:
        print("LOG: 定時連絡の時間ではないため、Discord通知はスキップします")

    print("END")

if __name__ == "__main__":
    main()