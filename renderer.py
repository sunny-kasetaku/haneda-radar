# ==========================================
# Project: KASETACK - renderer.py (v4.1 Gold)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password="----"):
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    if not os.path.exists(result_file): return
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    stand = data.get("recommended_stand", "判定中")
    update_time = data.get("update_time", "--:--")
    flights = data.get("flights", [])

    # ランク別カラー（S:黄金, A:赤, B:緑, C:白, D:灰色）
    rank = "D"; r_color = "#555"
    if total_pax >= 800: rank, r_color = "S", "#ffcc00"
    elif total_pax >= 400: rank, r_color = "A", "#ff4444"
    elif total_pax >= 100: rank, r_color = "B", "#00ff00"
    elif total_pax > 0: rank, r_color = "C", "#ffffff"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:10px; display:flex; justify-content:center; }}
            .container {{ width:100%; max-width:400px; text-align:center; }}
            .main-card {{ background:#1c1c1c; border-radius:15px; padding:20px; margin-bottom:10px; border:1px solid #333; display:flex; align-items:center; justify-content:center; gap:20px; }}
            .rank-logo {{ font-size:100px; font-weight:bold; color:{r_color}; line-height:1; }}
            .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
            .t-card {{ background:#111; border:1px solid #222; border-radius:10px; padding:15px 5px; }}
            .footer {{ text-align:center; color:#444; font-size:11px; margin-top:15px; border-top:1px solid #222; padding-top:15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div style="color:#ffcc00; font-size:11px; margin-bottom:10px;">⚠️ KASETACK 羽田レーダー v4.1</div>
            <div class="main-card">
                <div class="rank-logo">{rank}</div>
                <div style="text-align:left;"><b style="font-size:20px;">【{stand}】</b><br>需要期待値 {total_pax}名</div>
            </div>
            <div class="grid">
                <div class="t-card">1号 (T1南)<br><b>0</b></div>
                <div class="t-card">2号 (T1北)<br><b>0</b></div>
                <div class="t-card">3号 (T2)<br><b>0</b></div>
                <div class="t-card">4号 (T2)<br><b>0</b></div>
            </div>
            <div class="footer">
                取得: {update_time} | <b>Pass: {password}</b><br>
                SITE: {CONFIG['SITE_URL']}
            </div>
        </div>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 黄金デザイン適用(Pass:{password})")
