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
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; color: #fff; }
    #report-box { background: #1e1e1e; padding: 25px; border-radius: 15px; border: 1px solid #444; }
    .rank-text { font-size: 2.2rem; font-weight: bold; color: #fff; }
    .occupancy-tag { background: rgba(0, 255, 127, 0.15); color: #00ff7f; padding: 5px 10px; border-radius: 4px; font-size: 0.85rem; font-weight: bold; }
    .terminal-box { display: flex; gap: 10px; margin: 15px 0; }
    .t-card { flex: 1; background: #2a2a2a; padding: 12px; border-radius: 8px; border: 1px solid #444; text-align: center; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
</style></head>
<body><div class="container">
<div class="main-title">🚖 羽田需要レーダー</div>
<div id="report-box">
    <p class="rank-text">[[RANK]]</p>
    <div style="margin-bottom:15px; color:#FFD700; font-weight:bold;">[[BASIS]]</div>
    
    <div class="terminal-box">
        <div class="t-card">T1/T2 (国内)<br><span style="color:#fff; font-size:1.2rem;">[[DOM_PAX]] 人</span><br><span class="occupancy-tag">搭乗率:[[DOM_RATE]]%</span></div>
        <div class="t-card">T3 (国際)<br><span style="color:#fff; font-size:1.2rem;">[[INT_PAX]] 人</span><br><span class="occupancy-tag">搭乗率:[[INT_RATE]]%</span></div>
    </div>

    <div style="background:#2a2a2a; padding:10px; border-radius:8px; margin-bottom:15px;">
        <span style="color:#FFD700;">🅿️ プール予測: [[POOL_WAIT]]</span>
    </div>

    <div style="background:#222; padding:15px; border-radius:10px; border-left:5px solid #FFD700;">
        <strong>推奨アクション: [[TARGET]]</strong><br>
        <span style="font-size:0.95rem;">[[REASON]]</span>
    </div>

    <div class="update-area" style="text-align:center; margin-top:30px;">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
    </div>
</div>
<div class="footer">更新: [[TIME]] | [[DEBUG]]</div>
</div></body></html>
"""

def get_load_factor(h, is_intl):
    # 🌟 プロデューサーと考える「確率」ロジック
    # 深夜(23-02)の国際線は高稼働、平日昼の国内線は中稼働
    if is_intl:
        if 22 <= h or h <= 2: return 85  # 深夜の国際線は本命
        return 70
    else:
        if 7 <= h <= 10 or 17 <= h <= 20: return 80 # 国内線通勤ラッシュ
        return 60

def fetch_haneda_stochastic():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    headers = {"User-Agent": "Mozilla/5.0"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    dom_pax, int_pax, status = 0, 0, "Wait"
    dom_rate = get_load_factor(now.hour, False)
    int_rate = get_load_factor(now.hour, True)

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            status = "OK"
            flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\d+', r.text, re.DOTALL)
            for h, m, ampm, carrier in flights:
                f_h = int(h)
                if ampm == "PM" and f_h < 12: f_h += 12
                elif ampm == "AM" and f_h == 12: f_h = 0
                f_t = now.replace(hour=f_h % 24, minute=int(m), second=0, microsecond=0)
                diff = (f_t - now).total_seconds() / 60
                
                if -15 < diff < 45: # 現場判断用（60分）
                    if carrier in ["JL", "NH", "BC", "7G", "6J"]: 
                        dom_pax += int(180 * (dom_rate / 100))
                    else: 
                        int_pax += int(250 * (int_rate / 100))
        else: status = f"HTTP-{r.status_code}"
    except: status = "NetErr"
    return dom_pax, int_pax, dom_rate, int_rate, status

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    d_pax, i_pax, d_rate, i_rate, debug = fetch_haneda_stochastic()
    
    total = d_pax + i_pax
    if total > 800: rk, basis = "🌈 S 【 激熱 】", f"推計{total}名の大規模需要"
    elif total > 400: rk, basis = "🔥 A 【 推奨 】", f"推計{total}名の安定需要"
    elif total > 0: rk, basis = "✨ B 【 注意 】", f"推計{total}名の小規模需要"
    else: rk, basis = "🌑 D 【 撤退 】", "到着予定なし"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[DOM_PAX]]", str(d_pax)).replace("[[INT_PAX]]", str(i_pax)).replace("[[DOM_RATE]]", str(d_rate)).replace("[[INT_RATE]]", str(i_rate)).replace("[[POOL_WAIT]]", "統計的に混雑中").replace("[[TIME]]", n.strftime('%H:%M')).replace("[[DEBUG]]", debug).replace("[[TARGET]]", "T3(国際線)" if i_pax > d_pax else "T1/T2(国内線)").replace("[[REASON]]", "深夜の国際線は搭乗率が高く、高単価が狙える『確率』が高いです。")
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
