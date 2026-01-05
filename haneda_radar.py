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
    .rank-basis { background: rgba(255, 215, 0, 0.15); color: #FFD700; padding: 8px 15px; border-radius: 5px; font-size: 0.9rem; font-weight: bold; display: inline-block; margin-bottom: 15px; }
    .ai-advice { line-height: 1.8; font-size: 1.1rem; background: #2a2a2a; padding: 20px; border-radius: 10px; border: 1px solid #555; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; box-shadow: 0 6px 0 #b89b00; transition: 0.1s; }
    .reload-btn:active { transform: translateY(4px); box-shadow: none; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p class="rank-text">[[RANK]]</p>
    <div class="rank-basis">[[BASIS]]</div>
    <h3>🏁 推奨アクション</h3>
    <p style="font-size: 1.1rem;">👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice">[[REASON]]</div>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要データ詳細（全天候型・統合解析）</h3>
    <div style="font-size: 0.95rem; color:#aaa;">[[DETAILS]]</div>
    <div class="update-area" style="text-align:center; margin-top:30px;">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
        <div id="timer" style="color:#FFD700; margin-top:10px; font-weight:bold;">自動更新まで あと <span id="sec">60</span> 秒</div>
    </div>
</div>
<div class="footer">更新: [[TIME]] (JST) | [[DEBUG]]<br>🔑 PASS: [[PASS]]</div>
</div>
<script>
    let s = 60;
    setInterval(() => { s--; document.getElementById('sec').innerText = s; if(s <= 0) location.reload(); }, 1000);
</script>
</body></html>
"""

def fetch_haneda_optimized():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    valid, raw_count, status = 0, 0, "Wait"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            status = "OK"
            html = r.text
            times = re.findall(r'(\d{1,2}):(\d{2})\s?([AP]M)?', html)
            raw_count = len(times)
            for h, m, ampm in times:
                f_hour = int(h)
                if ampm == "PM" and f_hour < 12: f_hour += 12
                elif ampm == "AM" and f_hour == 12: f_hour = 0
                f_time = now.replace(hour=f_hour % 24, minute=int(m), second=0, microsecond=0)
                if now.hour >= 20 and f_hour <= 5: f_time += datetime.timedelta(days=1)
                elif now.hour <= 5 and f_hour >= 20: f_time -= datetime.timedelta(days=1)
                diff = (f_time - now).total_seconds() / 60
                if -15 < diff < 180: valid += 1
        else: status = f"HTTP-{r.status_code}"
    except: status = "NetErr"
    return valid, raw_count, status

def call_ai(v, raw, h):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    p = f"羽田{h}時台。有効{v}件。総{raw}件。タクシー運転手に向けた、国内線と国際線の動向を踏まえたアドバイスを30文字で。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"【直近需要】:{v}便 / 【全検知（国内含）】:{raw}便"}
    except: return {"reason": "現在は羽田の稼ぎ時です！T3を中心に、朝の国内線ラッシュも視野に入れて。","details": f"Raw Detect: {raw}"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, raw, debug = fetch_haneda_optimized()
    
    # 判定根拠のロジック
    basis = "現在の便数に基づく通常判定"
    if (0 <= n.hour < 2):
        rk = "🌈 S 【 爆発的需要・即出撃 】"
        basis = "判定根拠：深夜帯の単価上昇およびタクシー利用率の極端な高まり"
    elif v >= 10:
        rk = "🌈 S 【 爆発的需要・即出撃 】"
        basis = f"判定根拠：直近3時間以内に{v}便の到着を検知（高需要）"
    elif v >= 5:
        rk = "🔥 A 【 安定需要・稼ぎ時 】"
        basis = f"判定根拠：直近3時間以内に{v}便の到着を検知"
    else:
        rk = "✨ B 【 チャンス待ち 】"
        basis = "判定根拠：直近の到着便が少数（予備データ監視中）"
    
    target = "T1/T2 国内線到着" if 5 <= n.hour < 12 else "T3 国際線到着"
    ai = call_ai(v, raw, n.hour)
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[DEBUG]]", debug).replace("[[TARGET]]", target)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
