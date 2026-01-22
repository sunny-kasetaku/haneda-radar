import requests
import json

# --- 設定項目 ---
API_KEY = "76e04028a66e0e2d2b42d7d9c75462e7"  # ここにご自身のキーを入れてください
TARGET_AIRPORT = "HND"      # 羽田空港（IATAコード）

def run_audit():
    print(f"--- 羽田空港（{TARGET_AIRPORT}）の生データ監査を開始します ---")
    
    # APIのリクエストURL
    # 注：国内線を漏らさないよう、statusの指定を外して「全件」取得します
    url = f"http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': API_KEY,
        'arr_iata': TARGET_AIRPORT,
        'limit': 100  # 最大件数まで取得
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'data' not in data:
            print("❌ エラー: APIから正しくデータが届いていません。")
            print(data)
            return

        # 生データをそのまま保存
        with open('audit_raw_dump.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 成功: {len(data['data'])} 件のフライトデータを 'audit_raw_dump.json' に保存しました。")
        print("次に、このファイルを開いて中身を確認してください。")

    except Exception as e:
        print(f"❌ 実行中にエラーが発生しました: {e}")

if __name__ == "__main__":
    run_audit()