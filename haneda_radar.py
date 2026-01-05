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
    .status-badge { background: rgba(255, 215, 0, 0.15); color: #FFD700; padding: 8px 15px; border-radius: 5px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 10px; border: 1px solid rgba(255,215,0,0.3); }
    .pool-info { background: #2a2a2a; border: 1px solid #444; padding: 15px; border-radius: 10px; margin: 15px 0; }
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
    <div class="status-badge">[[BASIS]]</div>
    
    <div class="pool-info">
        <span style="color:#FFD700; font-weight:bold;">🅿️ タクシープール予測</span><br>
        <span style="font-size:1.2rem;">[[POOL_WAIT]]</span>
    </div>

    <h3>🏁 推奨アクション</h3>
    <p style="font-size: 1.1rem;">👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice">[[REASON]]</div>
    
    <div class="disclaimer">※本情報はフライト統計と予測に基づいています。実際のプール混雑状況は、現地のカメラや目視確認、仲間の無線情報と照らし合わせ、最終的な判断はご自身で行ってください。</div>

    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要詳細（グローバル統合）</h3>
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

def fetch_haneda_full():
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

def get_pool_prediction(h):
    # 統計に基づいたプールの混雑予測（プロデューサーの知見に基づく）
    if 0 <= h <= 2: return "混雑度: 高 (推測待ち 60-90分)", 1.5
    if 5 <= h <= 9: return "混雑度: 極大 (推測待ち 90-120分)", 2.0
    return "混雑度: 中 (推測待ち 30-45分)", 1.0

def call_ai(v, raw, h, pool):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    p = f"羽田{h}時。有効{v}便。プール{pool}。タクシー運転手に、需要とプールの混雑を天秤にかけた出撃判断を30文字で。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except: return "需要と供給のバランスに注意。プール情報と合わせて最終判断を。"

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, raw, debug = fetch_haneda_full()
    
    pool_text, pool_factor = get_pool_prediction(n.hour)
    
    # ロジックの再構築
    if debug != "OK": rk, basis = "⚠️ 判定不能", "データ取得エラー"
    elif v == 0: rk, basis = "🌑 D 【 撤退推奨 】", "到着予定便なし"
    elif (0 <= n.hour < 2) and v > 0:
        rk = "🌈 S 【 爆発的需要 】"
        basis = "深夜単価＋高利用率（1便以上捕捉）"
    elif (v / pool_factor) >= 8: rk, basis = "🔥 A 【 安定需要 】", f"高回転期待（{v}便検知）"
    else: rk, basis = "✨ B 【 チャンス待ち 】", "需要・供給バランスを注視"
    
    target = "T1/T2 国内線" if 5 <= n.hour < 12 else "T3 国際線"
    ai_reason = call_ai(v, raw, n.hour, pool_text)
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[BASIS]]", basis).replace("[[REASON]]", ai_reason).replace("[[DETAILS]]", f"直近需要:{v}便 / 全検知:{raw}便").replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[DEBUG]]", debug).replace("[[TARGET]]", target).replace("[[POOL_WAIT]]", pool_text)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
