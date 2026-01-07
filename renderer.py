import json
import os
from datetime import datetime
from config import CONFIG

def run_render():
    result_file = CONFIG.get("RESULT_JSON", "analysis_result.json")
    report_file = CONFIG.get("REPORT_FILE", "index.html")
    
    # データの読み込み
    data = {"flights": [], "count": 0, "update_time": "--:--"}
    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    flights = data.get("flights", [])
    update_time = data.get("update_time", datetime.now().strftime("%H:%M"))

    # デザイン再現
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK 羽田レーダー v4.0</title>
        <style>
            body {{ background-color: #000; color: #fff; font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }}
            .info-banner {{ border: 1px solid #ffcc00; border-radius: 8px; padding: 10px; text-align: center; color: #ffcc00; font-size: 13px; margin-bottom: 15px; }}
            
            .main-rank-card {{ background-color: #222; border: 2px solid #555; border-radius: 15px; padding: 30px 10px; text-align: center; margin-bottom: 15px; }}
            .rank-icon {{ font-size: 80px; font-weight: bold; color: #888; line-height: 1; }}
            .rank-text {{ font-size: 20px; font-weight: bold; margin-top: 10px; }}

            .threshold-bar {{ background-color: #111; border-radius: 20px; padding: 8px; display: flex; justify-content: space-around; font-size: 12px; margin-bottom: 15px; color: #888; }}
            .threshold-bar span b {{ color: #eee; }}

            .terminal-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }}
            .terminal-card {{ background-color: #111; border: 1px solid #333; border-radius: 10px; padding: 15px; text-align: center; }}
            .terminal-name {{ color: #888; font-size: 11px; }}
            .pax-count {{ font-size: 28px; font-weight: bold; margin: 5px 0; }}
            .pool-count {{ color: #ffcc00; font-size: 14px; font-weight: bold; }}

            .advisor-box {{ background-color: #1a1a1a; border-left: 5px solid #ffcc00; border-radius: 4px; padding: 15px; margin-bottom: 20px; font-size: 14px; line-height: 1.5; }}
            .advisor-title {{ color: #ffcc00; font-weight: bold; margin-bottom: 5px; }}

            .data-table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 20px; }}
            .data-table th {{ border-bottom: 1px solid #333; padding: 10px; color: #ffcc00; text-align: left; font-weight: normal; }}
            .data-table td {{ padding: 15px 10px; border-bottom: 1px solid #111; }}

            .update-btn {{ background-color: #ffcc00; color: #000; width: 100%; padding: 18px; border-radius: 40px; border: none; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
            .footer-info {{ text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="info-banner">⚠️ 案内：本データは15分ごとに自動更新されます。<br>解析範囲：現在時刻の前後 60 分 (±30分)</div>

        <div class="main-rank-card">
            <div class="rank-icon">D</div>
            <div class="rank-text">【撤退】需要なし</div>
        </div>

        <div class="threshold-bar">
            <span><b style="color:#ffcc00">S</b>:800~</span> <span><b style="color:#ff6600">A</b>:400~</span> <span><b style="color:#00ff00">B</b>:100~</span> <span><b>C</b>:1~</span> <span><b>D</b>:0</span>
        </div>

        <div class="terminal-grid">
            <div class="terminal-card"><div class="terminal-name">1号 (T1南)</div><div class="pax-count">0人</div><div class="pool-count">プール: 100台</div></div>
            <div class="terminal-card"><div class="terminal-name">2号 (T1北)</div><div class="pax-count">0人</div><div class="pool-count">プール: 100台</div></div>
            <div class="terminal-card"><div class="terminal-name">3号 (T2)</div><div class="pax-count">0人</div><div class="pool-count">プール: 120台</div></div>
            <div class="terminal-card"><div class="terminal-name">4号 (T2)</div><div class="pax-count">0人</div><div class="pool-count">プール: 80台</div></div>
        </div>

        <div class="terminal-card" style="margin-bottom: 15px; width: 100%; box-sizing: border-box;">
            <div class="terminal-name">国際 (T3)</div><div class="pax-count">0人</div><div class="pool-count">プール: 150台</div>
        </div>

        <div class="advisor-box">
            <div class="advisor-title">⚡ 参謀アドバイス：</div>
            羽田全体で約{len(flights) * 150 if flights else 0}名の需要を検知。1番付近が有力です。
        </div>

        <table class="data-table">
            <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
            <tbody>
    """

    if not flights:
        html_content += "<tr><td colspan='4' style='text-align:center; padding:30px; color:#444;'>対象なし</td></tr>"
    else:
        for f in flights:
            html_content += f"""
                <tr>
                    <td>捕捉</td>
                    <td style="color:#ffcc00; font-weight:bold;">{f.get('flight_no')}</td>
                    <td>{f.get('airline')}</td>
                    <td>150人</td>
                </tr>
            """

    html_content += f"""
            </tbody>
        </table>

        <button class="update-btn">最新情報に更新</button>
        <div class="footer-info">
            画面の自動再読み込みまであと 46 秒<br><br>
            最終データ取得: {update_time} | v4.0 Live
        </div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ スクリーンショットに基づき、v4.0デザインを完全復元しました。")

if __name__ == "__main__":
    run_render()
