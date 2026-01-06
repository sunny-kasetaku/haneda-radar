# 今までのファイル名を維持します
from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def main():
    print("--- KASETACK 羽田レーダー 起動 ---")
    
    # 1. 外部サイトからデータを取ってくる
    # ここでコケても raw_flight.txt があれば解析は進める設計です
    run_fetch()
    
    # 2. データを解析してJSONに保存する
    # サニーさんのロジック（30分前後の判定など）はここに入っています
    data = run_analyze()
    
    # 3. 解析結果を元に index.html を書き出す
    if data:
        run_render()
        print(f"--- 更新完了: {data['update_time']} ---")
    else:
        print("エラー: 解析データが生成されませんでした。")

if __name__ == "__main__":
    main()
