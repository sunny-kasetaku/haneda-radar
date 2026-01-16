# ==========================================
# Project: KASETACK - renderer.py (v5.2 Fix Discord Link)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password): # 固定値 "0116" を削除し、外部からの入力を受け取るように修正
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file): return
    
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    update_time = data.get("update_time", "--:--")
    flights = data.get("flights", [])
    
    # ターミナル別集計
    t1_s = data.get("t1_south_pax", 0)
    t1_n = data.get("t1_north_pax", 0)
    t2_3 = data.get("t2_3_pax", 0)
    t2_4 = data.get("t2_4_pax", 0)
    t3_i = data.get("t3_intl_pax", 0)

    # ランク判定
    rank = "D"; r_color = "#555"; status_text = "【撤退】 需要なし"
    if total_pax >= 800: rank, r_color, status_text = "S", "#FFD700", "【最高】 需要爆発"
    elif total_pax >= 400: rank, r_color, status_text = "A", "#FF6B00", "【推奨】 需要過多"
    elif total_pax >= 100: rank, r_color, status_text = "B", "#00FF00", "【待機】 需要あり"
    elif total_pax > 0: rank, r_color, status_text = "C", "#FFFFFF", "【注意】 需要僅少"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar v5.2 Live</title>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v1";
                const savedPass = localStorage.getItem(storageKey);
                const correctPass = "{password}";

                // 正しいパスワードが保存されていれば表示
                if (savedPass === correctPass) {{
                    document.getElementById('main-content').style.display = 'block';
                    return;
                }}

                const input = prompt("パスワードを入力してください");
                if (input === correctPass) {{
                    localStorage.setItem(storageKey, input);
                    document.getElementById('main-content').style.display = 'block';
                }} else {{
                    alert("無効なパスワードです");
                    window.location.reload();
                }}
            }}
            window.onload = checkPass;
        </script>
        <style>
            body {{ background:#000; color:#fff; font-family:'Helvetica Neue',Arial,sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:450px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 10px; padding: 10px; text-align: center; color: #FFD700; font-size: 13px; margin-bottom: 15px; }}
            .rank-card {{ background: #1A1A1A; border: 2px solid #444; border-radius: 20px; padding: 30px 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {r_color}; line-height: 1; margin-bottom: 10px; }}
            .status-label {{ font-size: 24px; font-weight: bold; color: #fff; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 15px; padding: 15px; text-align: center; }}
            .t-title {{ color: #AAA; font-size: 13px; }}
            .t-num {{ font-size: 32px; font-weight: bold; color: #FFF; }}
            .advice-box {{ background: #1A1A1A; border-left: 5px solid #FFD700; padding: 15px; margin-bottom: 20px; }}
            .table-header {{ display: flex; justify-content: space-between; color: #FFD700; font-weight: bold; padding: 10px 5px; border-bottom: 1px solid #333; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 5px; border-bottom: 1px solid #222; font-size: 14px; }}
            .col-time {{ width: 20%; }} .col-name {{ width: 25%; color: #FFD700; }} .col-origin {{ width: 25%; }} .col-pax {{ width: 20%; text-align: right; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 案内：本データは15分ごとに自動更新されます。</div>
            <div class="rank-card">
                <div class="rank-display">{rank}</div>
                <div class="status-label">{status_text}</div>
            </div>
            <div class="grid">
                <div class="t-card"><div class="t-title">1号(T1南)</div><div class="t-num">{t1_s}人</div></div>
                <div class="t-card"><div class="t-title">2号(T1北)</div><div class="t-num">{t1_n}人</div></div>
                <div class="t-card"><div class="t-title">3号(T2)</div><div class="t-num">{t2_3}人</div></div>
                <div class="t-card"><div class="t-title">4号(T2)</div><div class="t-num">{t2_4}人</div></div>
                <div class="t-card" style="grid-column: 1/3;"><div class="t-title">国際(T3)</div><div class="t-num">{t3_i}人</div></div>
            </div>
            <div class="advice-box">⚡ 参謀アドバイス：羽田全体で約{total_pax}名の需要。</div>
            <div class="table-header"><div>時刻</div><div>便名</div><div>出身</div><div>推計</div></div>
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else "---"}</div><div class="col-name">{f["flight_no"]}</div><div class="col-origin">{f.get("origin","---")}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights[:20]])}
            <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
            <div style="text-align:center; color:#666; font-size:12px;">
                最終データ取得: {update_time} | v5.2 Live
            </div>
        </div>
        <script>
            let sec = 60;
            setInterval(() => {{
                sec--;
                if(sec == 0) location.reload();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ パスワード門番(記憶型)を適用完了")