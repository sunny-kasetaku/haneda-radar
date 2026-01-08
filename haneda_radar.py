# ==========================================
# Project: KASETACK - haneda_radar.py
# ==========================================
from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def main():
    print("--- KASETACK 羽田レーダー: 固定名同期完了 ---")
    
    # 全工程実行
    run_fetch()
    data = run_analyze()
    
    if data:
        run_render()
        print(f"--- 全工程完了 (更新: {data['update_time']}) ---")
    else:
        print("❌ 解析プロセス失敗")

if __name__ == "__main__":
    main()
