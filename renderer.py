# ==========================================
# Project: KASETACK - renderer.py (v5.0 UI Rebirth)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password="0116"):
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file): return
    
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    update_time = data.get("update_time", "--:--")
    flights = data.get("flights", [])
    
    # ターミナル別集計（analyzerから渡される想定のデータ）
    # まだ0の場合は0と表示されますが、器は完璧に用意しました
    t1_s = data.get("t1_south_pax", 0)
    t1_n = data.get("t1_north_pax", 0)
    t2_3 = data.get("t2_3_pax", 0)
    t2_4 = data.get("t2_4_pax", 0)
    t3_i = data.get("t3_intl_pax", 0)

    # ランク判定ロジック
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
        <title>KASETACK Radar v4.0 Live</title>
        # renderer.py の script セクションを以下のように書き換えます（全文の中の該当部分）

        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass";
                const savedPass = localStorage.getItem(storageKey);
                const correctPass = "{password}";

                // すでに保存されているパスワードが正しいかチェック
                if (savedPass === correctPass) {{
                    document.getElementById('main-content').style.display = 'block';
                    return;
                }}

                // 保存されていない、または間違っている場合のみ prompt を出す
                const input = prompt("パスワードを入力してください");
                if (input === correctPass) {{
                    localStorage.setItem(storage_key, input); // ブラウザに保存
                    document.getElementById('main-content').style.display = 'block';
                }} else {{
                    alert("無効なパスワードです");
                    window.location.reload();
                }}
            }}
            
            // ログアウト（パスワード再入力）したい時のための関数（必要であれば）
            function logout() {{
                localStorage.removeItem("kasetack_auth_pass");
                location.reload();
            }}

            window.onload = checkPass;
        </script>
        <style>
            body {{ background:#000; color:#fff; font-family:'Helvetica Neue',Arial,sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:450px; }}
            
            /* ヘッダー案内 */
            .info-banner {{ border: 2px solid #FFD700; border-radius: 10px; padding: 10px; text-align: center; color: #FFD700; font-size: 13px; margin-bottom: 15px; }}
            
            /* メインランクカード */
            .rank-card {{ background: #1A1A1A; border: 2px solid #444; border-radius: 20px; padding: 30px 20px; text-align: center; margin-bottom: 15px; position: relative; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {r_color}; line-height: 1; margin-bottom: 10px; }}
            .status-label {{ font-size: 24px; font-weight: bold; color: #fff; }}

            /* ランク閾値表示 */
            .rank-thresholds {{ display: flex; justify-content: space-around; font-size: 12px; color: #888; margin-bottom: 15px; padding: 0 10px; }}

            /* ターミナルグリッド */
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 15px; padding: 15px; text-align: center; }}
            .t-title {{ color: #AAA; font-size: 13px; margin-bottom: 5px; }}
            .t-num {{ font-size: 32px; font-weight: bold; color: #FFF; }}
            .t-unit {{ font-size: 16px; color: #FFF; }}
            .full-card {{ grid-column: 1 / span 2; }}

            /* 参謀アドバイス */
            .advice-box {{ background: #1A1A1A; border-left: 5px solid #FFD700; padding: 15px; text-align: left; margin-bottom: 20px; }}
            .advice-title {{ color: #FFD700; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; }}

            /* テーブル */
            .table-header {{ display: flex; justify-content: space-between; color: #FFD700; font-weight: bold; padding: 10px 5px; border-bottom: 1px solid #333; font-size: 14px; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 5px; border-bottom: 1px solid #222; font-size: 14px; }}
            .col-time {{ width: 20%; }} .col-name {{ width: 25%; color: #FFD700; }} .col-origin {{ width: 25%; }} .col-pax {{ width: 20%; text-align: right; }}

            /* ボタン */
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border: none; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; cursor: pointer; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">
                ⚠️ 案内：本データは15分ごとに自動更新されます。<br>解析範囲：現在時刻の前後 60分 (±30分)
            </div>

            <div class="rank-card">
                <div class="rank-display">{rank}</div>
                <div class="status-label">{status_text}</div>
            </div>

            <div class="rank-thresholds">
                <span><b style="color:#FFD700">S</b>:800~</span>
                <span><b style="color:#FF6B00">A</b>:400~</span>
                <span><b style="color:#00FF00">B</b>:100~</span>
                <span><b style="color:#FFFFFF">C</b>:1~</span>
                <span><b style="color:#888">D</b>:0</span>
            </div>

            <div class="grid">
                <div class="t-card"><div class="t-title">1号 (T1南)</div><div class="t-num">{t1_s}<span class="t-unit">人</span></div></div>
                <div class="t-card"><div class="t-title">2号 (T1北)</div><div class="t-num">{t1_n}<span class="t-unit">人</span></div></div>
                <div class="t-card"><div class="t-title">3号 (T2)</div><div class="t-num">{t2_3}<span class="t-unit">人</span></div></div>
                <div class="t-card"><div class="t-title">4号 (T2)</div><div class="t-num">{t2_4}<span class="t-unit">人</span></div></div>
                <div class="t-card full-card"><div class="t-title">国際 (T3)</div><div class="t-num">{t3_i}<span class="t-unit">人</span></div></div>
            </div>

            <div class="advice-box">
                <div class="advice-title">⚡ 参謀アドバイス：</div>
                羽田全体で約{total_pax}名の需要を検知。{stand if 'stand' in locals() else '---'}付近が有力です。
            </div>

            <div class="table-header">
                <div class="col-time">時刻</div><div class="col-name">便名</div><div class="col-origin">出身</div><div class="col-pax">推計</div>
            </div>
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else "---"}</div><div class="col-name">{f["flight_no"]}</div><div class="col-origin">{f.get("origin","---")}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights[:20]])}

            <button class="update-btn" onclick="location.reload()">最新情報に更新</button>

            <div class="footer">
                画面の自動再読み込みまであと <span id="timer">60</span> 秒<br>
                最終データ取得: {update_time} | v4.0 Live
            </div>
        </div>
        <script>
            let sec = 60;
            setInterval(() => {{
                sec--;
                if(sec >= 0) document.getElementById('timer').innerText = sec;
                if(sec == 0) location.reload();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ UI完全復刻＆門番適用完了 (Pass: {password})")