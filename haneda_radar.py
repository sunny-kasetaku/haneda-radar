from fetcher import run_fetch
from analyzer import run_analyze
from renderer import run_render

def main():
    # 1. 取得
    success = run_fetch()
    
    # 2. 解析 (取得に失敗しても前回のファイルがあれば実行可能)
    data = run_analyze()
    
    # 3. 出力
    if data:
        run_render()
        print("All processes completed successfully.")
    else:
        print("Analysis failed due to missing data.")

if __name__ == "__main__":
    main()
