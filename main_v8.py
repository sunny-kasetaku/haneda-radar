# main_v8.py (Final Integration)
# ---------------------------------------------------------
# 羽田空港タクシー需要予測システム v8.4
# ---------------------------------------------------------
import os
import requests
from datetime import datetime
from config import CONFIG 

# ★修正済みの api_handler_v2 を読み込む
from api_handler_v2 import fetch_flights_v2
import analyzer_v2 as analyzer
import renderer_new as renderer
import discord_bot as bot

def main():
    start_time = datetime.now()
    print(f"START: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. パスワード生成 (Rendererへ渡す用)
    daily_pass = start_time.strftime('%m%d') 

    # 2. データ取得
    # ★ここで修正した api_handler_v2 を使います！
    # 3ページ分(300件)取得し、Analyzer用に整形されたデータが返ってきます
    flights = fetch_flights_v2(target_airport="HND", pages=3)
    
    if not flights:
        print("WARNING: データが0件のため終了します")
        return

    # 3. 分析
    # 整形済みデータなので、Analyzerにそのまま渡してOK
    try:
        results = analyzer.analyze_demand(flights)
        print("✅ 分析完了")
    except Exception as e:
        print(f"❌ Analyzer Error: {e}")
        return

    # 4. 描画 & 保存
    try:
        renderer.generate_html_new(results, daily_pass)
        print("✅ HTML生成完了")
    except Exception as e:
        print(f"❌ Renderer Error: {e}")

    # 5. 通知 (Discord)
    # 朝6時00分〜15分の間だけ通知
    if start_time.hour == 6 and 0 <= start_time.minute < 15:
        print("LOG: 定時連絡の時間です")
        bot.send_daily_info(CONFIG.get("DISCORD_WEBHOOK_URL"), daily_pass)
    else:
        print("LOG: 定時連絡外のため通知スキップ")

    print("END")

if __name__ == "__main__":
    main()