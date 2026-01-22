import os
import requests
import json
import random
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
    print("-" * 50)
    print(f"開始時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (JST)")

    # パスワードはランダムを維持（これがないとログインできないため）
    random.seed(start_time.strftime('%Y%m%d'))
    daily_pass = f"{random.randint(0, 9999):04d}"
    
    print(f"【重要】本日のランダムパスワード: {daily_pass}")
    print("-" * 50)

    # 2. データ取得（フィルターなしの元の状態に戻しました）
    print("📡 データを再取得中（フィルター解除版）...")
    flights = fetch_flight_data(CONFIG.get("AVIATION_STACK_API_KEY"))
    
    print(f"📊 取得件数: {len(flights)}件 (全ての便を分析対象にします)")
    
    # 3. 分析
    analysis_result = analyze_demand(flights)
    
    # 4. HTML生成
    render_html(analysis_result, daily_pass)
    
    # 5. 通知 (Discord)
    bot = DiscordBot()
    if start_time.hour == 6 and 0 <= start_time.minute < 20:
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)

    print("✅ 元の取得条件に戻しました。完了です。")
    print("-" * 50)

if __name__ == "__main__":
    main()
