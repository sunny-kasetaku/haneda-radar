import os
import random
from datetime import datetime, timedelta
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 日本時間 (JST)
    now = datetime.utcnow() + timedelta(hours=9)
    print(f"--- START: {now.strftime('%Y-%m-%d %H:%M:%S')} (JST) ---")

    # ==========================================
    # 🔑 1. パスワード生成ロジック (深夜対応版)
    # ==========================================
    # 【変更点】
    # 00:00 〜 05:59 までは「前日の日付」を使ってパスワードを作るように変更。
    # これで夜勤中のドライバーは朝6時まで同じパスワードでログインし続けられます。
    if now.hour < 6:
        pass_date = now - timedelta(days=1)
    else:
        pass_date = now
        
    random.seed(pass_date.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    print(f"PASS: {daily_pass} (Base Date: {pass_date.strftime('%Y-%m-%d')})")

    # ==========================================
    # ✈️ 2. データ取得ロジック (日またぎ対応版)
    # ==========================================
    api_key = CONFIG.get("AVIATION_STACK_API_KEY")
    
    # (A) 今日のデータを取得 (既存維持)
    flights_raw = fetch_flight_data(api_key)
    print(f"LOG: Fetched Today's Data: {len(flights_raw)} records")

    # (B) 【追加点】深夜(00:00〜03:59)なら、昨日のデータも取りに行く
    # 国際線などは「出発日」で管理されるため、日付をまたぐと今日のデータに出てこない対策。
    # これで深夜の「国際線ゼロ」バグが直ります。
    if 0 <= now.hour < 4:
        yesterday_str = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"LOG: Midnight detected. Fetching yesterday's data ({yesterday_str})...")
        
        # 日付指定で追加取得 (api_handler_v2の改修が必要)
        flights_yesterday = fetch_flight_data(api_key, date_str=yesterday_str)
        flights_raw.extend(flights_yesterday)
        print(f"LOG: Added Yesterday's Data: +{len(flights_yesterday)} records")

    # 3. 鉄壁の旅客便フィルター (既存維持)
    # ※ここ重要：Cargo除外ロジックはそのまま残しています
    flights = []
    for f in flights_raw:
        if f.get('status') == 'cancelled': continue
        
        airline = str(f.get('airline', '')).lower()
        f_num = str(f.get('flight_number', '')).lower()
        
        if 'cargo' in airline or 'cargo' in f_num:
            continue
        
        flights.append(f)

    print(f"LOG: Total Merged {len(flights_raw)} -> Passenger Only {len(flights)}")

    # 4. 分析 & HTML生成 (既存維持)
    analysis_result = analyze_demand(flights)
    render_html(analysis_result, daily_pass)
    
    # 5. Discord通知 (朝6時台のみ)
    bot = DiscordBot()
    
    # 【維持】二重投稿防止ロジック (< 8分) はそのまま残しています
    if now.hour == 6 and 0 <= now.minute < 8:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)

    print("--- END: SUCCESS ---")

if __name__ == "__main__":
    main()
