import requests
import datetime
import os
import random
import re

# ==========================================================
# 📊 【設定定数】 ロジックの心臓部
# ==========================================================
STATS_CONFIG = {
    "AIRCRAFT_CAPACITY": {"BIG": 350, "SMALL": 180, "INTL": 280},
    "LOAD_FACTORS": {"MIDNIGHT": 0.88, "RUSH": 0.82, "NORMAL": 0.65},
    "STAND_MAP": {
        "P1": ["JL_SOUTH", "BC"], "P2": ["JL_NORTH", "NU", "JTA"],
        "P3": ["NH"], "P4": ["ADO", "SNA", "SFJ", "7G", "FW"], "P5": ["INTL"]
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK FINAL UI</title>
<style>
    body { background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 10px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; }
    
    /* 総合判定ランク */
    .rank-box { background: #1a1a1a; padding: 25px; border-radius: 15px; border: 3px solid [[RANK_COLOR]]; text-align: center; margin-bottom: 15px; }
    .rank-main { font-size: 3.8rem; font-weight: 900; color: [[RANK_COLOR]]; margin: 0; }
    .rank-desc { font-size: 1.1rem; font-weight: bold; margin-top: 5px; color: #fff; }

    /* 5エリアグリッド */
    .stand-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px; }
    .stand-card { background: #222; padding: 15px; border-radius: 10px; border: 1px solid #444; text-align: center; }
    .stand-card.intl { grid-column: span 2; border-color: #FFD700; }
    .val { font-size: 1.8rem; font-weight: bold; color: #fff; display: block; }
    .label { font-size: 0.8rem; color: #aaa; }
    .best-stand { border-color: #00ff7f; background: rgba(0,255,127,0.1); }

    /* 判例 (Legend) */
    .legend { background: #151515; padding: 10px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-bottom: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }

    .advice-box { background: #222; border-left: 6px solid #FFD700; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 0.95rem; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #111; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 2px solid #333; padding: 10px; }
    .flight-list td { padding: 10px; border-bottom: 1px solid #222; }

    .update-btn { background: #FFD700; color: #000; border: none; padding: 25px; width: 100%; font-size: 1.6rem; font-weight: bold; border-radius: 15px; cursor: pointer; margin-top: 15px; box-shadow: 0 5px 0 #b89b00; }
</style></head>
<body><div class="container">
    <h2 style="text-align:center; color:#FFD700; margin:10px 0;">🚖 KASETACK 羽田需要攻略</h2>
    
    <div class="rank-box">
        <p class="rank-main">[[RANK]]</p>
        <p class="rank-desc">[[RANK_MSG]]</p>
    </div>

    <div class="legend">
        <span>🌈S: 激熱(800人~)</span><span>🔥A: 推奨(400人~)</span><span>✨B: 注意(100人~)</span>
        <span>☁️C: 微妙(1人~)</span><span>🌑D: 撤退(到着なし)</span>
    </div>

    <div class="stand-grid">
        <div class="stand-card [[H1]]"><span class="label">1号 (T1南)</span><span class="val">[[P1]]人</span></div>
        <div class="stand-card [[H2]]"><span class="label">2号 (T1北)</span><span class="val">[[P2]]人</span></div>
        <div class="stand-card [[H3]]"><span class="label">3号 (T2)</span><span class="val">[[P3]]人</span></div>
        <div class="stand-card [[H4]]"><span class="label">4号 (T2)</span><span class="val">[[P4]]人</span></div>
        <div class="stand-card intl [[H5]]"><span class="label">国際 (T3)</span><span class="val">[[P5]]人</span></div>
    </div>

    <div class="advice-box">
        <strong>⚡ 根拠・戦術：</strong><br>[[REASON]]
    </div>

    <h3>✈️ 到着エビデンス (直近60分)</h3>
    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>タイプ</th><th>推計</th></tr></thead>
        <tbody>[[ROWS]]</tbody>
    </table>
    
    <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
    <div style="text-align:center; font-size:0.75rem; color:#555; margin-top:20px;">更新: [[TIME]] | v3.5 FIXED UI</div>
</div></body></html>
"""

def fetch_and_generate():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    rows = ""
    total_pax = 0

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+)', r.text, re.DOTALL)
        
        # 搭乗率
        rate = STATS_CONFIG["LOAD_FACTORS"]["NORMAL"]
        if 22 <= now.hour or now.hour <= 2: rate = STATS_CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
        elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = STATS_CONFIG["LOAD_FACTORS"]["RUSH"]

        for h, m, ampm, carrier, fnum in flights:
            f_h = int(h)
            if ampm == "PM" and f_h < 12: f_h += 12
            elif ampm == "AM" and f_h == 12: f_h = 0
            f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
            
            diff = (f_t - now).total_seconds() / 60
            if -10 < diff < 50:
                is_big = int(fnum) < 1000 if fnum.isdigit() else False
                cap = STATS_CONFIG["AIRCRAFT_CAPACITY"]["BIG"] if is_big else STATS_CONFIG["AIRCRAFT_CAPACITY"]["SMALL"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]: cap = STATS_CONFIG["AIRCRAFT_CAPACITY"]["INTL"]
                
                pax = int(cap * rate)
                total_pax += pax
                
                # 暫定振り分け (後でJAL詳細ロジック追加)
                s_key = "P5"
                if carrier == "JL": s_key = "P1" # とりあえずP1
                elif carrier == "NH": s_key = "P3"
                elif carrier in ["BC"]: s_key = "P1"
                elif carrier in ["ADO", "SNA", "SFJ", "7G"]: s_key = "P4"
                
                stands[s_key] += pax
                rows += f"<tr><td>{f_h:02d}:{m}</td><td>{carrier}{fnum}</td><td>{'大型' if is_big else '普通'}</td><td>{pax}名</td></tr>"
    except: pass

    # ランク判定
    if total_pax > 800: rk, col, msg = "🌈 S", "#FFD700", "【激熱】出撃推奨！大波が来ています。"
    elif total_pax > 400: rk, col, msg = "🔥 A", "#FF4500", "【推奨】安定需要。入庫を検討してください。"
    elif total_pax > 100: rk, col, msg = "✨ B", "#00ff7f", "【注意】小規模需要あり。効率を重視。"
    elif total_pax > 0: rk, col, msg = "☁️ C", "#87CEEB", "【微妙】需要少なめ。周辺待機を推奨。"
    else: rk, col, msg = "🌑 D", "#888", "【撤退】対象便なし。無理は禁物です。"

    best_key = max(stands, key=stands.get) if total_pax > 0 else ""
    target_names = {"P1":"1号(T1南)","P2":"2号(T1北)","P3":"3号(T2)","P4":"4号(T2)","P5":"国際(T3)"}
    reason = f"直近60分の推計降機人数は計 {total_pax} 名です。特に【{target_names.get(best_key, 'なし')}】への需要が集中しています。"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[RANK_COLOR]]", col).replace("[[RANK_MSG]]", msg) \
        .replace("[[P1]]", str(stands["P1"])).replace("[[P2]]", str(stands["P2"])).replace("[[P3]]", str(stands["P3"])).replace("[[P4]]", str(stands["P4"])).replace("[[P5]]", str(stands["P5"])) \
        .replace("[[H1]]", "best-stand" if best_key=="P1" else "").replace("[[H2]]", "best-stand" if best_key=="P2" else "") \
        .replace("[[H3]]", "best-stand" if best_key=="P3" else "").replace("[[H4]]", "best-stand" if best_key=="P4" else "").replace("[[H5]]", "best-stand" if best_key=="P5" else "") \
        .replace("[[REASON]]", reason).replace("[[ROWS]]", rows if rows else "<tr><td colspan='4'>到着予定なし</td></tr>") \
        .replace("[[TIME]]", now.strftime("%H:%M"))

    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    fetch_and_generate()
