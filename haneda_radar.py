# ==========================================
# Project: KASETACK - haneda_radar.py
# ==========================================
from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def main():
    print("--- KASETACK 羽田レーダー 実行開始 ---")
    
    # 1. データ取得
    fetch_success = run_fetch()
    
    # 2. 解析・計算
    if fetch_success:
        data = run_analyze()
        
        # 3. HTML出力
        if data:
            run_render()
            print(f"--- 全工程正常完了 (更新: {data['update_time']}) ---")
        else:
            print("❌ 解析エラーが発生しました。")
    else:
        print("❌ データ取得に失敗したため、工程を中断します。")

if __name__ == "__main__":
    main()
