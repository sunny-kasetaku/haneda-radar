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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"2. 応答受信。ステータスコード: {response.status_code}")
        response.raise_for_status()

        if len(response.text) < 100:
            print("警告: 受信したデータが少なすぎます（ブロックの可能性あり）")
            return False

        print(f"3. ファイル書き込み中... ターゲット: {CONFIG['DATA_FILE']}")
        
        abs_path = os.path.abspath(CONFIG["DATA_FILE"])
        print(f"保存先フルパス: {abs_path}")

        # --- ここから足し算：調査パッチ ---
        with open(CONFIG["DATA_FILE"], "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print("\n--- 🔍 データ中身の簡易調査（血の掟：精度向上のため） ---")
        content_upper = response.text.upper()
        
        # JAL / ANA の存在チェック
        if "JAL" in content_upper or "JL " in content_upper or "ANA" in content_upper or "NH " in content_upper:
            print("✅ 国内キャリア（JAL/ANA等）の記述が見つかりました！")
        else:
            print("⚠️ 警告：JAL/ANAが見当たりません。国内便が漏れている可能性があります。")

        # 機材名のヒントチェック
        equipments = ["777", "787", "A350", "737", "767", "A320"]
        found_eq = [eq for eq in equipments if eq in content_upper]
        if found_eq:
            print(f"✅ 機材のヒントを発見: {found_eq} (これを使えば精度が爆上がりします)")
        else:
            print("ℹ️ 機材情報の直接記述（787など）は見つかりませんでした。")
        print("--------------------------------------------------\n")
        # --- 調査パッチ終了 ---

        print("--- Fetcher 成功完了 ---")
        return True

    except requests.exceptions.Timeout:
        print("❌ エラー: タイムアウト（15秒応答なし）")
    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: 通信トラブル: {e}")
    except Exception as e:
        print(f"❌ エラー: 予期せぬ不具合: {e}")
    
    return False

if __name__ == "__main__":
    run_fetch()
