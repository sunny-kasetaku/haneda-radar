import requests
import os
import sys
from config import CONFIG

def run_fetch():
    # 羽田到着便のURL
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    
    print("--- Fetcher 開始 ---")
    try:
        print(f"1. ターゲットURLに接続試行中... (Timeout=15s)")
        # タイムアウトを15秒に設定。これで6分待たされることはなくなります
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"2. 応答受信。ステータスコード: {response.status_code}")
        response.raise_for_status() # エラーがあればここで例外を投げる

        # データが空でないか確認
        if len(response.text) < 100:
            print("警告: 受信したデータが少なすぎます（ブロックの可能性あり）")
            return False

        print(f"3. ファイル書き込み中... ターゲット: {CONFIG['DATA_FILE']}")
        
        # ファイル保存の絶対パスを表示（環境の確認用）
        abs_path = os.path.abspath(CONFIG["DATA_FILE"])
        print(f"保存先フルパス: {abs_path}")

        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("--- Fetcher 成功完了 ---")
        return True

    except requests.exceptions.Timeout:
        print("❌ エラー: 相手サイトからの応答が15秒以内にありませんでした（タイムアウト）")
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: 通信中に問題が発生しました: {e}")
    except Exception as e:
        print(f"❌ エラー: 予期せぬ不具合です: {e}")
    
    return False

if __name__ == "__main__":
    run_fetch()
