import os
import json
from datetime import datetime, timedelta
from api_handler_v2 import fetch_flight_data
from analyzer_v2 import analyze_demand

def main():
    # --- 1. 日本時間の現在時刻を取得 ---
    # ここを修正し、システム全体の「時計」を日本時間に合わせます
    now_jst = datetime.utcnow() + timedelta(hours=9)
    print(f"DEBUG: Current JST Time: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

    # APIキーの取得（GitHub Secretsから）
    api_key = os.environ.get("AVIATION_STACK_API_KEY")
    if not api_key:
        print("Error: API Key not found.")
        return

    # --- 2. データの取得 ---
    # 日本日付でデータを取得
    today_str = now_jst.strftime('%Y-%m-%d')
    flights = fetch_flight_data(api_key, today_str)

    if not flights:
        print("No flight data fetched.")
        return

    # --- 3. 分析の実行 ---
    # 日本時間で分析を行います
    report = analyze_demand(flights)

    # --- 4. HTMLの生成 ---
    html_content = generate_html(report, now_jst)
    
    # 保存（GitHub Pages用）
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Success: Report generated (index.html)")

def generate_html(report, now):
    """
    分析レポートをHTML形式に流し込む
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
        # 表示用に時刻を整形（秒を削る）
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

    # HTMLテンプレート (時刻表示部分を日本時間に修正)
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    # 変数の置換
    html = template.replace("{{RANK}}", rank)
    html = html.replace("{{RANK_LABEL}}", label)
    html = html.replace("{{T1_SOUTH}}", str(report.get("1号(T1南)", 0)))
    html = html.replace("{{T1_NORTH}}", str(report.get("2号(T1北)", 0)))
    html = html.replace("{{T2_3}}", str(report.get("3号(T2)", 0)))
    html = html.replace("{{T2_4}}", str(report.get("4号(T2)", 0)))
    html = html.replace("{{T3}}", str(report.get("国際(T3)", 0)))
    html = html.replace("{{FLIGHT_ROWS}}", rows)
    html = html.replace("{{FORECAST_ROWS}}", f_rows)
    html = html.replace("{{TOTAL_FLIGHTS}}", str(report['unique_count']))
    # ここが重要：JSTの現在時刻を表示する
    html = html.replace("{{UPDATE_TIME}}", now.strftime('%H:%M'))

    return html

if __name__ == "__main__":
    main()