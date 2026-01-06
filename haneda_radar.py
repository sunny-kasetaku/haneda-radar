import requests
import datetime
import os
import random
import re

# ==========================================================
# ⚙️ 【チューニング・パネル】 ここを書き換えるだけで調整可能
# ==========================================================
CONFIG = {
    # 🕒 時間軸の設定（現場の声に基づき -30 / +30 に変更）
    "WINDOW_PAST": -30,   # 現在から何分前まで見るか
    "WINDOW_FUTURE": 30,  # 現在から何分後まで見るか
    
    # 👥 搭乗人数・搭乗率の設定
    "CAPACITY": {"BIG": 350, "SMALL": 180, "INTL": 280},
    "LOAD_FACTORS": {"MIDNIGHT": 0.88, "RUSH": 0.82, "NORMAL": 0.65},
    
    # ✈️ 出身地による1号/2号の振り分けリスト
    "SOUTH_CITIES": ["福岡", "那覇", "伊丹", "鹿児島", "長崎", "熊本", "宮崎", "小松", "岡山", "広島", "高松", "松山", "高知"],
    "NORTH_CITIES": ["札幌", "千歳", "青森", "秋田", "山形", "三沢", "旭川", "女満別", "帯広", "釧路", "函館"]
}

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK v3.6</title>
<style>
    body { background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 10px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; }
    .rank-box { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 3px solid [[RANK_COLOR]]; text-align: center; margin-bottom: 10px; }
    .rank-main { font-size: 3.5rem; font-weight: 900; color: [[RANK_COLOR]]; margin: 0; }
    
    /* 5エリアグリッド */
    .stand-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px; }
    .stand-card { background: #222; padding: 15px; border-radius: 10px; border: 1px solid #444; text-align: center; }
    .stand-card.intl { grid-column: span 2; border-color: #FFD700; }
    .val { font-size: 1.8rem; font-weight: bold; color: #fff; display: block; }
    .label { font-size: 0.8rem; color: #aaa; }
    .best-stand { border-color: #00ff7f; background: rgba(0,255,127,0.1); }

    /* 判断基準表示（固定） */
    .criteria-badge { background: #333; color: #FFD700; padding: 5px 10px; border-radius: 5px; font-size: 0.75rem; display: inline-block; margin-bottom: 10px; }

    .advice-box { background: #222; border-left: 6px solid #FFD700; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #111; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 2px solid #333; padding: 10px; }
    .flight-list td { padding: 10px; border-bottom: 1px solid #222; }
    .update-btn { background: #FFD700; color: #000; border: none; padding: 25px; width: 100%; font-size: 1.6rem; font-weight: bold; border-radius: 15px; cursor: pointer; margin-top: 15px; }
</style></head>
<body><div class="container">
    <div style="text-align:center;">
        <span class="criteria-badge">📍 解析対象：現在時刻から [[WINDOW_INFO]] の便</span>
    </div>
    
    <div class="rank-box">
        <p class="rank-main">[[RANK]]</p>
        <p style="color:#fff; font-weight:bold; margin:5px 0;">[[RANK_MSG]]</p>
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

    <h3>✈️ 到着エビデンス (詳細)</h3>
    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
        <tbody>[[ROWS]]</tbody>
    </table>
    
    <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
    <div style="text-align:center; font-size:0.75rem; color:#555; margin-top:20px;">更新: [[TIME]] | v3.6 Tunable</div>
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
        # origin(出身地)も取得するように正規表現を調整
        flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+).*?<td>(.*?)</td>', r.text, re.DOTALL)
        
        rate = CONFIG["LOAD_FACTORS"]["NORMAL"]
        if 22 <= now.hour or now.hour <= 2: rate = CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
        elif 7 <= now.hour <= 9 or 17 <= now.hour <= 20: rate = CONFIG["LOAD_FACTORS"]["RUSH"]

        for h, m, ampm, carrier, fnum, origin in flights:
            f_h = int(h)
            if ampm == "PM" and f_h < 12: f_h += 12
            elif ampm == "AM" and f_h == 12: f_h = 0
            f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
            
            diff = (f_t - now).total_seconds() / 60
            
            # 🕒 設定されたウィンドウで判定 (-30分 〜 +30分)
            if CONFIG["WINDOW_PAST"] <= diff <= CONFIG["WINDOW_FUTURE"]:
                is_big = int(fnum) < 1000 if fnum.isdigit() else False
                cap = CONFIG["CAPACITY"]["BIG"] if is_big else CONFIG["CAPACITY"]["SMALL"]
                if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]: cap = CONFIG["CAPACITY"]["INTL"]
                
                pax = int(cap * rate)
                total_pax += pax
                
                # 🌟 精密な振り分けロジック
                s_key = "P5" # デフォルト国際
                if carrier == "JL":
                    if any(city in origin for city in CONFIG["SOUTH_CITIES"]): s_key = "P1"
                    elif any(city in origin for city in CONFIG["NORTH_CITIES"]): s_key = "P2"
                    else: s_key = "P1"
                elif carrier == "BC": s_key = "P1"
                elif carrier == "NH": s_key = "P3"
                elif carrier in ["ADO", "SNA", "SFJ", "7G"]: s_key = "P4"
                
                stands[s_key] += pax
                rows += f"<tr><td>{f_h:02d}:{m}</td><td>{carrier}{fnum}</td><td>{origin[:6]}</td><td>{pax}名</td></tr>"
    except: pass

    # ランク判定とHTML置換は維持
    rk, col, msg = ("🌑 D", "#888", "【撤退】対象なし")
    if total_pax > 800: rk, col, msg = ("🌈 S", "#FFD700", "【激熱】即出撃！")
    elif total_pax > 400: rk, col, msg = ("🔥 A", "#FF4500", "【推奨】安定需要")
    elif total_pax > 100: rk, col, msg = ("✨ B", "#00ff7f", "【注意】小規模需要")
    elif total_pax > 0: rk, col, msg = ("☁️ C", "#87CEEB", "【微妙】待機推奨")

    best_key = max(stands, key=stands.get) if total_pax > 0 else ""
    win_info = f"{abs(CONFIG['WINDOW_PAST'])}分前 〜 {CONFIG['WINDOW_FUTURE']}分後"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[RANK_COLOR]]", col).replace("[[RANK_MSG]]", msg) \
        .replace("[[WINDOW_INFO]]", win_info) \
        .replace("[[P1]]", str(stands["P1"])).replace("[[P2]]", str(stands["P2"])) \
        .replace("[[P3]]", str(stands["P3"])).replace("[[P4]]", str(stands["P4"])).replace("[[P5]]", str(stands["P5"])) \
        .replace("[[H1]]", "best-stand" if best_key=="P1" else "").replace("[[H2]]", "best-stand" if best_key=="P2" else "") \
        .replace("[[H3]]", "best-stand" if best_key=="P3" else "").replace("[[H4]]", "best-stand" if best_key=="P4" else "").replace("[[H5]]", "best-stand" if best_key=="P5" else "") \
        .replace("[[REASON]]", f"現在から30分前後の集中状況を解析。計{total_pax}名の需要予測です。").replace("[[ROWS]]", rows if rows else "<tr><td colspan='4'>対象なし</td></tr>") \
        .replace("[[TIME]]", now.strftime("%H:%M"))

    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    fetch_and_generate()
