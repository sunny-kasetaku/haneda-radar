import requests
import json
from datetime import datetime, timedelta

class DiscordBot:
    def __init__(self):
        pass

    def send_daily_info(self, webhook_url, password):
        """
        Discordに「本日のパスワード」と「おはようございます」のメッセージを送る
        """
        if not webhook_url:
            print("⚠️ Webhook URLが設定されていないため、通知をスキップします。")
            return

        # 🦁 修正: UTC(世界標準時)に9時間を足して、無理やり日本時間(JST)にする
        # これで「日付が1日戻る」現象を防ぎます
        jst_now = datetime.utcnow() + timedelta(hours=9)
        today_str = jst_now.strftime('%Y/%m/%d')

        # 送信するメッセージ内容
        payload = {
            "username": "羽田空港AIレーダー",
            "content": (
                f"☀️ **おはようございます！**\n"
                f"本日の羽田空港タクシー需要予測システムが稼働しました。\n\n"
                f"📅 **日付:** {today_str}\n"
                f"🔑 **本日のパスワード:** `{password}`\n\n"
                f"以下のURLからアクセスしてください:\n"
                f"https://sunny-kasetaku.github.io/haneda-radar/"
            )
        }

        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            # Discordは成功時に 204 No Content を返すことが多い
            if response.status_code == 204 or response.status_code == 200:
                print("✅ Discord通知送信成功")
            else:
                print(f"⚠️ Discord通知エラー: {response.status_code} {response.text}")
        except Exception as e:
            print(f"❌ Discord送信例外: {e}")