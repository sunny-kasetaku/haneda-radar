import os
from datetime import datetime

def generate_html_new(demand_results, _):
    flight_list = demand_results.get("flights", [])
    
    # ランク判定
    total = sum(v for k, v in demand_results.items() if k not in ["forecast", "unique_count", "flights"])
    if total >= 600: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 300: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    else:              r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"

    # テーブル行作成
    table_rows = "".join([f"<tr><td>{f.get('arrival_time','')[11:16]}</td><td style='color:gold;'>{f.get('flight_iata')}</td><td>{f.get('origin')}</td><td>{f.get('pax_estimated')}名</td></tr>" for f in flight_list[:10]])

    # カード作成
    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    pax_counts = [demand_results.get(k, 0) for k in target_keys]
    max_val = max(pax_counts) if pax_counts else 0
    best_idx = pax_counts.index(max_val) if max_val > 0 else -1
    
    cards_html = ""
    for i, name in enumerate(target_keys):
        cls = "best-choice" if i == best_idx else ""
        badge = '<div class="best-badge">🏆 BEST</div>' if i == best_idx else ""
        style = 'style="grid-column: 1/3;"' if name == "国際(T3)" else ""
        cards_html += f'<div class="t-card {cls}" {style}>{badge}<div style="color:#888;font-size:12px;">{name}</div><div class="t-num">{demand_results.get(name)}人</div></div>'

    # 予測データ（エラー回避のため事前に変数化）
    f = demand_results.get("forecast", {})
    h1_l, h1_p = f['h1']['label'], f['h1']['pax']
    h2_l, h2_p = f['h2']['label'], f['h2']['pax']
    h3_l, h3_p = f['h3']['label'], f['h3']['pax']

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.5; background:#fff; }} 100% {{ opacity: 1; background:#000; }} }}
            body.loading {{ animation: flash 0.4s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-weight: bold; margin-bottom: 15px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 25px 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 100px; font-weight: bold; color: {c}; line-height: 1; }}
            .forecast-box {{ background: #111; border: 1px dashed #444; border-radius: 15px; padding: 15px; margin-bottom: 15px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 20px 0 10px; border-left: 4px solid gold; padding-left: 8px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; }}
            .flight-table td {{ padding: 10px 5px; border-bottom: 1px solid #222; text-align: center; }}
            .cam-link {{ display: block; text-align: center; padding: 15px; background: #333; color: #FFD700; text-decoration: none; border-radius: 12px; margin-bottom: 20px; font-weight: bold; border: 1px solid #444; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 20px; font-size: 24px; font-weight: bold; border: none; cursor: pointer; }}
        </style>
        <script>
            function checkPass() {{
                if (localStorage.getItem("kasetack_auth_pass_v2") === "kase") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                }} else {{
                    if (prompt("パスワード入力") === "kase") {{ localStorage.setItem("kasetack_auth_pass_v2", "kase"); location.reload(); }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 300便解析 | 実数: {demand_results.get('unique_count')}機</div>
            
            <div class="rank-card">
                <div>{sym} <span class="rank-display">{r}</span></div>
                <div style="font-size:24px; font-weight:bold;">{st}</div>
            </div>

            <a href="https://www.youtube.com/results?search_query=羽田空港+ライブカメラ" target="_blank" class="cam-link">🎥 ライブカメラで現場を確認</a>

            <div class="section-title">🕒 3時間先までの予測（機材推計込）</div>
            <div class="forecast-box">
                <div style="display:flex; justify-content:space-around; text-align:center;">
                    <div><div style="font-size:11px; color:#888;">{h1_l}</div><div style="font-size:20px; font-weight:bold; color:#00FF00;">{h1_p}人</div></div>
                    <div style="border-left:1px solid #333; padding-left:10px;"><div style="font-size:11px; color:#888;">{h2_l}</div><div style="font-size:20px; font-weight:bold; color:#00FF00;">{h2_p}人</div></div>
                    <div style="border-left:1px solid #333; padding-left:10px;"><div style="font-size:11px; color:#888;">{h3_l}</div><div style="font-size:20px; font-weight:bold; color:#00FF00;">{h3_p}人</div></div>
                </div>
            </div>

            <div class="grid">{cards_html}</div>

            <div class="section-title">✈️ 分析の根拠</div>
            <table class="flight-table"><tr style="color:gold; font-size:11px;"><td>時刻</td><td>便名</td><td>出発地</td><td>推計</td></tr>{table_rows}</table>

            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            
            <div style="font-size:11px; color:#666; margin-top:15px; line-height:1.4; padding:10px; border:1px solid #222;">
                【免責事項】 本システムはAviationstack APIデータと機材サイズ推計（30/70/150/250名）による期待値です。実際の行列を保証するものではありません。
            </div>

            <div style="text-align:center; color:#888; font-size:12px; margin-top:20px; padding-bottom:30px;">
                自動更新まで <span id="timer" style="color:gold; font-weight:bold; font-size:16px;">60</span> 秒 | {datetime.now().strftime('%H:%M')} 更新
            </div>
        </div>
        <script>let sec=60; setInterval(()=>{{ sec--; if(sec>=0) document.getElementById('timer').innerText=sec; if(sec<=0) location.reload(true); }},1000);</script>
    </body></html>
    """
    with open("index_test.html", "w", encoding="utf-8") as f: f.write(html_content)