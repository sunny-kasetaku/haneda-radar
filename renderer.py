import json
import os
from datetime import datetime
from config import CONFIG

def run_render():
    result_file = CONFIG.get("RESULT_JSON", "analysis_result.json")
    report_file = CONFIG.get("REPORT_FILE", "index.html")
    
    print(f"--- KASETACK Renderer: 現場デザイン完全復元 ---")

    data = {"flights": [], "count": 0, "update_time": "--:--"}
    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    flights = data.get("flights", [])
    update_time = data.get("update_time", "--:--")

    # プロデューサー指定の「タクシー業務専用ダッシュボード」デザイン
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>羽田到着レーダー | KASETACK</title>
        <style>
            body {{ background-color: #000; color: #fff; font-family: 'Impact', 'Arial Black', sans-serif; margin: 0; padding: 10px; }}
            .header {{ background-color: #ff9900; color: #000; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; border-radius: 5px 5px 0 0; }}
            .status-bar {{ background-color: #222; padding: 10px; border-bottom: 2px solid #ff9900; display: flex; justify-content: space-between; font-size: 14px; color: #ff9900; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .data-table th {{ background-color: #333; color: #ff9900; padding: 12px; border: 1px solid #444; text-align: left; }}
            .data-table td {{ padding: 15px; border: 1px solid #444; font-size: 20px; border-bottom: 2px solid #333; }}
            .flight-no {{ color: #ff9900; font-size: 24px; font-weight: bold; }}
            .airline {{ color: #ccc; font-size: 16px; }}
            .msg {{ text-align: center; padding: 50px; color: #666; font-size: 18px; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #444; }}
        </style>
    </head>
    <body>
        <div class="header">🚖 羽田到着便レーダー (KASETACK)</div>
        <div class="status-bar">
            <span>更新時刻: {update_time}</span>
            <span>捕捉数: {len(flights)}</span>
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>便名 / 航空会社</th>
                    <th>状況</th>
                </tr>
            </thead>
            <tbody>
    """

    if not flights:
        html_content += """
                <tr>
                    <td colspan="2" class="msg">📡 信号待機中... 次の更新で捕捉予定</td>
                </tr>
        """
    else:
        for f in flights:
            html_content += f"""
                <tr>
                    <td>
                        <span class="flight-no">{f.get('flight_no')}</span><br>
                        <span class="airline">{f.get('airline')}</span>
                    </td>
                    <td style="color: #00ff00;">● 捕捉中</td>
                </tr>
            """

    html_content += """
            </tbody>
        </table>
        <div class="footer">SYSTEM v20.0 | AUTHENTIC DATA</div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ デザインを完全復元しました。")

if __name__ == "__main__":
    run_render()
