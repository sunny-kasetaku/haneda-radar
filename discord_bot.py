# discord_bot.py
import requests
from datetime import datetime

def send_daily_info(webhook_url, daily_password):
    """
    朝の定時連絡：URLとパスワードのみを送信
    """
    if not webhook_url or "YOUR_DISCORD" in webhook_url:
        print("LOG: Discord Webhook未設定のためスキップ")
        return

    today_str = datetime.now().strftime('%m/%d (%a)')

    payload = {
        "username": "Haneda Demand System",
        "content": f"☀️ **おはようございます！ {today_str} のアクセス情報です**",
        "embeds": [
            {
                "title": "🚕 羽田空港 需要予測システム v8.2",
                "description": "本日の稼働を開始しました。以下のリンクからアクセスしてください。",
                "color": 0x00BFFF,
                "fields": [
                    {"name": "🔗 システムURL", "value": "https://your-site-url.com/index.html", "inline": False},
                    {"name": "🔑 本日のパスワード", "value": f"**{daily_password}**", "inline": False}
                ],
                "footer": {"text": "※パスワードは毎日午前6時に変更されます"}
            }
        ]
    }

    try:
        requests.post(webhook_url, json=payload)
        print("LOG: Discordに定時案内を送信しました")
    except Exception as e:
        print(f"ERROR: Discord送信失敗 {e}")