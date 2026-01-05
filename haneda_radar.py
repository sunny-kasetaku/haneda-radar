import requests
import datetime
import os
import random
import re

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TRAVEL_TIME = 20 # 羽田への移動時間（分）

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .header-logo { color: #FFD700; font-weight: bold; font-size: 1.1rem; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; padding-bottom: 5px; color: #fff; }
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }
    h3 { color: #FFD700; margin-top:20px; border-left:5px solid #FFD700; padding-left:12px; font-size: 1.2rem; }
    strong { color: #FF4500; font-size: 1.1em; }
    .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.15); padding:12px; border-radius:8px; margin: 10px 0; border: 1px solid #ff4444; text-align: center; }
    .update-area { text-align: center; margin-top: 25px; background: #222; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px 0; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; }
    #timer { color: #FFD700; font-size: 1rem; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #666; margin-top: 20px; text-align: right; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p style="font-size: 1.2rem;">[[RANK]]</p>
    <div class="cancel-info">[[CANCEL_BLOCK]]</div>
    <h3>🏁 推奨アクション</h3>
    <p>👉 <strong>[[TARGET]]</strong></p>
    <p><strong>判定理由：</strong><br>[[REASON]]</p>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 供給データ詳細</h3>
    <div>[[DETAILS]]</div>
    <div class="update-area">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
        <div id="timer">次回自動更新まで あと <span id="sec">60</span> 秒</div>
    </div>
</div>
<div class="footer">更新: [[TIME]] (JST) <br>🔑 PASS: [[PASS]]</div>
</div>
<script>
    let s = 60;
    setInterval(() => {
        s--; document.getElementById('sec').innerText = s;
        if(s <= 0) location.reload();
    }, 1000);
</script>
</body></html>
"""

def fetch_debug_flights():
    urls = ["https://transit.yahoo.co.jp/airport/arrival/23/?kind=1", "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"]
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    raw_time_count = 0
    valid_count = 0
    c_count = 0
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = "utf-8"
            html = r.text
            c_count += html.count("欠航")
            times = re.findall(r'(\d{1,2}):(\d{2})', html)
            raw_time_count += len(times)
            
            for h, m in times:
                f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                if now.hour >= 21 and int(h) <= 4: f_time += datetime.timedelta(days=1)
                diff = (f_time - now).total_seconds() / 60
                
                # 💡 判定を緩める：今から120分先まで全部数える
                if -10 < diff < 120:
                    valid_count += 1
        except: pass
    return valid_count, c_count, raw_time_count

def call_ai(v, c, raw):
    if v < 1: return {"reason": f"現在、データ上の有効便数は0件です（解析対象数:{raw}）。Yahoo!側のリストが更新されるまで待機を。","details": f"検出された全時刻数: {raw} / 欠航: {c}"}
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    p = f"羽田: 有効便{v}件(全検知{raw}, 欠航{c})。タクシー運転手に簡潔な助言を。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=20).json()
        if "candidates" in res:
            return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"生データ検知: {raw}件 / 有効判定: {v}件"}
        return {"reason": "AI制限中。数値から判断してください。","details": f"検知数: {raw}"}
    except: return {"reason": "通信エラー", "details": "再試行"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw = fetch_debug_flights()
    
    if v >= 10: rk = "🔥 A 【 稼ぎ時 】"
    elif v >= 4: rk = "✨ B 【 狙い目 】"
    else: rk = "⚠️ C 【 ハマる危険 】"
    
    cb = f"❌ 欠航：{c} 便" if c > 0 else "✅ 順調な運行"
    ai = call_ai(v, c, raw)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T3または都内").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb)
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
