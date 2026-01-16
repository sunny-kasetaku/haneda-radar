# ==========================================
# Project: KASETACK - renderer.py (v7.0 Professional Precision)
# ==========================================
import json
import os
from datetime import datetime, timedelta
from config import CONFIG

def run_render(password):
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file): return
    
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    update_time = data.get("update_time", "--:--")
    raw_flights = data.get("flights", [])

    # --- 1. 時間枠の精密フィルタ設定 (-30分 ～ +45分) ---
    try:
        now_dt = datetime.strptime(update_time, "%H:%M")
    except:
        now_dt = datetime.now()
    
    start_win = now_dt - timedelta(minutes=30)
    end_win = now_dt + timedelta(minutes=45)

    def is_in_window(f_time_str):
        try:
            # "18:21" または "2026-01-16T18:21" 形式に対応
            t_str = f_time_str.split("T")[1][:5] if "T" in f_time_str else f_time_str[:5]
            f_dt = datetime.strptime(t_str, "%H:%M")
            return start_win <= f_dt <= end_win
        except: return False

    # 解析範囲内の便だけに絞り込み ＆ 時刻順ソート
    flights = [f for f in raw_flights if is_in_window(f.get("time", ""))]
    flights.sort(key=lambda x: x.get("time", ""))

    # --- 2. ターミナル別の実数集計 ---
    pax_t1, pax_t2, pax_t3 = 0, 0, 0
    for f in flights:
        pax = f.get("pax", 0)
        term = f.get("terminal", "")
        if "T1" in term: pax_t1 += pax
        elif "T2" in term: pax_t2 += pax
        elif "T3" in term or "International" in term: pax_t3 += pax

    # --- 3. エクセル比率を「ターミナル内」の分配にのみ使用 ---
    current_hour = now_dt.hour
    WEIGHT_MASTER = {
        7: [2,0,1,0,8], 8: [8,9,13,4,0], 9: [10,9,16,3,1], 10: [6,8,9,4,0],
        11: [10,10,10,6,1], 12: [9,7,14,4,1], 13: [10,9,8,4,0], 14: [8,5,9,7,0],
        15: [7,7,13,3,0], 16: [7,12,10,5,2], 17: [10,7,10,4,6], 18: [10,8,11,9,1],
        19: [9,7,11,3,1], 20: [11,7,11,4,2], 21: [10,10,14,4,1], 22: [7,7,9,4,2], 23: [1,0,2,3,0]
    }
    w = WEIGHT_MASTER.get(current_hour, [1, 1, 1, 1, 1])

    # T1実数を1号・2号の比率で分ける
    w12 = (w[0] + w[1]) or 2
    t1_s = int(pax_t1 * w[0] / w12)
    t1_n = int(pax_t1 * w[1] / w12)

    # T2実数を3号・4号・4国際の比率で分ける
    w34i = (w[2] + w[3] + w[4]) or 3
    t2_3 = int(pax_t2 * w[2] / w34i)
    t2_4 = int(pax_t2 * w[3] / w34i)
    t2_intl = int(pax_t2 * w[4] / w34i)

    # 国際(T3)合計 = T3実数 + T2の国際分
    t3_i = pax_t3 + t2_intl

    total_pax = t1_s + t1_n + t2_3 + t2_4 + t3_i

    # --- 4. 判定ロジック ---
    pax_counts = [t1_s, t1_n, t2_3, t2_4, t3_i]
    max_val = max(pax_counts)
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    stand_names = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]

    display_pax = total_pax
    if current_hour >= 23 or current_hour <= 1: display_pax = int(total_pax * 1.5)

    if display_pax >= 800: rank, r_color, status_text, symbol = "S", "#FFD700", "【最高】 需要爆発", "🌈"
    elif display_pax >= 400: rank, r_color, status_text, symbol = "A", "#FF6B00", "【推奨】 需要過多", "🔥"
    elif display_pax >= 100: rank, r_color, status_text, symbol = "B", "#00FF00", "【待機】 需要あり", "✅"
    elif display_pax > 0: rank, r_color, status_text, symbol = "C", "#FFFFFF", "【注意】 需要僅少", "⚠️"
    else: rank, r_color, status_text, symbol = "D", "#888", "【撤退】 需要なし", "🌑"

    AIRPORT_MAP = {"CTS": "新千歳", "OKA": "那覇", "FUK": "福岡", "ITM": "伊丹", "KIX": "関空", "NGO": "中部", "JFK": "ニューヨーク", "LAX": "ロス", "HNL": "ホノルル", "IAD": "ワシントン", "DFW": "ダラス", "MSP": "ミネアポリス"}

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar v7.0 Precision</title>
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.5; background:#fff; }} 100% {{ opacity: 1; background:#000; }} }}
            body.loading {{ animation: flash 0.4s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-size: 14px; font-weight: bold; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 30px 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 150px; font-weight: bold; color: {r_color}; line-height: 1; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 38px; font-weight: bold; color: #FFF; }}
            .row {{ display: flex; justify-content: space-between; padding: 12px 5px; border-bottom: 1px solid #222; font-size: 14px; }}
            .col-time, .col-name, .col-origin, .col-pax {{ width: 25%; text-align: center; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; border: none; cursor: pointer; }}
            #timer {{ color: #FFD700; font-weight: bold; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v1";
                if (localStorage.getItem(storageKey) === "{password}") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                }} else {{
                    const input = prompt("パスワードを入力");
                    if (input === "{password}") {{ localStorage.setItem(storageKey, input); location.reload(); }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲：{start_win.strftime('%H:%M')}〜{end_win.strftime('%H:%M')} | 狙い目：{stand_names[best_idx] if best_idx != -1 else "---"}</div>
            <div class="rank-card">
                <div style="font-size:60px;">{symbol} <span style="font-size:150px; color:{r_color};">{rank}</span></div>
                <div style="font-size:32px; font-weight:bold;">{status_text}</div>
            </div>
            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div style="color:#999;font-size:13px;">1号(T1南)</div><div class="t-num">{t1_s}人</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div style="color:#999;font-size:13px;">2号(T1北)</div><div class="t-num">{t1_n}人</div></div>
                <div class="t-card {'best-choice' if best_idx==2 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==2 else '' }<div style="color:#999;font-size:13px;">3号(T2)</div><div class="t-num">{t2_3}人</div></div>
                <div class="t-card {'best-choice' if best_idx==3 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==3 else '' }<div style="color:#999;font-size:13px;">4号(T2)</div><div class="t-num">{t2_4}人</div></div>
                <div class="t-card {'best-choice' if best_idx==4 else ''}" style="grid-column: 1/3;">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==4 else '' }<div style="color:#999;font-size:13px;">国際(T3)</div><div class="t-num">{t3_i}人</div></div>
            </div>
            <div style="display:flex; justify-content:space-between; color:#FFD700; font-weight:bold; padding:10px 5px; border-bottom:1px solid #333;"><div>時刻</div><div>便名</div><div>出身</div><div>推計</div></div>
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else f["time"][:5]}</div><div class="col-name" style="color:#FFD700;">{f["flight_no"]}</div><div class="col-origin">{AIRPORT_MAP.get(f.get("origin",""), f.get("origin","---"))}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights])}
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div style="text-align:center; color:#888; font-size:12px;">自動更新まで <span id="timer">60</span> 秒 | v7.0 Precision</div>
        </div>
        <script>
            let sec = 60;
            setInterval(() => {{
                sec--;
                if(sec >= 0) document.getElementById('timer').innerText = sec;
                if(sec <= 0) location.reload(true);
            }}, 1000);
        </script>
    </body>
    </html>
    """
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ v7.0：-30/+45分厳守 ＆ ターミナル実数連動ロジックへ換装完了")