# ==========================================
# Project: KASETACK - renderer_new.py (v2.0 Integration Master)
# ==========================================
import json
import os
from datetime import datetime

def generate_html_new(demand_results, flight_list):
    """
    v7.7の全機能（タイマー、パスワード、日本語化、BEST表示）を継承し、
    300件解析と最新レイアウトを統合した全文ソース。
    """
    
    # --- 1. 空港名マスター（v7.7継承：日本語化） ---
    AIRPORT_MAP = {
        "CTS":"新千歳", "OKA":"那覇", "FUK":"福岡", "ITM":"伊丹", "KIX":"関空", 
        "NGO":"中部", "HKD":"函館", "ASJ":"佐賀", "NGS":"長崎", "YGJ":"米子", 
        "OKJ":"岡山", "MYJ":"松山", "TAK":"高松", "UKB":"神戸", "KUM":"熊谷",
        "LAX":"ロス", "JFK":"ニューヨーク", "SFO":"S.フラシスコ", "ORD":"シカゴ", 
        "DFW":"ダラス", "MSP":"ミネアポリス", "IAD":"ワシントン", "SEA":"シアトル", 
        "HNL":"ホノルル", "YVR":"バンクーバー", "EWR":"ニューアーク",
        "LHR":"ロンドン", "CDG":"パリ", "FRA":"フランクフルト", "MUC":"ミュンヘン",
        "SYD":"シドニー", "SIN":"シンガポール", "BKK":"バンコク", "HKG":"香港",
        "ICN":"仁川", "GMP":"金浦", "TSA":"松山(台北)", "TPE":"桃園"
    }

    # --- 2. スコア計算とランク判定 ---
    total = sum(demand_results.values())
    if total >= 800: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 400: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total >= 100: r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    elif total >= 1:   r, c, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"
    else:              r, c, sym, st = "D", "#888", "🌑", "【撤退】 需要なし"

    now_dt = datetime.now()
    now_str = now_dt.strftime('%H:%M')
    
    # --- 3. 狙い目（BEST）の判定（v7.7継承） ---
    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    pax_counts = [demand_results.get(k, 0) for k in target_keys]
    max_val = max(pax_counts) if pax_counts else 0
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    
    # パスワード（v7.7継承）
    password = "kase" 

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.5; background:#fff; }} 100% {{ opacity: 1; background:#000; }} }}
            body.loading {{ animation: flash 0.4s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            
            /* バナー・ランクカード（v7.7のデザインを尊重） */
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-size: 14px; font-weight: bold; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 25px 20px; text-align: center; margin-bottom: 10px; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {c}; line-height: 1; }}
            
            /* グリッド・カード表示（BEST表示対応） */
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; color: #FFF; }}
            
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 20px 0 10px; border-left: 4px solid gold; padding-left: 8px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; border-radius: 10px; overflow: hidden; }}
            .flight-table td {{ padding: 10px 5px; border-bottom: 1px solid #222; text-align: center; }}
            
            /* ボタン・タイマー */
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; border: none; cursor: pointer; }}
            .footer-timer {{ text-align: center; color: #888; font-size: 13px; padding: 20px 0; border-top: 1px solid #222; margin-top: 20px; }}
            #timer {{ color: #FFD700; font-weight: bold; font-size: 16px; }}
            .disclaimer {{ font-size: 11px; color: #666; line-height: 1.4; margin-top: 10px; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v2";
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
            <div class="info-banner">⚠️ 分析：直近300便解析中 | 狙い目：{target_keys[best_idx] if best_idx != -1 else "解析中"}</div>
            
            <div class="rank-card">
                <div style="font-size:40px;">{sym} <span class="rank-display">{r}</span></div>
                <div style="font-size:24px; font-weight:bold;">{st}</div>
            </div>

            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div style="color:#999;font-size:12px;">1号(T1南)</div><div class="t-num">{demand_results.get('1号(T1南)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div style="color:#999;font-size:12px;">2号(T1北)</div><div class="t-num">{demand_results.get('2号(T1北)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==2 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==2 else '' }<div style="color:#999;font-size:12px;">3号(T2)</div><div class="t-num">{demand_results.get('3号(T2)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==3 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==3 else '' }<div style="color:#999;font-size:12px;">4号(T2)</div><div class="t-num">{demand_results.get('4号(T2)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==4 else ''}" style="grid-column: 1/3;">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==4 else '' }<div style="color:#999;font-size:12px;">国際(T3)</div><div class="t-num">{demand_results.get('国際(T3)', 0)}人</div></div>
            </div>

            <div class="section-title">✈️ 分析の根拠 (直近の着陸便)</div>
            <table class="flight-table">
                <tr style="color:gold; font-size:11px;"><td>時刻</td><td>便名</td><td>出身</td><td>推計</td></tr>
    """

    # フライトリストの生成（00+00回避ロジック込）
    for f in flight_list[:8]:
        raw_time = f.get('arrival_time', '')
        try:
            t = raw_time.split('T')[1][:5] if 'T' in raw_time else raw_time[:5]
        except:
            t = "--:--"
            
        origin = f.get('origin', '---')
        origin_jp = AIRPORT_MAP.get(origin, origin)
        pax_val = f.get('pax') or 150
        
        html_content += f"<tr><td>{t}</td><td style='color:gold;'>{f['flight_iata']}</td><td>{origin_jp}</td><td>{pax_val}名</td></tr>"

    html_content += f"""
            </table>

            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            
            <div class="disclaimer">
                ⚠️ 本システムは航空機データのみに基づいています。実際の行列や台数はオンラインサロン等で確認してください。
            </div>

            <div class="footer-timer">
                画面の自動再読み込みまであと <span id="timer">60</span> 秒<br>
                最終更新: {now_str} | v2.0 Master Layout
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
    # テスト用ファイル名で保存
    with open("index_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ renderer_new.py：v7.7の全機能を統合したHTMLを作成しました。")