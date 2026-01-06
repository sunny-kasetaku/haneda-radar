import requests
import datetime
import os
import random
import re

# ==========================================================
# 📊 【マスターデータ】 現場の物理制約と統計
# ==========================================================
STATS_CONFIG = {
    "AIRCRAFT_CAPACITY": {"BIG": 350, "SMALL": 180, "INTL": 280}, # 物理的な最大定員
    "LOAD_FACTORS": {"MIDNIGHT": 0.85, "RUSH": 0.80, "NORMAL": 0.60}, # 搭乗率の統計
    # 5つの乗り場への振り分け設定
    "STAND_MAP": {
        "P1": {"carriers": ["JL", "BC"], "desc": "1号 (T1南)"}, # JAL(西日本等), スカイマーク
        "P2": {"carriers": ["JL", "NU", "JTA"], "desc": "2号 (T1北)"}, # JAL(北日本等), JTA
        "P3": {"carriers": ["NH", "FW"], "desc": "3号 (T2)"}, # ANA
        "P4": {"carriers": ["ADO", "SNA", "SFJ", "7G"], "desc": "4号 (T2)"}, # エアドゥ, ソラシド等
        "P5": {"carriers": ["INTL"], "desc": "国際 (T3)"} # 国際線
    }
}

def get_realistic_pax(carrier, fnum, now_hour):
    # 大型機判定（便名が3桁以下は大型の確率が高い統計）
    is_big = False
    try:
        if int(fnum) < 1000: is_big = True
    except: pass

    # 搭乗率の決定
    rate = STATS_CONFIG["LOAD_FACTORS"]["NORMAL"]
    if 22 <= now_hour or now_hour <= 2: rate = STATS_CONFIG["LOAD_FACTORS"]["MIDNIGHT"]
    elif 7 <= now_hour <= 9 or 17 <= now_hour <= 20: rate = STATS_CONFIG["LOAD_FACTORS"]["RUSH"]

    # 物理的な上限に基づいた推計（嘘をつかない計算）
    capacity = STATS_CONFIG["AIRCRAFT_CAPACITY"]["BIG"] if is_big else STATS_CONFIG["AIRCRAFT_CAPACITY"]["SMALL"]
    if carrier not in ["JL", "NH", "BC", "7G", "6J", "ADO", "SNA", "SFJ"]:
        capacity = STATS_CONFIG["AIRCRAFT_CAPACITY"]["INTL"]

    return int(capacity * rate), "大型機" if is_big else "中小型"

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK 5-STANDS</title>
<style>
    body { background: #0f0f0f; color: #eee; font-family: sans-serif; padding: 10px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; }
    .stand-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 15px; }
    .stand-card { background: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #333; text-align: center; }
    .stand-card.intl { grid-column: span 2; background: #262626; border-color: #FFD700; }
    .best { border-color: #00ff7f; background: rgba(0,255,127,0.1); }
    .val { font-size: 1.6rem; font-weight: bold; color: #fff; display: block; }
    .label { font-size: 0.75rem; color: #888; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 15px; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 1px solid #444; padding: 5px; }
    .flight-list td { padding: 8px; border-bottom: 1px solid #222; }
    .big-bird { color: #FF4500; font-weight: bold; }
    .update-btn { background: #FFD700; color: #000; border: none; padding: 20px; width: 100%; font-size: 1.2rem; font-weight: bold; border-radius: 10px; cursor: pointer; margin-top: 10px; }
</style></head>
<body><div class="container">
    <h2 style="text-align:center; color:#FFD700; margin:10px 0;">🚖 羽田 5エリア需要レーダー</h2>
    
    <div class="stand-grid">
        <div class="stand-card [[H1]]"><span class="label">1号 (T1南)</span><span class="val">[[P1]]</span><span class="label">名</span></div>
        <div class="stand-card [[H2]]"><span class="label">2号 (T1北)</span><span class="val">[[P2]]</span><span class="label">名</span></div>
        <div class="stand-card [[H3]]"><span class="label">3号 (T2)</span><span class="val">[[P3]]</span><span class="label">名</span></div>
        <div class="stand-card [[H4]]"><span class="label">4号 (T2)</span><span class="val">[[P4]]</span><span class="label">名</span></div>
        <div class="stand-card intl [[H5]]"><span class="label">国際 (T3)</span><span class="val">[[P5]]</span><span class="label">名</span></div>
    </div>

    <div style="background:#222; padding:15px; border-radius:8px; border-left:5px solid #FFD700; margin-bottom:15px;">
        <strong>📋 解析根拠:</strong> [[REASON]]
    </div>

    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>タイプ</th><th>推計</th></tr></thead>
        <tbody>[[ROWS]]</tbody>
    </table>
    
    <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
    <div style="text-align:right; font-size:0.7rem; color:#555; margin-top:10px;">[[TIME]] | DEBUG: [[DEBUG]]</div>
</div></body></html>
"""

def fetch_and_generate():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    stands = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    rows = ""
    
    try:
        # タイムアウトを5秒に設定し「くるくる」を防止
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\s?(\d+)', r.text, re.DOTALL)
        
        for h, m, ampm, carrier, fnum in flights:
            f_h = int(h)
            if ampm == "PM" and f_h < 12: f_h += 12
            elif ampm == "AM" and f_h == 12: f_h = 0
            f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
            
            diff = (f_t - now).total_seconds() / 60
            if -10 < diff < 50: # 60分ウィンドウ
                pax, p_type = get_realistic_pax(carrier, fnum, now.hour)
                
                # 5エリアへの正確な振り分け
                s_key = "P5" # デフォルト国際
                if carrier in STATS_CONFIG["STAND_MAP"]["P1"]["carriers"]: s_key = "P1"
                elif carrier in STATS_CONFIG["STAND_MAP"]["P2"]["carriers"]: s_key = "P2"
                elif carrier in STATS_CONFIG["STAND_MAP"]["P3"]["carriers"]: s_key = "P3"
                elif carrier in STATS_CONFIG["STAND_MAP"]["P4"]["carriers"]: s_key = "P4"
                
                stands[s_key] += pax
                bird_class = "class='big-bird'" if p_type == "大型機" else ""
                rows += f"<tr><td>{f_h:02d}:{m}</td><td>{carrier}{fnum}</td><td {bird_class}>{p_type}</td><td>{pax}名</td></tr>"
        debug = "OK"
    except Exception as e:
        debug = f"Error: {str(e)}"

    # 最も人数が多いエリアを特定
    best_key = max(stands, key=stands.get) if sum(stands.values()) > 0 else ""
    reason = f"直近60分で最も期待値が高いのは【{STATS_CONFIG['STAND_MAP'].get(best_key, {'desc':'-'})['desc']}】です。機体サイズと統計搭乗率に基づき算出。"
    
    html = HTML_TEMPLATE.replace("[[P1]]", str(stands["P1"])).replace("[[P2]]", str(stands["P2"])) \
        .replace("[[P3]]", str(stands["P3"])).replace("[[P4]]", str(stands["P4"])).replace("[[P5]]", str(stands["P5"])) \
        .replace("[[H1]]", "best" if best_key=="P1" else "").replace("[[H2]]", "best" if best_key=="P2" else "") \
        .replace("[[H3]]", "best" if best_key=="P3" else "").replace("[[H4]]", "best" if best_key=="P4" else "") \
        .replace("[[H5]]", "best" if best_key=="P5" else "") \
        .replace("[[REASON]]", reason).replace("[[ROWS]]", rows if rows else "<tr><td colspan='4'>対象便なし</td></tr>") \
        .replace("[[TIME]]", now.strftime("%H:%M")).replace("[[DEBUG]]", debug)

    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    fetch_and_generate()
