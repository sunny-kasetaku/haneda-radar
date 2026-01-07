import json
import os
from datetime import datetime
from config import CONFIG

def run_render():
    result_file = CONFIG.get("RESULT_JSON", "analysis_result.json")
    report_file = CONFIG.get("REPORT_FILE", "index.html")
    
    data = {"flights": [], "count": 0, "update_time": "--:--", "total_pax": 0}
    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    flights = data.get("flights", [])
    update_time = data.get("update_time", "--:--")
    total_pax = data.get("total_pax", 0)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK v4.0 Live</title>
        <style>
            body {{ background-color: #0b0b0b; color: #fff; font-family: -apple-system, sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }}
            .banner {{ border: 1px solid #ffcc00; border-radius: 10px; padding: 12px; text-align: center; color: #ffcc00; font-size: 13px; margin-bottom: 15px; background: rgba(255, 204, 0, 0.05); }}
            .main-card {{ background: #1c1c1c; border-radius: 20px; padding: 40px 0; text-align: center; margin-bottom: 15px; border: 1px solid #333; }}
            .rank-d {{ font-size: 90px; font-weight: bold; color: #555; line-height: 1; }}
            .rank-label {{ font-size: 22px; font-weight: bold; margin-top: 10px; color: #eee; }}
            .thresholds {{ display: flex; justify-content: space-around; font-size: 13px; color: #666; margin-bottom: 20px; }}
            .terminal-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }}
            .t-card {{ background: #111; border: 1px solid #222; border-radius: 12px; padding: 18px; text-align: center; }}
            .t-name {{ color: #777; font-size: 12px; margin-bottom: 5px; }}
            .t-pax {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
            .t-pool {{ color: #ffcc00; font-size: 14px; font-weight: bold; }}
            .advisor {{ background: #161616; border-left: 5px solid #ffcc00; padding: 18px; border-radius: 5px; margin-bottom: 20px; line-height: 1.6; font-size: 15px; }}
            .table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            .table th {{ color: #ffcc00; text-align: left; padding: 12px; border-bottom: 1px solid #222; font-weight: normal; font-size: 14px; }}
            .table td {{ padding: 18px 12px; border-bottom: 1px solid #111; font-size: 15px; }}
            .btn {{ background: #ffcc00; color: #000; width: 100%; padding: 20px; border-radius: 50px; border: none; font-size: 20px; font-weight: bold; margin-bottom: 15px; }}
            .footer {{ text-align: center; color: #444; font-size: 13px; line-height: 2; }}
        </style>
    </head>
    <body>
        <div class="banner">⚠️ 案内：本データは15分ごとに自動更新されます。<br>解析範囲：現在時刻の前後 60 分 (±30分)</div>
        <div class="main-card">
            <div class="rank-d">D</div>
            <div class="rank-label">【撤退】需要なし</div>
        </div>
        <div class="thresholds">
            <span><b style="color:#ffcc00">S</b>:800~</span><span><b style="color:#ff6600">A</b>:400~</span><span><b style="color:#00ff00">B</b>:100~</span><span><b>C</b>:1~</span><span><b>D</b>:0</span>
        </div>
        <div class="terminal-grid">
            <div class="t-card"><div class="t-name">1号 (T1南)</div><div class="t-pax">0人</div><div class="t-pool">プール: 100台</div></div>
            <div class="t-card"><div class="t-name">2号 (T1北)</div><div class="t-pax">0人</div><div class="t-pool">プール: 100台</div></div>
            <div class="t-card"><div class="t-name">3号 (T2)</div><div class="t-pax">0人</div><div class="t-pool">プール: 120台</div></div>
            <div class="t-card"><div class="t-name">4号 (T2)</div><div class="t-pax">0人</div><div class="t-pool">プール: 80台</div></div>
        </div>
        <div class="t-card" style="width:100%; box-sizing:border-box; margin-bottom:15px;">
            <div class="t-name">国際 (T3)</div><div class="t-pax">0人</div><div class="t-pool">プール: 150台</div>
        </div>
        <div class="advisor">
            <b style="color:#ffcc00">⚡ 参謀アドバイス：</b><br>
            羽田全体で約{total_pax}名の需要を検知。捕捉された各便の動向を注視してください。
        </div>
        <table class="table">
            <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
            <tbody>
    """

    if not flights:
        html_content += "<tr><td colspan='4' style='text-align:center; padding:40px; color:#444;'>対象なし</td></tr>"
    else:
        for f in flights:
            html_content += f"""
                <tr>
                    <td>捕捉済</td>
                    <td style="color:#ffcc00; font-weight:bold;">{f['flight_no']}</td>
                    <td>{f['airline']}</td>
                    <td>{f['pax']}人</td>
                </tr>
            """

    html_content += f"""
            </tbody>
        </table>
        <button class="btn">最新情報に更新</button>
        <div class="footer">画面の自動再読み込みまであと 46 秒<br>最終データ取得: {update_time} | v4.0 Live</div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ デザインをv4.0 Live仕様で100%復元しました。")

if __name__ == "__main__":
    run_render()
