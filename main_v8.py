import os
import requests
import json
import random
from datetime import datetime, timedelta
# ▼ ここを修正しました（fetch_flights_v2 -> fetch_flight_data）
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand
from renderer_new import render_html
from discord_bot import DiscordBot

# 設定
CONFIG = {
    "AVIATION_STACK_API_KEY": os.environ.get("AVIATION_STACK_API_KEY"),
    "DISCORD_WEBHOOK_URL": os.environ.get("DISCORD_WEBHOOK_URL"),
}

def main():
    # 日本時間 (JST)
    start_time = datetime.utcnow() + timedelta(hours=9)
    print(f"START: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (JST)")

    # パスワード生成 (テスト運用中は日付固定でもOKですが、コード上はランダム版にしておきます)
    # ※もし日付固定のままが良ければ daily_pass = start_time.strftime('%m%d') に戻してください
    daily_pass = str(random.randint(1000, 9999))
    print(f"LOG: 本日のパスワード生成 -> {daily_pass}")

    # 2. データ取得
    # ▼ ここも名前を合わせました
    flights = fetch_flight_data(CONFIG.get("AVIATION_STACK_API_KEY"))
    
    # 3. 分析
    analysis_result = analyze_demand(flights)
    
    # 4. HTML生成
    render_html(analysis_result, daily_pass)
    
    # 5. 通知 (Discord) - 朝6時台のみ
    bot = DiscordBot()
    if start_time.hour == 6 and 0 <= start_time.minute < 20:
        print("LOG: 定時連絡の時間です。Discordに通知を送ります。")
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)
    else:
        print("LOG: 定時連絡外のため、Discord通知はスキップします。")

    print("END")

if __name__ == "__main__":
    main()