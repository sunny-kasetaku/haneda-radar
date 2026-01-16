# ==========================================
# Project: KASETACK - renderer.py (v5.7 Symbol Restore)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password):
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file): return
    
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    update_time = data.get("update_time", "--:--")
    flights = data.get("flights", [])
    
    t1_s = data.get("t1_south_pax", 0)
    t1_n = data.get("t1_north_pax", 0)
    t2_3 = data.get("t2_3_pax", 0)
    t2_4 = data.get("t2_4_pax", 0)
    t3_i = data.get("t3_intl_pax", 0)

    # ランク判定 & シンボル設定
    if total_pax >= 800:
        rank, r_color, status_text, symbol = "S", "#FFD700", "【最高】 需要爆発", "🌈"
    elif total_pax >= 400:
        rank, r_color, status_text, symbol = "A", "#FF6B00", "【推奨】 需要過多", "🔥"
    elif total_pax >= 100:
        rank, r_color, status_text, symbol = "B", "#00FF00", "【待機】 需要あり", "✅"
    elif total_pax > 0:
        rank, r_color, status_text, symbol = "C", "#FFFFFF", "【注意】 需要僅少", "⚠️"
    else:
        rank, r_color, status_text, symbol = "D", "#888", "【撤退】 需要なし", "🌑"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar v5.7</title>
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.5; background:#fff; }} 100% {{ opacity: 1; background:#000; }} }}
            body.loading {{ animation: flash 0.4s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 12px; text-align: center; color: #FFD700; font-size: 15px; font-weight: bold; margin-bottom: 20px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 40px 20px; text-align: center; margin-bottom: 20px; }}
            .rank-display-wrap {{ display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 10px; }}
            .rank-symbol {{ font-size: 60px; }}
            .rank-display {{ font-size: 150px; font-weight: bold; color: {r_color}; line-height: 1; }}
            .status-label {{ font-size: 36px; font-weight: bold; color: #fff; }}
            .rank-thresholds {{ display: flex; justify-content: space-around; font-size: 13px; color: #999; margin-bottom: 25px; background: #111; padding: 10px; border-radius: 10px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 20px; text-align: center; }}
            .t-title {{ color: #999; font-size: 15px; }}
            .t-num {{ font-size: 42px; font-weight: bold; color: #FFF; }}
            .advice-box {{ background: #1A1A1A; border-left: 6px solid #FFD700; padding: 20px; margin-bottom: 25px; }}
            .table-header {{ display: flex; justify-content: space-between; color: #FFD700; font-weight: bold; padding: 12px 8px; border-bottom: 1px solid #333; }}
            .row {{ display: flex; justify-content: space-between; padding: 15px 8px; border-bottom: 1px solid #222; font-size: 16px; }}
            .col-time, .col-name, .col-origin, .col-pax {{ width: 25%; text-align: center; }}
            .col-name {{ color: #FFD700; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 20px; padding: 25px; font-size: 28px; font-weight: bold; margin: 25px 0; border: none; cursor: pointer; }}
            .footer-timer {{ text-align: center; color: #888; font-size: 15px; }}
            #timer {{ color: #FFD700; font-weight: bold; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v1";
                const savedPass = localStorage.getItem(storageKey);
                const correctPass = "{password}";
                if (savedPass === correctPass) {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                    return;
                }}
                const input = prompt("パスワードを入力してください");
                if (input === correctPass) {{
                    localStorage.setItem(storageKey, input);
                    document.getElementById('main-content').style.display = 'block';
                }} else {{ alert("無効なパスワードです"); window.location.reload(); }}
            }}
            window.onload = checkPass;
            function manualUpdate() {{ document.body.classList.add('loading'); setTimeout(() => location.reload(true), 100); }}
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 案内：本データは15分ごとに自動更新されます。<br>解析範囲：現在時刻の前後 60分 (±30分)</div>
            <div class="rank-card">
                <div class="rank-display-wrap">
                    <span class="rank-symbol">{symbol}</span>
                    <div class="rank-display">{rank}</div>
                </div>
                <div class="status-label">{status_text}</div>
            </div>
            <div class="rank-thresholds">
                <span>🌈<b style="color:#FFD700">S</b>:800~</span>
                <span>🔥<b style="color:#FF6B00">A</b>:400~</span>
                <span>✅<b style="color:#00FF00">B</b>:100~</span>
                <span>⚠️<b style="color:#FFFFFF">C</b>:1~</span>
                <span>🌑<b style="color:#888">D</b>:0</span>
            </div>
            <div class="grid">
                <div class="t-card"><div class="t-title">1号(T1南)</div><div class="t-num">{t1_s}人</div></div>
                <div class="t-card"><div class="t-title">2号(T1北)</div><div class="t-num">{t1_n}人</div></div>
                <div class="t-card"><div class="t-title">3号(T2)</div><div class="t-num">{t2_3}人</div></div>
                <div class="t-card"><div class="t-title">4号(T2)</div><div class="t-num">{t2_4}人</div></div>
                <div class="t-card" style="grid-column: 1/3;"><div class="t-title">国際(T3)</div><div class="t-num">{t3_i}人</div></div>
            </div>
            <div class="advice-box">羽田全体で約{total_pax}名の需要。</div>
            <div class="table-header"><div>時刻</div><div>便名</div><div>出身</div><div>推計</div></div>
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else "---"}</div><div class="col-name">{f["flight_no"]}</div><div class="col-origin">{f.get("origin","---")}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights[:20]]) if flights else '<div style="padding:20px;text-align:center;color:#666;">対象なし</div>'}
            <button class="update-btn" onclick="manualUpdate()">最新情報に更新</button>
            <div class="footer-timer">画面の自動再読み込みまであと <span id="timer">60</span> 秒</div>
        </div>
        <script>
            let sec = 60;
            const timerElement = document.getElementById('timer');
            setInterval(() => {{
                sec--;
                if(sec >= 0) timerElement.innerText = sec;
                if(sec <= 0) manualUpdate();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ シンボル(🌈🔥等)復刻 ＆ 更新ピカッを完全復旧")