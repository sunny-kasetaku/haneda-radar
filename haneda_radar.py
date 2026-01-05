import requests
import datetime
import os
import random
import re

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================================
# 📊 【マスターデータ】 現場の統計・定数（ここでチューニング可能）
# ==========================================================
STATS_CONFIG = {
    "BASE_PAX": {"INTL": 250, "DOM": 180},  # 1便あたりの基本定員
    "LOAD_FACTORS": {
        "MIDNIGHT": 0.85, # 22時-02時（深夜ボーナス）
        "RUSH": 0.80,     # 05時-09時 / 17時-20時
        "NORMAL": 0.65    # その他
    },
    "STAND_MAP": {
        "P1": ["JL", "JTA", "NU", "BC"],      # 1号 (T1南)
        "P2": [],                             # 2号 (T1北) ※JLの北行便
        "P3": ["NH", "ADO", "SNA", "FW", "7G"], # 3・4号 (T2)
        "P4": ["INTL"]                        # 国際 (T3) ※キャリアにないものは全てココ
    },
    "POOL_EXPECTATION": { # 時間帯別の予測待ち時間（統計）
        "0-2": "30-45分", "5-9": "90分超(回避推奨)", "DEFAULT": "20-30分"
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 10px; font-size: 1.5rem; color: #fff; display: flex; justify-content: space-between; }
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .rank-display { text-align: center; margin-bottom: 15px; }
    .rank-text { font-size: 2.8rem; font-weight: bold; color: #fff; margin: 0; text-shadow: 0 0 20px rgba(255,215,0,0.4); }
    .basis-badge { background: rgba(255,215,0,0.1); color: #FFD700; padding: 6px 15px; border-radius: 20px; font-size: 0.95rem; border: 1px solid #FFD700; display: inline-block; margin-top: 5px; }
    
    .stand-container { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
    .stand-card { background: #2a2a2a; padding: 12px; border-radius: 10px; border: 2px solid #444; text-align: center; transition: 0.3s; }
    .stand-card.highlight { border-color: #FFD700; background: rgba(255,215,0,0.1); box-shadow: 0 0 15px rgba(255,215,0,0.2); }
    .stand-name { font-size: 0.85rem; color: #bbb; margin-bottom: 5px; }
    .stand-pax { font-size: 1.5rem; font-weight: bold; color: #fff; }

    .advice-box { background: #222; border-left: 6px solid #FFD700; padding: 15px; border-radius: 4px; margin: 15px 0; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 15px; background: #1a1a1a; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 2px solid #333; padding: 10px; }
    .flight-list td { padding: 10px; border-bottom: 1px solid #2a2a2a; }
    
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; margin-top: 15px; box-shadow: 0 6px 0 #b89b00; }
    .footer { font-size: 0.75rem; color: #555; margin-top: 25px; text-align: center; line-height: 1.5; }
</style></head>
<body><div class="container">
<div class="main-title">🚖 KASETACK <span>[[TIME]]</span></div>
<div id="report-box">
    <div class="rank-display">
        <p class="rank-text">[[RANK]]</p>
        <div class="basis-badge">[[BASIS]]</div>
    </div>

    <div class="stand-container">
        <div class="stand-card [[H1]]"><div class="stand-name">1号 (T1南)</div><div class="stand-pax">[[P1]]人</div></div>
        <div class="stand-card [[H2]]"><div class="stand-name">2号 (T1北)</div><div class="stand-pax">[[P2]]人</div></div>
        <div class="stand-card [[H3]]"><div class="stand-name">3・4号 (T2)</div><div class="stand-pax">[[P3]]人</div></div>
        <div class="stand-card [[H4]]"><div class="stand-name">国際 (T3)</div><div class="stand-pax">[[P4]]人</div></div>
    </div>

    <div class="advice-box">
        <strong style="color:#FFD700;">🎯 戦術目標：[[TARGET]]</strong><br>
        <span style="font-size:0.95rem;">[[REASON]]</span>
    </div>

    <div style="background:#2a2a2a; padding:12px; border-radius:8px; font-size:0.9rem; border:1px solid #444;">
        🅿️ プール予測 (統計): <span style="color:#FFD700; font-weight:bold;">[[POOL_WAIT]]</span>
    </div>

    <h3 style="color:#FFD700; border-bottom:1px solid #444; padding-bottom:5px; margin-top:25px;">✈️ 到着エビデンス (直近60分)</h3>
    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>出発地</th><th>予測</th></tr></thead>
        <tbody>[[FLIGHT_ROWS]]</tbody>
    </table>

    <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
</div>
<div class="footer">
    【統計ハイブリッド型ロジック v2.0】<br>
    ※推計人数：機材定数×搭乗率統計（-15/+45分ウィンドウ）<br>
    DEBUG: [[DEBUG]] | PASS: [[PASS]]
</div>
</div></body></html>
"""

def fetch_haneda_hybrid():
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
            # 航空会社・便名・時刻・出発地を抽出
            flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+).*?<td>(.*?)</td>', r.text, re.DOTALL)
            
            # 搭乗率の決定
            rate = STATS_CONFIG["LOAD_FACTORS"]["NORMAL"]
            if 22 <= now.hour or now.hour <= 2: rate = STATS_CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
            elif (5 <= now.hour <= 9) or (17 <= now.hour <= 20): rate = STATS_CONFIG["LOAD_FACTORS"]["RUSH"]

            for h, m, ampm, carrier, fnum, origin in flights:
                f_h = int(h)
                if ampm == "PM" and f_h < 12: f_h += 12
                elif ampm == "AM" and f_h == 12: f_h = 0
                f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
                diff = (f_t - now).total_seconds() / 60
                
                # 🌟 60分ウィンドウ (-15分 〜 +45分)
                if -15 < diff < 45:
                    is_domestic = carrier in (STATS_CONFIG["STAND_MAP"]["P1"] + STATS_CONFIG["STAND_MAP"]["P3"])
                    base_cap = STATS_CONFIG["BASE_PAX"]["DOM"] if is_domestic else STATS_CONFIG["BASE_PAX"]["INTL"]
                    est_pax = int(base_cap * rate)
                    
                    # 乗り場判定
                    s_key = "P4" # デフォルト国際
                    if carrier in STATS_CONFIG["STAND_MAP"]["P1"]: s_key = "P1"
                    elif carrier in STATS_CONFIG["STAND_MAP"]["P3"]: s_key = "P3"
                    
                    stands[s_key] += est_pax
                    total_pax += est_pax
                    flight_rows += f"<tr><td>{f_h:02d}:{int(m):02d}</td><td>{carrier}{fnum}</td><td>{origin[:8]}</td><td>{est_pax}名</td></tr>"
        
        status = "OK"
    except: status = "NetErr"
    
    return stands, flight_rows, total_pax, status

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    stands, rows, total, debug = fetch_haneda_hybrid()
    
    # 判定・推奨アクション
    best_key = max(stands, key=stands.get)
    target_map = {"P1": "1号 (T1南)", "P2": "2号 (T1北)", "P3": "3・4号 (T2)", "P4": "国際線 (T3)"}
    target = target_map[best_key] if total > 0 else "待機・休憩推奨"
    
    if total > 800: rk, basis = "🌈 S 【 激熱 】", f"統計予測：計{total}名の集中降機"
    elif total > 300: rk, basis = "🔥 A 【 推奨 】", f"安定需要：計{total}名の降機予測"
    elif total > 0: rk, basis = "✨ B 【 注意 】", f"分散需要：計{total}名の降機予測"
    else: rk, basis = "🌑 D 【 撤退 】", "有効な到着便なし(安全装置)"

    # プール予測
    h_str = f"{n.hour}"
    pool = STATS_CONFIG["POOL_EXPECTATION"].get("0-2" if 0 <= n.hour <= 2 else ("5-9" if 5 <= n.hour <= 9 else "DEFAULT"))
    
    reason = f"【{target}】に需要が集中しています。統計上の搭乗率も高く、並ぶ価値は十分にあります。" if total > 0 else "現在は需要が枯渇しています。次回の波に備えて体力を温存してください。"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[TIME]]", n.strftime('%H:%M')) \
        .replace("[[P1]]", str(stands['P1'])).replace("[[P2]]", str(stands['P2'])).replace("[[P3]]", str(stands['P3'])).replace("[[P4]]", str(stands['P4'])) \
        .replace("[[H1]]", "highlight" if best_key=="P1" else "").replace("[[H2]]", "highlight" if best_key=="P2" else "") \
        .replace("[[H3]]", "highlight" if best_key=="P3" else "").replace("[[H4]]", "highlight" if best_key=="P4" else "") \
        .replace("[[TARGET]]", target).replace("[[REASON]]", reason).replace("[[POOL_WAIT]]", pool) \
        .replace("[[FLIGHT_ROWS]]", rows if rows else "<tr><td colspan='4' style='text-align:center;'>対象便なし</td></tr>") \
        .replace("[[DEBUG]]", debug).replace("[[PASS]]", str(random.randint(1000, 9999)))

    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
