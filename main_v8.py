import os
import random
from datetime import datetime, timedelta
# api_handler_v2 (中身は最新のv3ロジック) を使用
from api_handler_v2 import fetch_flight_data 
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 1. 現在時刻を「日本時間 (JST)」で確定させる
    now = datetime.utcnow() + timedelta(hours=9)
    today_str = now.strftime('%Y-%m-%d') 
    
    print(f"--- START: {now.strftime('%Y-%m-%d %H:%M:%S')} (JST) ---")

    # 2. パスワード生成 (0-6時は前日ベース)
    # これにより、朝6時の更新までは「昨日のパスワード」が維持されます
    if now.hour < 6:
        pass_date = now - timedelta(days=1)
    else:
        pass_date = now
    random.seed(pass_date.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    print(f"PASS: {daily_pass}")

    # 3. データ取得
    api_key = CONFIG.get("AVIATION_STACK_API_KEY")
    
    # 日本の日付を指定してデータを取得
    print(f"LOG: Force fetching data for DATE: {today_str} (JST)...")
    flights_raw = fetch_flight_data(api_key, date_str=today_str)
    print(f"LOG: Fetched Today's Data: {len(flights_raw)} records")

    # 日またぎ補完 (深夜0時〜4時の間だけ、昨日のデータも追加で拾う)
    # これがないと、深夜0時を過ぎた瞬間に「到着済み」の便が消えてしまうのを防ぐ
    if 0 <= now.hour < 4:
        target_date = now - timedelta(days=1)
        yesterday_str = target_date.strftime('%Y-%m-%d')
        print(f"LOG: Midnight detected. Also fetching YESTERDAY ({yesterday_str})...")
        
        flights_sub = fetch_flight_data(api_key, date_str=yesterday_str)
        flights_raw.extend(flights_sub)
        print(f"LOG: Added Yesterday's Data: +{len(flights_sub)} records")

    # ▼▼▼【犯人探し用デバッグログ】ここにAPIから来た直後の生時間を表示 ▼▼▼
    if len(flights_raw) > 0:
        # api_handler_v2から返ってきたリストの先頭を確認
        # ここが「19:xx」ならAPIがJSTを返している。「10:xx」ならUTC。
        print(f"DEBUG_RAW_CHECK: Flight {flights_raw[0].get('flight_number')} -> Time: {flights_raw[0].get('arrival_time')}")
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    # 4. 旅客便フィルター
    flights = []
    for f in flights_raw:
        if f.get('status') == 'cancelled': continue
        
        airline = str(f.get('airline', '')).lower()
        f_num = str(f.get('flight_number', '')).lower()
        
        # 貨物便を除外
        if 'cargo' in airline or 'cargo' in f_num:
            continue
        
        flights.append(f)

    print(f"LOG: Total Merged {len(flights_raw)} -> Passenger Only {len(flights)}")

    # 5. 分析 & HTML生成
    # 【重要】ここで日本時間(now)を各モジュールに渡します
    # render_html内部で「終電情報（23時台）」や「同点時の優先順位」が処理されます
    analysis_result = analyze_demand(flights, current_time=now)
    render_html(analysis_result, daily_pass, current_time=now)
    
    # 6. Discord通知
    # 修正: 1時間に1回の実行のため、6時台の実行であれば通知を送るように変更
    bot = DiscordBot()
    
    # ★変更箇所: 1時間に1回の実行なので、時間(hour)だけで判定すればOK
    is_notify_time = (now.hour == 6)

    if is_notify_time:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)
    else:
        print(f"LOG: Notification skipped (Current time {now.strftime('%H:%M')} is out of target slot)")

    print("--- END: SUCCESS ---")

if __name__ == "__main__":
    main()