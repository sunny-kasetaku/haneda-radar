import os
import json
from datetime import datetime, timedelta
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand

def main():
    # --- 1. 日本時間の現在時刻を取得 ---
    now_jst = datetime.utcnow() + timedelta(hours=9)
    print(f"DEBUG: Current JST Time: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

    # APIキーの取得（GitHub Secretsから）
    api_key = os.environ.get("AVIATION_STACK_API_KEY")
    if not api_key:
        print("Error: API Key not found.")
        return

    # --- 2. データの取得 ---
    today_str = now_jst.strftime('%Y-%m-%d')
    flights = fetch_flight_data(api_key, today_str)

    if not flights:
        print("No flight data fetched.")
        return

    # --- 3. 分析の実行 ---
    report = analyze_demand(flights)

    # --- 4. HTMLの生成 ---
    html_content = generate_html(report, now_jst)
    
    # 保存（GitHub Pages用）
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Success: Report generated (index.html)")

def generate_html(report, now):
    """
    分析レポートをHTML形式に変換する
    """
    # ランク判定
    total_pax = sum([report.get("1号(T1南)", 0), report.get("2号(T1北)", 0), 
                     report.get("3号(T2)", 0), report.get("4号(T2)", 0), 
                     report.get("国際(T3)", 0)])
    
    if total_pax >= 2000: rank, label = "🌈 S", "【最高】 需要爆発"
    elif total_pax >= 1000: rank, label = "🔥 A", "【高】 稼ぎ時"
    elif total_pax >= 500: rank, label = "✅ B", "【中】 安定"
    else: rank, label = "⚠️ C", "【低】 忍耐"

    # フライトリストの行生成
    rows = ""
    for f in report['flights']:
        t_disp = f.get('arrival_time', '00:00:00')[11:16]
        rows += f"<tr><td>{t_disp}</td><td style='color:gold;'>{f['flight_number']}</td><td>{f['origin']}</td><td>{f.get('pax_estimated', 0)}名</td></tr>"

    # 予測行の生成
    f_rows = ""
    for k in ["h1", "h2", "h3"]:
        item = report['forecast'][k]
        f_rows += f"""<div class="fc-row">
            <div class="fc-time">[{item['label']}]</div>
            <div class="fc-main"><span class="fc-status">{item['status']}</span><span class="fc-pax">(推計 {item['pax']}人)</span></div>
            <div class="fc-comment">└ {item['comment']}</div>
        </div>"""

    # --- HTMLの雛形（コード内に直接配置） ---
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-weight: bold; margin-bottom: 15px; font-size: 14px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 80px; font-weight: bold; color: #FFD700; line-height: 1; }}
            .rank-sub {{ font-size: 20px; font-weight: bold; margin-top:5px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; margin-top:5px; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 15px 0 5px 0; border-left: 4px solid gold; padding-left: 10px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; border-radius:10px; overflow:hidden; margin-bottom: 25px; }}
            .flight-table th {{ color:gold; padding:10px; border-bottom:1px solid #333; }}
            .flight-table td {{ padding: 10px; border-bottom: 1px solid #222; text-align: center; }}
            .forecast-box {{ background: #111; border: 1px solid #444; border-radius: 15px; padding: 15px; }}
            .fc-row {{ border-bottom: 1px dashed #333; padding: 10px 0; }}
            .fc-time {{ font-size: 14px; color: #FFD700; font-weight: bold; }}
            .fc-pax {{ color: #00FF00; font-weight: bold; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 15px; font-size: 20px; font-weight: bold; border: none; cursor: pointer; margin-top:20px; }}
            .footer {{ text-align:center; color:#666; font-size:11px; padding: 20px 0 40px 0; }}
        </style>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲: 過去60分〜未来30分 | 実数: {report['unique_count']}機</div>
            <div class="rank-card">
                <div class="rank-display">{rank}</div>
                <div class="rank-sub">{label}</div>
            </div>
            <div class="grid">
                <div class="t-card"><div style="color:#999;font-size:12px;">1号(T1南)</div><div class="t-num">{report.get("1号(T1南)", 0)}</div></div>
                <div class="t-card best-choice"><div class="best-badge">🏆 BEST</div><div style="color:#999;font-size:12px;">2号(T1北)</div><div class="t-num">{report.get("2号(T1北)", 0)}</div></div>
                <div class="t-card"><div style="color:#999;font-size:12px;">3号(T2)</div><div class="t-num">{report.get("3号(T2)", 0)}</div></div>
                <div class="t-card"><div style="color:#999;font-size:12px;">4号(T2)</div><div class="t-num">{report.get("4号(T2)", 0)}</div></div>
                <div class="t-card" style="grid-column: 1/3;"><div style="color:#999;font-size:12px;">国際(T3)</div><div class="t-num">{report.get("国際(T3)", 0)}</div></div>
            </div>
            <div class="section-title">✈️ 分析の根拠</div>
            <table class="flight-table">
                <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="section-title">📈 今後の需要予測</div>
            <div class="forecast-box">{f_rows}</div>
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer">最終データ取得: {now.strftime('%H:%M')} | JST Sync Mode</div>
        </div>
    </body>
    </html>
    """
    return html_template

if __name__ == "__main__":
    main()