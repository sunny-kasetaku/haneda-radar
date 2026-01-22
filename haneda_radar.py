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
    if run_fetch():
        data = run_analyze()
        if data:
            # --- [指示: パスワードを数字4桁(月日)に固定] ---
            jst = timezone(timedelta(hours=9))
            pw = datetime.now(jst).strftime('%m%d')  # 例: 0108
            
            # rendererへの受け渡し
            run_render(password=pw)
            
            # Discord通知メッセージ (pwを反映)
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
            print(f"--- 全工程正常完了 (Pass: {pw}) ---")
        else:
            print("❌ 解析エラー")

if __name__ == "__main__":
    main()
