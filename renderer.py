# ==========================================
# Project: KASETACK - renderer.py (v7.3 Delay & Cancel Handle)
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

    try:
        now_dt = datetime.strptime(update_time, "%H:%M")
    except:
        now_dt = datetime.now()
    
    # 解析範囲 (-30分 ～ +90分)
    start_win = now_dt - timedelta(minutes=30)
    end_win = now_dt + timedelta(minutes=90)

    # フィルタリング ＆ 集計
    flights = []
    pax_t1, pax_t2, pax_t3 = 0, 0, 0

    for f in raw_flights:
        # --- 1. ステータスチェック ---
        status = f.get("status", "")
        if "欠航" in status or "Cancelled" in status:
            continue # 欠航便は計算から除外

        # --- 2. 時刻の決定 (変更時刻があればそれを最優先) ---
        # ログの "到着予定(JST)" に遅延後の時間が入っていることを想定
        time_str = f.get("time", "")
        f_dt = None
        try:
            t_part = time_str.split("T")[1][:5] if "T" in time_str else time_str[:5]
            f_dt = datetime.strptime(t_part, "%H:%M")
        except: continue

        # --- 3. 解析範囲内か判定 ---
        if start_win <= f_dt <= end_win:
            flights.append(f)
            pax = f.get("pax", 0)
            term = f.get("terminal", "")
            if "T1" in term: pax_t1 += pax
            elif "T2" in term: pax_t2 += pax
            else: pax_t3 += pax

    # 時刻順に並び替え
    flights.sort(key=lambda x: x.get("time", ""))

    # --- 4. 統計比率配分 (Tさんエクセル) ---
    current_hour = now_dt.hour
    WEIGHT_MASTER = {
        7:[2,0,1,0,8], 8:[8,9,13,4,0], 9:[10,9,16,3,1], 10:[6,8,9,4,0],
        11:[10,10,10,6,1], 12:[9,7,14,4,1], 13:[10,9,8,4,0], 14:[8,5,9,7,0],
        15:[7,7,13,3,0], 16:[7,12,10,5,2], 17:[10,7,10,4,6], 18:[10,8,11,9,1],
        19:[9,7,11,3,1], 20:[11,7,11,4,2], 21:[10,10,14,4,1], 22:[7,7,9,4,2], 23:[1,0,2,3,0]
    }
    w = WEIGHT_MASTER.get(current_hour, [1, 1, 1, 1, 1])

    t1_s = int(pax_t1 * w[0] / ((w[0]+w[1]) or 2))
    t1_n = int(pax_t1 * w[1] / ((w[0]+w[1]) or 2))
    t2_3 = int(pax_t2 * w[2] / ((w[2]+w[3]+w[4]) or 3))
    t2_4 = int(pax_t2 * w[3] / ((w[2]+w[3]+w[4]) or 3))
    t3_i = pax_t3 + int(pax_t2 * w[4] / ((w[2]+w[3]+w[4]) or 3))

    total_pax = t1_s + t1_n + t2_3 + t2_4 + t3_i

    # --- 5. 判定・UI生成 ---
    pax_counts = [t1_s, t1_n, t2_3, t2_4, t3_i]
    max_val = max(pax_counts)
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    stand_names = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]

    if total_pax >= 800: rank, r_color, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total_pax >= 400: rank, r_color, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total_pax >= 100: rank, r_color, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    elif total_pax > 0: rank, r_color, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"
    else: rank, r_color, sym, st = "D", "#888", "🌑", "【撤退】 需要なし"

    AIRPORT_MAP = {"CTS":"新千歳","OKA":"那覇","FUK":"福岡","ITM":"伊丹","KIX":"関空","NGO":"中部","LAX":"ロス","HNL":"ホノルル","IAD":"ワシントン","DFW":"ダラス","MSP":"ミネアポリス","HKD":"函館","ASJ":"佐賀","NGS":"長崎"}

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar v7.3 Professional</title>
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
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; border: none; cursor: pointer; }}
            #timer {{ color: #FFD700; font-weight: bold; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v1";
                const pass = "{password}";
                if (localStorage.getItem(storageKey) === pass) {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                }} else {{
                    const input = prompt("パスワードを入力");
                    if (input === pass) {{ localStorage.setItem(storageKey, input); location.reload(); }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲：{start_win.strftime('%H:%M')}〜{end_win.strftime('%H:%M')} | 狙い目：{stand_names[best_idx] if best_idx != -1 else "なし"}</div>
            
            <div class="rank-card">
                <div style="font-size:60px;">{sym} <span style="font-size:150px; color:{r_color};">{rank}</span></div>
                <div style="font-size:32px; font-weight:bold;">{st}</div>
            </div>

            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div style="color:#999;font-size:13px;">1号(T1南)</div><div class="t-num">{t1_s}人</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div style="color:#999;font-size:13px;">2号(T1北)</div><div class="t-num">{t1_n}人</div></div>
                <div class="t-card {'best-choice' if best_idx==2 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==2 else '' }<div style="color:#999;font-size:13px;">3号(T2)</div><div class="t-num">{t2_3}人</div></div>
                <div class="t-card {'best-choice' if best_idx==3 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==3 else '' }<div style="color:#999;font-size:13px;">4号(T2)</div><div class="t-num">{t2_4}人</div></div>
                <div class="t-card {'best-choice' if best_idx==4 else ''}" style="grid-column: 1/3;">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==4 else '' }<div style="color:#999;font-size:13px;">国際(T3)</div><div class="t-num">{t3_i}人</div></div>
            </div>

            <div style="display:flex; justify-content:space-between; color:#FFD700; font-weight:bold; padding:10px 5px; border-bottom:1px solid #333;"><div>時刻</div><div>便名</div><div>出身</div><div>推計</div></div>
            {"".join([f'<div class="row"><div class="col-time">{f["time"].split("T")[1][:5] if "T" in f["time"] else f["time"][:5]}</div><div class="col-name" style="color:#FFD700;">{f["flight_no"]}</div><div class="col-origin">{AIRPORT_MAP.get(f.get("origin",""), f.get("origin","---"))}</div><div class="col-pax">{f["pax"]}名</div></div>' for f in flights]) if flights else '<div style="padding:40px; text-align:center; color:#666;">解析範囲内に有効な到着便はありません</div>'}
            
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div style="text-align:center; color:#888; font-size:12px;">最終取得: {update_time} | v7.3 Professional</div>
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
    print(f"✅ v7.3：遅延・欠航対応 ＆ 視界拡大完了")