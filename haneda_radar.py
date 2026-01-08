# ==========================================
# Project: KASETACK - haneda_radar.py
# ==========================================
import requests
from datetime import datetime, timezone, timedelta
from config import CONFIG
from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def send_discord(message):
    webhook_url = CONFIG.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Discord Webhook URL未設定")
        return
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
        print("✅ Discord通知完了")
    except Exception as e:
        print(f"❌ Discord送信エラー: {e}")

def main():
    print("--- KASETACK 羽田レーダー 実行開始 ---")
    
    # 1. 取得
    if run_fetch():
        # 2. 解析
        data = run_analyze()
        if data:
            # 日本時間基準パスワード (HND+月日)
            jst = timezone(timedelta(hours=9))
            pw = f"HND{datetime.now(jst).strftime('%m%d')}"
            
            # 3. HTML生成
            run_render(password=pw)
            
            # 4. Discord通知
            msg = (
                f"📡 **KASETACK レーダー稼働**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"【判定】: **{data['recommended_stand']}** (期待値 {data['total_pax']}名)\n"
                f"【URL】: {CONFIG['SITE_URL']}\n"
                f"【Pass】: `{pw}`\n"
                f"━━━━━━━━━━━━━━━\n"
                f"※更新: {data['update_time']} (JST)"
            )
            send_discord(msg)
            print(f"--- 全工程正常完了 (更新: {data['update_time']}) ---")
        else:
            print("❌ 解析エラー")

if __name__ == "__main__":
    main()
