import json
import os
from datetime import datetime
from config import CONFIG

def run_render():
    result_file = CONFIG.get("RESULT_JSON", "analysis_result.json")
    report_file = CONFIG.get("REPORT_FILE", "index.html")
    
    print(f"--- KASETACK Renderer v20.0: デザイン復元版 ---")

    # データの読み込み
    data = {"flights": [], "count": 0, "update_time": "--:--"}
    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    flights = data.get("flights", [])
    update_time = data.get("update_time", datetime.now().strftime("%H:%M:%S"))

    # プロデューサーこだわりの「KASETACKデザイン」を再構築
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK 羽田レーダー</title>
        <style>
            body {{ background-color: #0b0e14; color: #e0e6ed; font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; border: 1px solid #2d333b; border-radius: 8px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #f39c12 0%, #d35400 100%); color: #fff; padding: 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; letter-spacing: 2px; }}
            .stats-bar {{ background: #1c2128; padding: 10px; border-bottom: 1px solid #2d333b; display: flex; justify-content: space-between; font-size: 14px; color: #8b949e; }}
            .flight-grid {{ padding: 10px; background: #0b0e14; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; margin-bottom: 10px; padding: 15px; display: flex; align-items: center; border-left: 4px solid #f39c12; }}
            .flight-info {{ flex-grow: 1; }}
            .flight-no {{ font-size: 20px; font-weight: bold; color: #f39c12; margin-right: 15px; }}
            .airline {{ font-size: 16px; color: #c9d1d9; }}
            .status-tag {{ background: #238636; color: #fff; padding: 4px 8px; border-radius: 12px; font-size: 12px; }}
            .empty-msg {{ text-align: center; padding: 40px; color: #484f58; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #484f58; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚖 KASETACK 羽田レーダー</h1>
            </div>
            <div class="stats-bar">
                <span>🕒 更新: {update_time}</span>
                <span>📡 捕捉数: {len(flights)}件</span>
            </div>
            <div class="flight-grid">
    """

    if not flights:
        html_content += """
                <div class="empty-msg">
                    <p>📡 データを精査中...<br>生データから航空便を抽出しています</p>
                </div>
        """
    else:
        for f in flights:
            html_content += f"""
                <div class="card">
                    <div class="flight-no">{f.get('flight_no', '---')}</div>
                    <div class="flight-info">
                        <span class="airline">{f.get('airline', '不明')}</span>
                    </div>
                    <div class="status-tag">本物抽出</div>
                </div>
            """

    html_content += """
            </div>
            <div class="footer">
                © 2026 KASETACK System v20.0 | Data source: Flightradar24
            </div>
        </div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ KASETACKデザインでレポートを復元しました。")

if __name__ == "__main__":
    run_render()
