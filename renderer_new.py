# renderer_new.py
# ---------------------------------------------------------
# HTML Generator (Fix: Exclude string keys from sum)
# ---------------------------------------------------------
import os
from datetime import datetime, timedelta

def generate_html_new(demand_results, daily_password):
    
    flight_list = demand_results.get("flights", [])
    
    AIRPORT_MAP = {
        "CTS":"新千歳", "FUK":"福岡", "OKA":"那覇", "ITM":"伊丹", "KIX":"関空",
        "NGO":"中部", "KMQ":"小松", "HKD":"函館", "HIJ":"広島", "MYJ":"松山",
        "KCZ":"高知", "TAK":"高松", "KMJ":"熊本", "KMI":"宮崎", "KOJ":"鹿児島",
        "ISG":"石垣", "MMY":"宮古", "IWK":"岩国", "UBJ":"山口宇部", "TKS":"徳島",
        "AOJ":"青森", "MSJ":"三沢", "OIT":"大分", "AXT":"秋田", "GAJ":"山形",
        "HNL":"ホノルル", "JFK":"NY(JFK)", "LAX":"ロス", "SFO":"サンフランシスコ",
        "LHR":"ロンドン", "CDG":"パリ", "FRA":"フランクフルト", "HEL":"ヘルシンキ",
        "DXB":"ドバイ", "DOH":"ドーハ", "SIN":"ｼﾝｶﾞﾎﾟｰﾙ", "BKK":"ﾊﾞﾝｺｸ",
        "KUL":"ｸｱﾗﾙﾝﾌﾟｰﾙ", "CGK":"ｼﾞｬｶﾙﾀ", "MNL":"マニラ", "SGN":"ホーチミン",
        "HAN":"ハノイ", "HKG":"香港", "TPE":"台北(桃園)", "TSA":"台北(松山)",
        "ICN":"ソウル(仁川)", "GMP":"ソウル(金浦)", "PEK":"北京", "PVG":"上海(浦東)",
        "SHA":"上海(虹橋)", "DLC":"大連", "CAN":"広州"
    }

    # 1. ランク判定
    # ★修正箇所： "update_time" を除外リストに追加しました
    ignore_keys = ["forecast", "unique_count", "flights", "update_time"]
    total = sum(v for k, v in demand_results.items() if k not in ignore_keys)
    
    if total >= 600: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 300: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total >= 100: r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    else:              r, c, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"

    # 2. カード生成
    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    pax_counts = [demand_results.get(k, 0) for k in target_keys]
    max_val = max(pax_counts) if pax_counts else 0
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1

    cards_html = ""
    for i, name in enumerate(target_keys):
        is_best = (i == best_idx)
        cls = "best-choice" if is_best else ""
        style = 'style="grid-column: 1/3;"' if name == "国際(T3)" else ""
        badge = '<div class="best-badge">🏆 BEST</div>' if is_best else ""
        
        cards_html += f"""
        <div class="t-card {cls}" {style}>
            {badge}
            <div style="color:#999;font-size:12px;">{name}</div>
            <div class="t-num">{demand_results.get(name, 0)}人</div>
        </div>
        """

    # 3. テーブル生成
    table_rows = ""
    for f in flight_list:
        raw_time = str(f.get('arrival_time', ''))
        # Tがある場合のみスライス、なければそのままか空白
        if 'T' in raw_time and len(raw_time) >= 16:
            time_str = raw_time[11:16]
        else:
            time_str = raw_time if raw_time else "---"
            
        pax_disp = f"{f.get('pax_estimated')}名" if f.get('pax_estimated') else "---"
        origin_code = f.get('origin', '')
        origin_name = AIRPORT_MAP.get(origin_code, origin_code)

        table_rows += f"""
        <tr>
            <td>{time_str}</td>
            <td style='color:gold;'>{f.get('flight_iata')}</td>
            <td>{origin_name}</td>
            <td>{pax_disp}</td>
        </tr>
        """

    # 4. 予測生成
    f_data = demand_results.get("forecast", {})
    forecast_html = ""
    for k in ["h1", "h2", "h3"]:
        item = f_data.get(k, {})
        forecast_html += f"""
        <div class="fc-row">
            <div class="fc-time">[{item.get('label','--:--')}]</div>
            <div class="fc-main">
                <span class="fc-status">{item.get('status','-')}</span>
                <span class="fc-pax">(推計 {item.get('pax',0)}人)</span>
            </div>
            <div class="fc-comment">└ {item.get('comment','-')}</div>
        </div>
        """

    # 最終更新時刻（Analyzerから受け取ったものがあれば使う）
    update_str = demand_results.get("update_time", datetime.now().strftime('%H:%M'))

    # 5. HTML組み立て
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK Radar</title>
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 0.8; }} 100% {{ opacity: 1; }} }}
            body.loading {{ animation: flash 0.8s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-weight: bold; margin-bottom: 15px; font-size: 14px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 80px; font-weight: bold; color: {c}; line-height: 1; }}
            .rank-sub {{ font-size: 20px; font-weight: bold; margin-top:5px; }}
            .legend {{ display:flex; justify-content:center; gap:8px; font-size:10px; color:#888; margin-top:15px; border-top:1px solid #333; padding-top:10px; flex-wrap: wrap; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255,215,0,0.2); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; margin-top:5px; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 0 0 5px 0; border-left: 4px solid gold; padding-left: 10px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; border-radius:10px; overflow:hidden; margin-bottom: 25px; }}
            .flight-table th {{ color:gold; padding:10px; border-bottom:1px solid #333; text-align:center; }}
            .flight-table td {{ padding: 10px; border-bottom: 1px solid #222; text-align: center; }}
            .forecast-box {{ background: #111; border: 1px solid #444; border-radius: 15px; padding: 15px; margin-bottom: 20px; }}
            .fc-row {{ border-bottom: 1px dashed #333; padding: 10px 0; }}
            .fc-row:last-child {{ border-bottom: none; }}
            .fc-time {{ font-size: 14px; color: #FFD700; font-weight: bold; margin-bottom: 4px; }}
            .fc-main {{ font-size: 16px; margin-bottom: 2px; }}
            .fc-status {{ font-weight: bold; color: #fff; margin-right: 5px; }}
            .fc-pax {{ color: #00FF00; font-weight: bold; }}
            .fc-comment {{ font-size: 12px; color: #888; margin-left: 10px; }}
            .cam-box {{ background:#111; border:1px solid #444; border-radius:15px; padding:15px; margin-bottom:20px; text-align:center; }}
            .cam-title {{ color:#FFD700; font-weight:bold; font-size:14px; margin-bottom:10px; }}
            .cam-btn {{ display: block; padding: 12px; background: #FFD700; color: #000; text-decoration: none; border-radius: 8px; font-weight: bold; font-size:13px; margin-bottom:10px; }}
            .disclaimer {{ font-size: 10px; color: #888; text-align: left; line-height: 1.4; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 15px; font-size: 20px; font-weight: bold; border: none; cursor: pointer; margin-bottom:20px; }}
            .footer {{ text-align:center; color:#666; font-size:11px; padding-bottom:30px; }}
        </style>
        <script>
            const TODAY_PASS = "{daily_password}";

            function checkPass() {{
                const savedPass = localStorage.getItem("haneda_auth_pass_daily");
                if (savedPass === TODAY_PASS) {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                }} else {{
                    const userLayout = prompt("【本日のパスワード】数字4桁を入力してください");
                    if (userLayout === TODAY_PASS) {{
                        localStorage.setItem("haneda_auth_pass_daily", TODAY_PASS);
                        document.getElementById('main-content').style.display = 'block';
                        document.body.classList.add('loading');
                    }} else {{
                        alert("パスワードが違います。Discordを確認してください。");
                        location.reload();
                    }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲: 直近75分 | 実数: {demand_results.get('unique_count')}機</div>
            
            <div class="rank-card">
                <div class="rank-display">{sym} {r}</div>
                <div class="rank-sub">{st}</div>
                <div class="legend">
                    <span>🌈S:600~</span> <span>🔥A:300~</span> <span>✅B:100~</span> <span>⚠️C:1~</span>
                </div>
            </div>

            <div class="grid">{cards_html}</div>

            <div class="section-title">✈️ 分析の根拠</div>
            <table class="flight-table">
                <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>

            <div class="section-title">📈 今後の需要予測 (3時間先)</div>
            <div class="forecast-box">
                {forecast_html}
            </div>

            <div class="cam-box">
                <div class="cam-title">⚠️ 重要：最終判断の前に必ず確認</div>
                <a href="https://www.youtube.com/results?search_query=羽田空港+ライブカメラ" target="_blank" class="cam-btn">🎥 乗り場ライブカメラ (外部サイト)</a>
                <div class="disclaimer">
                    ※本システムは航空機のデータのみに基づいています。実際の行列やタクシー待機台数は考慮していません。オンラインサロンでの現地報告も併せて確認してください。
                </div>
            </div>

            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer">
                画面の自動再読み込みまであと <span id="timer" style="color:gold; font-weight:bold;">60</span> 秒<br>
                最終データ取得: {update_str} | v8.4 Daily-Pass
            </div>
        </div>
        <script>let sec=60; setInterval(()=>{{ sec--; if(sec>=0) document.getElementById('timer').innerText=sec; if(sec<=0) location.reload(true); }},1000);</script>
    </body></html>
    """
    
    # ★修正：本番用ファイル名 index.html に書き込み
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)