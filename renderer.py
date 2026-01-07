import json
import os
from datetime import datetime
from config import CONFIG

def run_render():
    result_file = CONFIG.get("RESULT_JSON", "analysis_result.json")
    report_file = CONFIG.get("REPORT_FILE", "index.html")
    
    print(f"--- KASETACK Renderer v18.0: 防御表示版 ---")

    data = {"flights": [], "count": 0, "total_pax": 0}
    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    flights = data.get("flights", [])
    update_time = data.get("last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>羽田到着レーダー</title>
        <style>
            body {{ font-family: sans-serif; background: #1a1a1a; color: #eee; padding: 20px; }}
            .card {{ background: #333; border-left: 5px solid #f39c12; margin: 10px 0; padding: 10px; border-radius: 4px; }}
            .flight-no {{ font-size: 1.2em; font-weight: bold; color: #f39c12; }}
        </style>
    </head>
    <body>
        <h1>🚖 羽田到着便スクレイピング結果</h1>
        <p>更新: {update_time} | 捕捉数: {len(flights)}件</p>
        <hr>
    """

    if not flights:
        html_content += "<p>⚠️ 航空会社コード（JL/NH等）に一致するデータがまだ見つかりません。取得サイズを確認してください。</p>"
    else:
        for f in flights:
            html_content += f"""
            <div class="card">
                <span class="flight-no">{f.get('flight_no')}</span><br>
                {f.get('airline')} | 状況: {f.get('status')}
            </div>
            """

    html_content += "</body></html>"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ レポート生成完了: {report_file}")

if __name__ == "__main__":
    run_render()
