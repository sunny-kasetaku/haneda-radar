import datetime

def generate_html_new(demand_results, flight_list):
    """
    【新デザイン・レンダラー】
    - 判例と5段階評価を維持
    - 時間軸を整理（現状→根拠→未来）
    - 免責事項とカメラリンクを最下部に配置
    """
    total = sum(demand_results.values())
    
    # 5段階評価判定
    rank, rank_text, color, icon = ("D", "待機中", "#888", "🟣")
    if total >= 800: rank, rank_text, color, icon = ("S", "超絶", "#ff00ff", "🌈")
    elif total >= 400: rank, rank_text, color, icon = ("A", "推奨", "#ff4500", "🔥")
    elif total >= 100: rank, rank_text, color, icon = ("B", "期待", "#32cd32", "✅")
    elif total >= 1:   rank, rank_text, color, icon = ("C", "注意", "#ffa500", "⚠️")

    now_str = datetime.datetime.now().strftime('%H:%M:%S')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>羽田需要レーダー v2</title>
        <style>
            body {{ background: #121212; color: #eee; font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 10px; line-height: 1.6; }}
            .container {{ max-width: 500px; margin: 0 auto; }}
            .header {{ text-align: center; padding: 10px 0; border-bottom: 1px solid #333; }}
            .rank-card {{ background: #1e1e1e; border-radius: 12px; padding: 20px; text-align: center; margin: 15px 0; border: 1px solid #444; }}
            .rank-val {{ font-size: 5rem; font-weight: bold; color: {color}; margin: 0; }}
            .legend {{ display: flex; justify-content: space-between; font-size: 0.65rem; color: #999; margin-top: 10px; border-top: 1px solid #333; padding-top: 8px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
            .grid-item {{ background: #222; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #333; }}
            .grid-item b {{ font-size: 1.4rem; color: #fff; }}
            .grid-item.full {{ grid-column: span 2; border: 1px solid gold; background: #2a2a10; }}
            .section-title {{ font-size: 0.95rem; font-weight: bold; margin: 20px 0 10px; color: gold; display: flex; align-items: center; }}
            .list-card {{ background: #1e1e1e; border-radius: 8px; padding: 12px; margin-bottom: 15px; }}
            .flight-table {{ width: 100%; font-size: 0.85rem; border-collapse: collapse; }}
            .flight-table td {{ padding: 6px 4px; border-bottom: 1px solid #333; }}
            .btn-camera {{ display: block; background: #ffd700; color: #000; text-align: center; padding: 16px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin: 20px 0; }}
            .disclaimer {{ font-size: 0.75rem; color: #aaa; background: #252525; padding: 12px; border-radius: 6px; border-left: 4px solid #cc0000; }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <b>🚕 KASETACK 羽田需要レーダー</b><br>
            <span style="font-size:0.8rem; color:#888;">{now_str} 現在 <span style="display:inline-block; animation: spin 2s linear infinite;">🔄</span></span>
        </div>

        <div class="rank-card">
            <div style="font-size:0.9rem;">【{rank_text}】 需要予測スコア</div>
            <p class="rank-val">{icon}{rank}</p>
            <div class="legend">
                <span>🌈 S:800+</span> <span>🔥 A:400+</span> <span>✅ B:100+</span> <span>⚠️ C:1+</span> <span>🟣 D:0</span>
            </div>
        </div>

        <div class="grid">
            <div class="grid-item">1号(T1南)<br><b>{demand_results.get('1号 (T1/JAL系)', 0)}人</b></div>
            <div class="grid-item">2号(T1北)<br><b>0人</b></div>
            <div class="grid-item">3号(T2)<br><b>{demand_results.get('2号 (T2/ANA系)', 0)}人</b></div>
            <div class="grid-item">4号(T2)<br><b>{demand_results.get('4号 (T2/国際)', 0)}人</b></div>
            <div class="grid-item full">国際(T3)<br><b style="font-size:1.8rem;">{demand_results.get('3号 (T3/国際)', 0)}人</b></div>
        </div>

        <div class="section-title">✈️ 分析の根拠 (直近の着陸便)</div>
        <div class="list-card">
            <table class="flight-table">
    """
    
    # 証拠となるフライトリスト（最新8件）
    for f in flight_list[:8]:
        t = f['arrival_time'][-8:-3]
        html_content += f"<tr><td>{t}</td><td><b>{f['flight_iata']}</b></td><td>T{f['terminal']}</td><td style='color:#bbb;'>{f['airline']}</td></tr>"

    html_content += f"""
            </table>
        </div>

        <div class="section-title">📈 今後の需要予測 (3時間先)</div>
        <div class="list-card" style="font-size:0.85rem;">
            ・13時台： 👀 低 (約120人)<br>
            ・14時台： 🔥 高 (約380人)<br>
            ・15時台： 🚀 激 (約600人)
        </div>

        <a href="https://www.google.com/search?q=羽田空港+タクシー乗り場+ライブカメラ" class="btn-camera" target="_blank">📹 乗り場ライブカメラを確認</a>

        <div class="disclaimer">
            <b>⚠️ 重要：最終判断の前に必ず確認</b><br>
            本システムは航空機の到着データのみに基づいています。実際の乗り場の行列やタクシー待機台数は考慮していません。オンラインサロンの報告も併せて確認し、最終的な判断はご自身で行ってください。
        </div>

        <div style="text-align:center; font-size:0.6rem; color:#444; margin-top:30px; border-top:1px solid #222; padding-top:10px;">
            HND-RADAR v2.0 Test Build | Logic: 300-Page-Offset
        </div>
    </div>
    <style> @keyframes spin {{ 100% {{ transform:rotate(360deg); }} }} </style>
    </body>
    </html>
    """
    
    with open("index_test.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index_test.html を作成しました。")