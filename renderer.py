# ==========================================
# Project: KASETACK - renderer.py (v4.0 Live Restoration)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password="----"):
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file):
        return

    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    stand = data.get("recommended_stand", "判定中")
    update_time = data.get("update_time", "--:--")
    flights = data.get("flights", [])

    # ランク判定と色設定
    rank = "D"; rank_msg = "需要なし"; r_color = "#555"
    if total_pax >= 800: rank, rank_msg, r_color = "S", "需要爆発", "#ffcc00"
    elif total_pax >= 400: rank, rank_msg, r_color = "A", "需要あり", "#ff4444"
    elif total_pax >= 100: rank, rank_msg, r_color = "B", "期待", "#00ff00"
    elif total_pax > 0: rank, rank_msg, r_color = "C", "微増", "#ffffff"

    # HTML生成
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK v4.0 Live</title>
        <style>
            body {{ background-color: #000; color: #fff; font-family: sans-serif; margin: 0; padding: 10px; display: flex; justify-content: center; }}
            .container {{ width: 100%; max-width: 400px; }}
            .banner {{ border: 1px solid #ffcc00; border-radius: 8px; padding: 10px; text-align: center; color: #ffcc00; font-size: 13px; margin-bottom: 10px; background: rgba(255, 204, 0, 0.05); }}
            
            .main-card {{ background: #1c1c1c; border-radius: 15px; padding: 20px 0; text-align: center; margin-bottom: 10px; border: 1px solid #333; display: flex; align-items: center; justify-content: center; gap: 20px; }}
            .rank-logo {{ font-size: 100px; font-weight: bold; color: {r_color}; line-height: 1; }}
            .rank-info {{ text-align: left; }}
            .rank-label {{ font-size: 20px; font-weight: bold; color: #fff; }}
            
            .thresholds {{ display: flex; justify-content: space-between; font-size: 11px; color: #888; margin-bottom: 10px; padding: 0 5px; }}
            
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }}
            .t-card {{ background: #111; border: 1px solid #222; border-radius: 10px; padding: 15px 5px; text-align: center; }}
            .t-name {{ color: #777; font-size: 12px; margin-bottom: 5px; }}
            .t-pax {{ font-size: 32px; font-weight: bold; }}
            .t-pax span {{ font-size: 14px; font-weight: normal; margin-left: 2px; }}
            
            .advisor {{ background: #161616; border-left: 4px solid #ffcc00; padding: 15px; border-radius: 4px; margin-bottom: 15px; text-align: left; font-size: 14px; line-height: 1.5; }}
            
            .table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }}
            .table th {{ color: #ffcc00; text-align: left; padding: 8px; border-bottom: 1px solid #333; font-weight: normal; }}
            .table td {{ padding: 12px 8px; border-bottom: 1px solid #111; }}

            .btn {{ background: #ffcc00; color: #000; width: 100%; padding: 15px; border-radius: 10px; border: none; font-size: 18px; font-weight: bold; margin-bottom: 10px; cursor: pointer; }}
            .footer {{ text-align: center; color: #444; font-size: 11px; line-height: 1.8; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="banner">⚠️ 案内：本データは15分ごとに自動更新されます。<br>解析範囲：現在時刻の前後 60 分 (±30分)</div>
            
            <div class="main-card">
                <div class="rank-logo">{rank}</div>
                <div class="rank-info">
                    <div class="rank-label">【{stand}】 {rank_msg}</div>
                </div>
            </div>

            <div class="thresholds">
                <span><b style="color:#ffcc00">S</b>:800~</span><span><b style="color:#ff4444">A</b>:400~</span><span><b style="color:#00ff00">B</b>:100~</span><span><b>C</b>:1~</span><span><b>D</b>:0</span>
            </div>

            <div class="grid">
                <div class="t-card"><div class="t-name">1号 (T1南)</div><div class="t-pax">0<span>人</span></div></div>
                <div class="t-card"><div class="t-name">2号 (T1北)</div><div class="t-pax">0<span>人</span></div></div>
                <div class="t-card"><div class="t-name">3号 (T2)</div><div class="t-pax">0<span>人</span></div></div>
                <div class="t-card"><div class="t-name">4号 (T2)</div><div class="t-pax">0<span>人</span></div></div>
            </div>
            <div class="t-card" style="width:100%; box-sizing:border-box; margin-bottom:10px;">
                <div class="t-name">国際 (T3)</div><div class="t-pax">0<span>人</span></div>
            </div>

            <div class="advisor">
                <b style="color:#ffcc00">⚡ 参謀アドバイス：</b><br>
                羽田全体で約{total_pax}名の需要を検知。{stand}付近が有力です。
            </div>

            <table class="table">
                <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                <tbody>
    """

    if not flights:
        html_content += "<tr><td colspan='4' style='text-align:center; padding:20px; color:#444;'>対象なし</td></tr>"
    else:
        for f in flights[:15]:
            time_display = f['time'].split('T')[1][:5] if 'T' in f['time'] else "捕捉済"
            html_content += f"""
                <tr>
                    <td>{time_display}</td>
                    <td style="color:#ffcc00; font-weight:bold;">{f['flight_no']}</td>
                    <td>{f.get('origin', '---')}</td>
                    <td>{f['pax']}人</td>
                </tr>
            """

    html_content += f"""
                </tbody>
            </table>

            <button class="btn" onclick="location.reload()">最新情報に更新</button>
            
            <div class="footer">
                画面の自動再読み込みまであと 46 秒<br>
                最終データ取得: {update_time} | Pass: {password} | v4.0 Live
            </div>
        </div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ デザインを v4.0 Live 仕様で完全復旧しました。")
