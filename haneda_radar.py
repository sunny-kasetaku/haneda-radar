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
    .rank-text { font-size: 2.2rem; font-weight: bold; color: #fff; text-shadow: 0 0 15px rgba(255,215,0,0.5); }
    .ai-advice { line-height: 1.8; font-size: 1.1rem; background: #2a2a2a; padding: 20px; border-radius: 10px; border: 1px solid #555; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p class="rank-text">[[RANK]]</p>
    <div style="background:rgba(255,215,0,0.1); padding:10px; border-radius:8px; margin:15px 0; color:#FFD700; text-align:center; font-weight:bold;">✅ 国内線・国際線 統合監視モード</div>
    <h3>🏁 推奨アクション</h3>
    <p style="font-size: 1.1rem;">👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice">[[REASON]]</div>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要データ詳細（全天候型解析）</h3>
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

def fetch_haneda_perfect():
    url = "https://www.flightview.com/traveltools/FlightStatusByAirport.asp?airport=HND&at=A"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, raw_count, status = 0, 0, "Wait"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        status = str(r.status_code)
        if r.status_code == 200:
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
    except:
        status = "GlobalConnErr"
    
    return valid, raw_count, status

def call_ai(v, raw, is_morning):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    if is_morning:
        p = f"羽田 朝の国内線ラッシュ開始。有効便{v}件。国内線が主力のタクシー運転手へ向けた、今日のスタートダッシュのアドバイスを。"
    else:
        p = f"羽田 深夜1時台。国際線ラッシュ。有効便{v}件。タクシー運転手に向けた、高単価を狙う熱いアドバイスを。"
        
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"需要予測:{v}便 / データ検知:{raw}便"}
    except:
        return {"reason": "現在は羽田の稼ぎ時です！国内線・国際線ともにグローバルデータで監視中。急行しましょう！", "details": f"Raw Detect: {raw}"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, raw, debug = fetch_haneda_perfect()
    
    # 朝5時以降を「国内線主力時間」と判定
    is_morning = (5 <= n.hour < 12)
    target = "T1/T2 国内線到着" if is_morning else "T3 国際線到着"
    
    if v >= 10: rk = "🌈 S 【 爆発的需要・即出撃 】"
    elif v >= 5: rk = "🔥 A 【 安定需要・稼ぎ時 】"
    else: rk = "✨ B 【 チャンス待ち 】"
    
    ai = call_ai(v, raw, is_morning)
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[DEBUG]]", debug).replace("[[TARGET]]", target)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
