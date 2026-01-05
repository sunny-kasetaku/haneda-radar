import requests
import datetime
import os
import random
import re

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 10px; font-size: 1.5rem; color: #fff; display: flex; justify-content: space-between; align-items: center; }
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #444; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .rank-display { text-align: center; margin-bottom: 15px; }
    .rank-text { font-size: 2.5rem; font-weight: bold; color: #fff; margin: 0; }
    .basis-badge { background: rgba(255,215,0,0.1); color: #FFD700; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; border: 1px solid #FFD700; }
    
    .stand-container { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 15px 0; }
    .stand-card { background: #2a2a2a; padding: 10px; border-radius: 8px; border: 1px solid #555; text-align: center; }
    .stand-card.highlight { border-color: #FFD700; background: rgba(255,215,0,0.05); }
    .stand-name { font-size: 0.8rem; color: #aaa; margin-bottom: 5px; }
    .stand-pax { font-size: 1.3rem; font-weight: bold; color: #fff; }

    .advice-box { background: #222; border-left: 5px solid #FFD700; padding: 15px; border-radius: 4px; margin-bottom: 20px; line-height: 1.6; }
    
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 15px; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 1px solid #444; padding: 8px; }
    .flight-list td { padding: 8px; border-bottom: 1px solid #333; }
    
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; margin-top: 10px; }
    .footer { font-size: 0.75rem; color: #666; margin-top: 20px; text-align: center; }
</style></head>
<body><div class="container">
<div class="main-title">🚖 KASETACK <span>[[TIME]]</span></div>
<div id="report-box">
    <div class="rank-display">
        <p class="rank-text">[[RANK]]</p>
        <span class="basis-badge">[[BASIS]]</span>
    </div>

    <div class="stand-container">
        <div class="stand-card [[H1]]"><div class="stand-name">1号 (T1南)</div><div class="stand-pax">[[P1]] 人</div></div>
        <div class="stand-card [[H2]]"><div class="stand-name">2号 (T1北)</div><div class="stand-pax">[[P2]] 人</div></div>
        <div class="stand-card [[H3]]"><div class="stand-name">3・4号 (T2)</div><div class="stand-pax">[[P3]] 人</div></div>
        <div class="stand-card [[H4]]"><div class="stand-name">国際 (T3)</div><div class="stand-pax">[[P4]] 人</div></div>
    </div>

    <div class="advice-box">
        <strong>⚡ 推奨：[[TARGET]]</strong><br>
        <span>[[REASON]]</span>
    </div>

    <div style="background:#2a2a2a; padding:10px; border-radius:8px; font-size:0.9rem;">
        🅿️ プール予測: [[POOL_WAIT]]
    </div>

    <h3>✈️ 到着便明細 (直近60分)</h3>
    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>出発地</th><th>予測</th></tr></thead>
        <tbody>[[FLIGHT_ROWS]]</tbody>
    </table>

    <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
</div>
<div class="footer">
    ※推計人数は搭乗率統計に基づく予測です。最終判断は自己責任でお願いします。<br>
    DEBUG: [[DEBUG]] | PASS: [[PASS]]
</div>
</div></body></html>
"""

def fetch_haneda_precision_stands():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    headers = {"User-Agent": "Mozilla/5.0"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    flight_rows = ""
    total_pax = 0

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            # 簡易的なスクレイピングで便名、時刻、航空会社を取得
            flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+).*?<td>(.*?)</td>', r.text, re.DOTALL)
            for h, m, ampm, carrier, fnum, origin in flights:
                f_h = int(h)
                if ampm == "PM" and f_h < 12: f_h += 12
                elif ampm == "AM" and f_h == 12: f_h = 0
                f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
                diff = (f_t - now).total_seconds() / 60
                
                if -15 < diff < 45:
                    pax = 180 if carrier in ["JL", "NH", "BC", "7G", "6J"] else 220
                    # 搭乗率補正
                    rate = 0.85 if (22 <= now.hour or now.hour <= 2) else 0.65
                    est_pax = int(pax * rate)
                    
                    stand_key = "P4" # デフォルト国際
                    if carrier in ["JL", "JTA", "NU"]: stand_key = "P1" # 本来は行き先でP1/P2分けるが簡易的にP1
                    elif carrier == "BC": stand_key = "P1"
                    elif carrier in ["NH", "ADO", "SNA", "FW"]: stand_key = "P3"
                    
                    stands[stand_key] += est_pax
                    total_pax += est_pax
                    flight_rows += f"<tr><td>{f_h:02d}:{int(m):02d}</td><td>{carrier}{fnum}</td><td>{origin[:8]}</td><td>{est_pax}人</td></tr>"
        
        status = "OK"
    except: status = "NetErr"
    
    return stands, flight_rows, total_pax, status

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    stands, rows, total, debug = fetch_haneda_precision_stands()
    
    # 最も人数が多い乗り場を特定
    best_stand_key = max(stands, key=stands.get)
    target_map = {"P1": "1号乗り場 (T1南)", "P2": "2号乗り場 (T1北)", "P3": "3・4号乗り場 (T2)", "P4": "国際線 (T3)"}
    target = target_map[best_stand_key] if total > 0 else "周辺待機・休憩推奨"
    
    if total > 800: rk, basis = "🌈 S 【 激熱 】", f"60分以内に計{total}名の降機予測"
    elif total > 300: rk, basis = "🔥 A 【 推奨 】", f"計{total}名の安定した需要"
    elif total > 0: rk, basis = "✨ B 【 注意 】", f"計{total}名の小規模需要"
    else: rk, basis = "🌑 D 【 撤退 】", "有効な到着便なし"

    # プール予測（統計）
    pool_wait = "混雑：中（30-50分）" if 0 <= n.hour <= 2 else "混雑：低（15-30分）"
    
    reason = f"現在は{target}の期待値が最大です。降機後のタイムラグを含め、今から並ぶのが最も効率的です。" if total > 0 else "有効な到着便がありません。無理な入庫は避け、次回の波を待ちましょう。"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[TIME]]", n.strftime('%H:%M')) \
        .replace("[[P1]]", str(stands['P1'])).replace("[[P2]]", str(stands['P2'])).replace("[[P3]]", str(stands['P3'])).replace("[[P4]]", str(stands['P4'])) \
        .replace("[[H1]]", "highlight" if best_stand_key=="P1" else "").replace("[[H2]]", "highlight" if best_stand_key=="P2" else "") \
        .replace("[[H3]]", "highlight" if best_stand_key=="P3" else "").replace("[[H4]]", "highlight" if best_stand_key=="P4" else "") \
        .replace("[[TARGET]]", target).replace("[[REASON]]", reason).replace("[[POOL_WAIT]]", pool_wait) \
        .replace("[[FLIGHT_ROWS]]", rows if rows else "<tr><td colspan='4' style='text-align:center;'>対象便なし</td></tr>") \
        .replace("[[DEBUG]]", debug).replace("[[PASS]]", str(random.randint(1000, 9999)))

    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
