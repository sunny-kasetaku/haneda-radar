# ==========================================
# Project: KASETACK - renderer.py (v6.5 All-Access)
# ==========================================
import json
import os
from datetime import datetime
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

    # 空港名変換辞書（適宜追加可能）
    AIRPORT_MAP = {
        "HND": "羽田", "NRT": "成田", "CTS": "新千歳", "OKA": "那覇", 
        "FUK": "福岡", "ITM": "伊丹", "KIX": "関空", "NGO": "中部", 
        "HKG": "香港", "TPE": "台北", "ICN": "仁川", "BKK": "バンコク", 
        "SIN": "シンガポール", "LHR": "ロンドン", "CDG": "パリ", 
        "FRA": "フランクフルト", "JFK": "NY/JFK", "LAX": "ロス", 
        "SFO": "S.フラシスコ", "ORD": "シカゴ", "DFW": "ダラス", 
        "MSP": "ミネアポリス", "HNL": "ホノルル", "SYD": "シドニー", 
        "YGJ": "米子", "OKJ": "岡山", "MYJ": "松山", "TAK": "高松"
    }

    try:
        current_hour = int(update_time.split(":")[0])
    except:
        current_hour = datetime.now().hour

    # エクセル統計比率マスター
    WEIGHT_MASTER = {
        7:  [2, 0, 1, 0, 8],   8:  [8, 9, 13, 4, 0],  9:  [10, 9, 16, 3, 1],
        10: [6, 8, 9, 4, 0],   11: [10, 10, 10, 6, 1], 12: [9, 7, 14, 4, 1],
        13: [10, 9, 8, 4, 0],  14: [8, 5, 9, 7, 0],   15: [7, 7, 13, 3, 0],
        16: [7, 12, 10, 5, 2], 17: [10, 7, 10, 4, 6],  18: [10, 8, 11, 9, 1],
        19: [9, 7, 11, 3, 1],  20: [11, 7, 11, 4, 2],  21: [10, 10, 14, 4, 1],
        22: [7, 7, 9, 4, 2],   23: [1, 0, 2, 3, 0]
    }
    
    w = WEIGHT_MASTER.get(current_hour, [1, 1, 1, 1, 1])
    w_sum = sum(w) if sum(w) > 0 else 5

    # 期待値計算
    pax_counts = [
        int(total_pax * (w[0] / w_sum)), int(total_pax * (w[1] / w_sum)),
        int(total_pax * (w[2] / w_sum)), int(total_pax * (w[3] / w_sum)),
        int(total_pax * (w[4] / w_sum))
    ]
    t1_s, t1_n, t2_3, t2_4, t3_i = pax_counts

    # 最高期待値の判定
    max_val = max(pax_counts)
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    stand_names = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    best_stand_name = stand_names[best_idx] if best_idx != -1 else "待機推奨"

    # ランク判定
    display_pax = total_pax
    if current_hour >= 23 or current_hour <= 1: display_pax = int(total_pax * 1.5)

    if display_pax >= 800: rank, r_color, status_text, symbol = "S", "#FFD700", "【最高】 需要爆発", "🌈"
    elif display_pax >= 400: rank, r_color, status_text, symbol = "A", "#FF6B00", "【推奨】 需要過多", "🔥"
    elif display_pax >= 100: rank, r_color, status_text, symbol = "B", "#00FF00", "【待機】 需要あり", "✅"
    elif display_pax > 0: rank, r_color, status_text, symbol = "C", "#FFFFFF", "【注意】 需要僅少", "⚠️"
    else: rank, r_color, status_text, symbol = "D", "#888", "【撤退】 需要なし", "🌑"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar v6.5</title>
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.5; background:#fff; }} 100% {{ opacity: 1; background:#000; }} }}
            body.loading {{ animation: flash 0.4s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-size: 14px; font-weight: bold; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 30px 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 150px; font-weight: bold; color: {r_color}; line-height: 1; }}
            .rank-thresholds {{ display: flex; justify-content: space-around; font-size: 12px; color: #999; margin-bottom: 20px; background: #111; padding: 8px; border-radius: 10px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-title {{ color: #999; font-size: 13px; }}
            .t-num {{ font-size: 38px; font-weight: bold; color: #FFF; }}
            .table-header {{ display: flex; justify-content: space-between; color: #FFD700; font-weight: bold; padding: 10px 5px; border-bottom: 1px solid #333; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 5px; border-bottom: 1px solid #222; font-size: 14px; }}
            .col-time, .col-name, .col-origin, .col-pax {{ width: 25%; text-align: center; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; border: none; cursor: pointer; }}
            .footer-timer {{ text-align: center; color: #888; font-size: 14px; margin-top: 10px; line-height: 1.6; }}
            #timer {{ color: #FFD700; font-weight: bold; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v1";
                if (localStorage.getItem(storageKey) === "{password}") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                    return;
                }}
                const input = prompt("パスワードを入力");
                if (input === "{password}") {{
                    localStorage.setItem(storageKey, input);
                    location.reload();
                }} else {{ window.location.reload(); }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 現在の狙い目：{best_stand_name}</div>
            <div class="rank-card">
                <div style="font-size:60px;">{symbol} <span style="font-size:150px; color:{r_color};">{rank}</span></div>
                <div style="font-size:32px; font-weight:bold;">{status_text}</div>
            </div>
            <div class="rank-thresholds">
                <span>🌈<b>S</b>:800~</span><span>🔥<b>A</b>:400~</span><span>✅<b>B</b>:100~</span><span>⚠️<b>C</b>:1~</span><span>🌑<b>D</b>:0</span>
            </div>
            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div class="t-title">1号(T1南)</div><div class="t-num">{t1_s}人</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div class="t-title">2号(T1北)</div><div class="t-num">{t1_n}人</div></div>
                <div class="t-card {'best-choice' if best_idx==2 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==2 else '' }<div class="t-title">3号(T2)</div><div class="t-num">{t2_3}人</div></div>
                <div class="t-card {'best-choice' if best_idx==3 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==3 else '' }<div class="t-title">4号(T2)</div><div class="t-num">{t2_4}人</div></div>
                <div class="t-card {'best-choice' if best_idx==4 else ''}" style="grid-column: 1/3;">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==4 else '' }<div class="t-title">国際(T3)</div><div class="t-num">{t3_i}人</div></div>
            </div>
            
            <div class="table-header"><div class="col-time">時刻</div><div class="col-name">便名</div><div class="col-origin">出身</div><div class="col-pax">推計</div></div>
            
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else "---"}</div><div class="col-name" style="color:#FFD700;">{f["flight_no"]}</div><div class="col-origin">{AIRPORT_MAP.get(f.get("origin",""), f.get("origin","---"))}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights]) if flights else '<div style="padding:20px;text-align:center;color:#666;">対象なし</div>'}
            
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer-timer">
                画面の自動再読み込みまであと <span id="timer">60</span> 秒<br>
                最終データ取得: {update_time} | v6.5 Final
            </div>
        </div>
        <script>
            let sec = 60;
            const timerElement = document.getElementById('timer');
            setInterval(() => {{
                sec--;
                if(sec >= 0) timerElement.innerText = sec;
                if(sec <= 0) location.reload(true);
            }}, 1000);
        </script>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ v6.5：全到着便を網羅（制限解除）しました")