from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def main():
    print("--- KASETACK 羽田レーダー 全工程開始 ---")
    
    # 1. データ取得
    run_fetch()
    
    # 2. 解析・計算（ここを軽量版に差し替え済み）
    data = run_analyze()
    
    # 3. HTML出力
    if data:
        run_render()
        print(f"--- 全工程完了！ 更新時刻: {data['update_time']} ---")
    else:
        print("❌ エラー: 解析データが生成されませんでした。")

if __name__ == "__main__":
    main()
