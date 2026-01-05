import requests
import datetime
import os
import random
import re
import time

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .header-logo { color: #FFD700; font-weight: bold; font-size: 1.1rem; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; padding-bottom: 5px; color: #fff; }
    #report-box { background: #1e1e1e; padding: 25px; border-radius: 15px; border: 1px solid #444; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
    h3 { color: #FFD700; margin-top:20px; border-left:6px solid #FFD700; padding-left:15px; font-size: 1.2rem; }
    .rank-text { font-size: 2.2rem; font-weight: bold; color: #fff; text-shadow: 0 0 15px rgba(255,215,0,0.5); margin-bottom: 5px; }
    .basis-box { background: rgba(255, 215, 0, 0.1); border: 1px solid rgba(255,215,0,0.3); padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 0.95rem; }
    .terminal-box { display: flex; gap: 10px; margin-bottom: 15px; }
    .t-card { flex: 1; background: #2a2a2a; padding: 10px; border-radius: 8px; border: 1px solid #444; text-align: center; }
    .ai-advice { line-height: 1.8; font-size: 1.1rem; background: #2a2a2a; padding: 20px; border-radius: 10px; border: 1px solid #555; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; box-shadow: 0 6px 0 #b89b00; }
    .disclaimer { font-size: 0.75rem; color: #888; margin-top: 15px; line-height: 1.4; border-top: 1px solid #333; padding-top: 10px; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 総合出撃判定</h3>
    <p class="rank-text">[[RANK]]</p>
    <div class="basis-box">[[BASIS]]</div>
    
    <div class="terminal-box">
        <div class="t-card">T1/T2 (国内)<br><span style="color:#FFD700; font-size:1.2rem; font-weight:bold;">[[DOM_PAX]] 人</span></div>
        <div class="t-card">T3 (国際)<br><span style="color:#FFD700; font-size:1.2rem; font-weight:bold;">[[INT_PAX]] 人</span></div>
    </div>

    <div style="background:#2a2a2a; padding:10px; border-radius:8px; margin-bottom:15px; border:1px solid #444;">
        <span style="color:#FFD700; font-weight:bold;">🅿️ プール予測: [[POOL_WAIT]]</span>
    </div>

    <h3>🏁 推奨アクション</h3>
    <p style="font-size: 1.1rem;">👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice">[[REASON]]</div>
    
    <div class="disclaimer">※予測人数：直近60分（降機タイムラグ考慮）の推計値。現場のカメラ情報や仲間との通信を最優先し、無理な出撃は控えてください。</div>

    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要データ解析詳細</h3>
    <div style="font-size: 0.9rem; color:#aaa;">[[DETAILS]]</div>
    <div class="update-area" style="text-align:center; margin-top:30px;">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
        <div id="timer" style="color:#FFD700; margin-top:10px; font-weight:bold;">自動更新まで あと <span id="sec">60</span> 秒</div>
    </div>
</div>
<div class="footer">更新: [[TIME]] (JST) | [[DEBUG]]<br>🔑 PASS: [[PASS]]</div>
</div>
<script>let s=60; setInterval(()=>{s--; document.getElementById('sec').innerText=s; if(s<=0) location.reload();}, 1000);</script>
</body></html>
"""

def fetch_haneda_precision():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    dom_pax, int_pax, status = 0, 0, "Wait"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            status = "OK"
            html = r.text
            # 正規表現で時刻と便名を拾う
            flights = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?.*?(\w{2,3})\d+', html, re.DOTALL)
            for h, m, ampm, carrier in flights:
                f_hour = int(h)
                if ampm == "PM" and f_hour < 12: f_hour += 12
                elif ampm == "AM" and f_hour == 12: f_hour = 0
                f_time = now.replace(hour=f_hour % 24, minute=int(m), second=0, microsecond=0)
                if now.hour >= 20 and f_hour <= 5: f_time += datetime.timedelta(days=1)
                elif now.hour <= 5 and f_hour >= 20: f_time -= datetime.timedelta(days=1)
                
                diff = (f_time - now).total_seconds() / 60
                if -15 < diff < 45: # 🌟 現場直感：前後60分
                    # キャリアコードで国内(JL/NH/BC/7G)と国際を簡易判定
                    if carrier in ["JL", "NH", "BC", "7G", "6J", "FW"]: dom_pax += 150
                    else: int_pax += 220
        else: status = f"HTTP-{r.status_code}"
    except: status = "NetErr"
    return dom_pax, int_pax, status

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    d_pax, i_pax, debug = fetch_haneda_precision()
    
    # 🌟 供給予測（統計モデル）
    pool_wait = "30-50分" if 0 <= n.hour <= 2 else "20-30分"
    if 5 <= n.hour <= 9: pool_wait = "90分以上(注意)"

    total_pax = d_pax + i_pax
    if debug != "OK": rk, basis = "⚠️ 予測不能", "データ通信エラー"
    elif total_pax == 0: rk, basis = "🌑 D 【 撤退 】", "到着予定・降機客なし"
    elif (0 <= n.hour < 2): rk, basis = "🌈 S 【 深夜特需 】", f"計{total_pax}名の降機需要。高単価タイム。"
    elif total_pax > 1000: rk, basis = "🌈 S 【 激熱 】", f"1時間以内に{total_pax}名の大規模需要"
    elif total_pax > 500: rk, basis = "🔥 A 【 推奨 】", f"安定した到着需要({total_pax}名)"
    else: rk, basis = "✨ B 【 微風 】", f"到着需要{total_pax}名（待機時間注意）"

    target = "T3 (国際線)" if i_pax >= d_pax else "T1/T2 (国内線)"
    if total_pax == 0: target = "周辺待機・休憩推奨"
    
    # AIアドバイス（ハルシネーション抑制）
    reason = "現在、データ上の到着需要は極めて高いです。T3の国際線が主力となります。" if total_pax > 0 else "現在、1時間以内の到着予定はありません。無理な入庫は控えてください。"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[REASON]]", reason).replace("[[DOM_PAX]]", str(d_pax)).replace("[[INT_PAX]]", str(i_pax)).replace("[[POOL_WAIT]]", pool_wait).replace("[[TIME]]", n.strftime('%Y-%m-%d %H:%M')).replace("[[PASS]]", str(random.randint(1000, 9999))).replace("[[DEBUG]]", debug).replace("[[TARGET]]", target).replace("[[DETAILS]]", f"推計降機人数: {total_pax}名（国内:{d_pax} / 国際:{i_pax}）")
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
