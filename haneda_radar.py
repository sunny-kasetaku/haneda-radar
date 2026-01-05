import requests
import datetime
import os
import random
import re
import time

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TRAVEL_TIME = 20 

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .header-logo { color: #FFD700; font-weight: bold; font-size: 1.1rem; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; padding-bottom: 5px; color: #fff; }
    #report-box { background: #1e1e1e; padding: 25px; border-radius: 15px; border: 1px solid #444; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
    h3 { color: #FFD700; margin-top:20px; border-left:6px solid #FFD700; padding-left:15px; font-size: 1.3rem; }
    .rank-text { font-size: 2rem; font-weight: bold; color: #fff; text-shadow: 0 0 15px rgba(255,215,0,0.5); }
    .ai-advice { line-height: 1.8; font-size: 1.1rem; color: #fff; background: #2a2a2a; padding: 20px; border-radius: 10px; border: 1px solid #555; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p class="rank-text">[[RANK]]</p>
    <div style="background:rgba(255,215,0,0.1); padding:10px; border-radius:8px; margin:15px 0; color:#FFD700; text-align:center; font-weight:bold;">[[CANCEL_BLOCK]]</div>
    <h3>🏁 推奨アクション</h3>
    <p style="font-size: 1.1rem;">👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice">[[REASON]]</div>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要データ詳細（国内＋国際 統合解析）</h3>
    <div style="font-size: 0.95rem; color:#aaa;">[[DETAILS]]</div>
    <div class="update-area" style="text-align:center; margin-top:30px;">
        <button class="reload-btn" style="background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer;" onclick="location.reload()">最新情報に更新</button>
        <div id="timer" style="color:#FFD700; margin-top:15px; font-weight:bold;">次回自動更新まで あと <span id="sec">60</span> 秒</div>
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

def fetch_haneda_stealth_v2():
    # 💡 ページ構成が安定しているフライトタブへ
    urls = [
        "https://flights.yahoo.co.jp/airport/HND/arrival?kind=1",
        "https://flights.yahoo.co.jp/airport/HND/arrival?kind=2"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    }
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, cancel, raw_count, status_log = 0, 0, 0, []

    # セッションを開始して人間らしさを出す
    session = requests.Session()
    session.headers.update(headers)

    for url in urls:
        try:
            r = session.get(url, timeout=15)
            status_log.append(str(r.status_code))
            if r.status_code == 200:
                html = r.text
                times = re.findall(r'(\d{1,2}):(\d{2})', html)
                raw_count += len(times)
                cancel += html.count("欠航") + html.count("Cancelled")
                for h, m in times:
                    f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                    if now.hour >= 20 and int(h) <= 5: f_time += datetime.timedelta(days=1)
                    diff = (f_time - now).total_seconds() / 60
                    if -10 < diff < 150: valid += 1
            # 連続アクセスを避けるための小さな休憩
            time.sleep(1)
        except:
            status_log.append("ConnErr")
    
    is_prime = (now.hour == 0)
    return valid, cancel, raw_count, "/".join(status_log), is_prime

def call_ai(v, c, raw, prime):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    p = f"羽田 0時台。国内線最終の残り客と国際線深夜ラッシュ。有効便{v}件。タクシー運転手に向けた具体的な『稼ぎのコツ』を30文字で。"
    if prime: p += " (注意: 通信が不安定だが0時台の需要は確定。熱く励まして)"
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"国内＋国際統合解析: 有効{v}便 / 検知{raw}"}
    except:
        return {"reason": "0時台はT3(国際線)が主役。国内線遅延客も狙えるボーナスタイムです！", "details": f"データ検知{raw}"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw, debug, prime = fetch_haneda_stealth_v2()
    
    if prime or v >= 10: rk = "🌈 S 【 深夜爆発・国内国際統合 】"
    elif v >= 5: rk = "🔥 A 【 稼ぎ時・即出撃 】"
    else: rk = "✨ B 【 粘り目 】"
    
    cb = "✅ 運行は順調です" if c == 0 else f"❌ {c}件に欠航/遅延あり"
    ai = call_ai(v, c, raw, prime)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T3(国際線) または T2国内線最終").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[DEBUG]]", debug)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
