import os
from datetime import datetime

def generate_html_new(demand_results, flight_list):
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

    # 数値集計
    total = sum(v for k, v in demand_results.items() if k not in ["forecast", "unique_count"])
    if total >= 800: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 400: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total >= 100: r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    else:              r, c, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"

    now_str = datetime.now().strftime('%H:%M')
    forecast = demand_results.get("forecast", {})
    
    # 時間枠データの安全な取得
    h1 = forecast.get('h1', {"label": "-", "pax": 0})
    h2 = forecast.get('h2', {"label": "-", "pax": 0})
    h3 = forecast.get('h3', {"label": "-", "pax": 0})

    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    pax_counts = [demand_results.get(k, 0) for k in target_keys]
    max_val = max(pax_counts) if pax_counts else 0
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-size: 14px; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 25px 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {c}; line-height: 1; }}
            .forecast-box {{ background: #111; border: 1px dashed #444; border-radius: 15px; padding: 15px; margin-bottom: 20px; }}
            .forecast-grid {{ display: flex; justify-content: space-around; text-align: center; }}
            .fc-label {{ font-size: 11px; color: #888; }}
            .fc-pax {{ font-size: 20px; font-weight: bold; color: #00FF00; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 20px 0 10px; border-left: 4px solid gold; padding-left: 8px; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; border: none; cursor: pointer; }}
        </style>
        <script>
            function checkPass() {{
                const storageKey = "kasetack_auth_pass_v2";
                if (localStorage.getItem(storageKey) === "kase") {{
                    document.getElementById('main-content').style.display = 'block';
                }} else {{
                    if (prompt("パスワードを入力") === "kase") {{
                        localStorage.setItem(storageKey, "kase");
                        location.reload();
                    }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">分析：直近300便（実数: {demand_results.get('unique_count', 0)}機）</div>
            <div class="rank-card">
                <div style="font-size:40px;">{sym} <span class="rank-display">{r}</span></div>
                <div style="font-size:24px; font-weight:bold;">{st}</div>
            </div>
            <div class="section-title">🕒 3時間先までの予測</div>
            <div class="forecast-box">
                <div class="forecast-grid">
                    <div class="forecast-item">
                        <div class="fc-label">{h1['label']}</div>
                        <div class="fc-pax">{h1['pax']}人</div>
                    </div>
                    <div class="forecast-item" style="border-left: 1px solid #333; padding-left:10px;">
                        <div class="fc-label">{h2['label']}</div>
                        <div class="fc-pax">{h2['pax']}人</div>
                    </div>
                    <div class="forecast-item" style="border-left: 1px solid #333; padding-left:10px;">
                        <div class="fc-label">{h3['label']}</div>
                        <div class="fc-pax">{h3['pax']}人</div>
                    </div>
                </div>
            </div>
            <div class="grid">
                <div class="t-card {'best-choice' if best_idx==0 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==0 else '' }<div style="color:#999;font-size:12px;">1号(T1南)</div><div class="t-num">{demand_results.get('1号(T1南)', 0)}</div></div>
                <div class="t-card {'best-choice' if best_idx==1 else ''}">{ '<div class="best-badge">🏆 BEST</div>' if best_idx==1 else '' }<div style="color:#999;font-size:12px;">2号(T1北)</div><div class="t-num">{demand_results.get('2号(T1北)', 0)}</div></div>
                <div class="t-card {'best-choice' if