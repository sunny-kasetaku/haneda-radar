import os
import requests
import json
from datetime import datetime, timedelta
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

    # ▼ パスワードは「今日の日付(0122)」に固定
    daily_pass = start_time.strftime('%m%d')
    print(f"LOG: 本日のパスワード -> {daily_pass}")

    # 2. データ取得（ここは300件取ってきますが、画面には出しません）
    flights = fetch_flight_data(CONFIG.get("AVIATION_STACK_API_KEY"))
    
    # 3. 分析（★ここで300件から「直近75分」などの条件で絞り込まれます）
    analysis_result = analyze_demand(flights)
    
    # 4. HTML生成（絞り込まれた結果だけを表示します）
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