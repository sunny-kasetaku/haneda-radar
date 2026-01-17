import json
import os
from datetime import datetime, timedelta

def generate_html_new(demand_results, flight_list):
    """
    v7.7の全機能（タイマー、パスワード、日本語化、BEST表示）を継承し、
    新しい「証拠・予測」レイアウトを統合した最終形態。
    """
    # --- 空港名マスター（v7.7継承） ---
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

    # スコア計算とランク判定
    total = sum(demand_results.values())
    if total >= 800: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 400: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total >= 100: r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    elif total >= 1:   r, c, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"
    else:              r, c, sym, st = "D", "#888", "🌑", "【撤退】 需要なし"

    now_dt = datetime.now()
    now_str = now_dt.strftime('%H:%M')
    
    # 狙い目（BEST）の判定
    pax_counts = list(demand_results.values())
    max_val = max(pax_counts) if pax_counts else 0
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    stand_names = list(demand_results.keys())

    # パスワード（v7.7から引用。適宜修正してください）
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
            
            /* v7.7 継承スタイル */
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-size: 14px; font-weight: bold; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 25px 20px; text-align: center; margin-bottom: 10px; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {c}; line-height: 1; }}
            
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; color: #FFF; }}
            
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 20px 0 10px; border-left: 4px solid gold; padding-left: 8px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; border-radius: 10px; overflow: hidden; }}
            .flight-table td {{ padding: 10px 5px; border-bottom: 1px solid #222; text-align: center; }}
            
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; margin: 20px 0; border: none; cursor: pointer; }}
            .btn-camera {{ display: block; background: #444; color: #fff; text-align: center; padding: 12px; border-radius: 10px; text-decoration: none; font-size: 14px; margin: 10px 0; border: 1px solid #666; }}
            
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
            <div class="info-banner">⚠️ 分析：直近300便 | 狙い目：{stand_names[best_idx] if best_idx != -1 else "解析中"}</div>
            
            <div class="rank-card">
                <div style="font-size:40px;">{sym} <span class="rank-display">{r}</span></div>
                <div style="font-size:24px; font-weight:bold;">{st}</div>
                <div style="display: flex; justify-content: space-around; font-size: 10px; color: #999; margin-top: 15px; padding-top: 10px; border-top: 1px solid #333;">
                    <span>🌈<b>S</b>:800~</span><span>🔥<b>A</b>:400~</span><span>✅<b>B</b>:100~</span><span>⚠️<b>C</b>:1~</span><span>🌑<b>D</b>:0</span>
                </div>
            </div>

            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div style="color:#999;font-size:12px;">1号(T1南)</div><div class="t-num">{demand_results.get('1号 (T1/JAL系)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div style="color:#999;font-size:12px;">2号(T1北)</div><div class="t-num">0人</div></div>
                <div class="t-card {'best-choice' if best_idx==2 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==2 else '' }<div style="color:#999;font-size:12px;">3号(T2)</div><div class="t-num">{demand_results.get('2号 (T2/ANA系)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==3 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==3 else '' }<div style="color:#999;font-size:12px;">4号(T2)</div><div class="t-num">{demand_results.get('4号 (T2/国際)', 0)}人</div></div>
                <div class="t-card {'best-choice' if best_idx==4 else ''}" style="grid-column: 1/3;">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==4 else '' }<div style="color:#999;font-size:12px;">国際(T3)</div><div class="t-num">{demand_results.get('3号 (T3/国際)', 0)}人</div></div>
            </div>

            <div class="section-title">✈️ 分析の根拠 (直近の着陸便)</div>
            <table class="flight-table">
                <tr style="color:gold; font-size:11px;"><td>時刻</td><td>便名</td><td>出身</td><td>結果</td></tr>
    """

    for f in flight_list[:8]:
        t = f['arrival_time'].split('T')[1][:5] if 'T' in f['arrival_time'] else f['arrival_time'][:5]
        origin = f.get('origin', '---')
        origin_jp = AIRPORT_MAP.get(origin, origin) # 日本語名に変換
        html_content += f"<tr><td>{t}</td><td style='color:gold;'>{f['flight_iata']}</td><td>{origin_jp}</td><td>着陸済</td></tr>"

    html_content += f"""
            </table>

            <div class="section-title">📈 今後の需要予測 (3時間先)</div>
            <div style="background:#1A1A1A; padding:15px; border-radius:12px; font-size:14px; border:1px solid #333;">
                ・この後1時間： 🔥 高め<br>
                ・その後の波： 👀 14時台に大型便集中
            </div>

            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            
            <a href="https://www.google.com/search?q=羽田空港+タクシー乗り場+ライブカメラ" class="btn-camera" target="_blank">📹 ライブカメラを確認 (外部)</a>

            <div class="disclaimer">
                ⚠️ 本システムは航空機の到着実績のみに基づいています。実際の乗り場の行列や待機台数は考慮していません。オンラインサロンの報告も併せて確認し、最終判断はご自身で行ってください。
            </div>

            <div class="footer-timer">
                画面の自動再読み込みまであと <span id="timer">60</span> 秒<br>
                最終データ取得: {now_str} | v7.7 Final Layout
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
    with open("index_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 継承完了：v7.7の機能を含んだ index_test.html を作成しました。")