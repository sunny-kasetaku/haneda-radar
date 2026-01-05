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
    <h3>✈️ 需要データ詳細（統合解析）</h3>
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

def fetch_haneda_ultimate():
    # 💡 3つの異なるドメイン/パスを試す
    urls = [
        "https://flights.yahoo.co.jp/airport/HND/arrival",
        "https://transit.yahoo.co.jp/airport/23/arrival",
        "https://transit.yahoo.co.jp/airport/arrival/23/"
    ]
    # 🌟 日本のiPhone/Safariに完全偽装
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-jp"
    }
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, cancel, raw_count, last_status = 0, 0, 0, "Wait"

    for url in urls:
        try:
            # 接続リトライを含めた粘り強いリクエスト
            r = requests.get(url, headers=headers, timeout=10)
            last_status = str(r.status_code)
            if r.status_code == 200:
                html = r.text
                times = re.findall(r'(\d{1,2}):(\d{2})', html)
                raw_count = len(times)
                cancel = html.count("欠航") + html.count("Cancelled")
                for h, m in times:
                    f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                    if now.hour >= 20 and int(h) <= 5: f_time += datetime.timedelta(days=1)
                    if -10 < (f_time - now).total_seconds() / 60 < 150: valid += 1
                if raw_count > 0: break # 1つでも取れたら終了
            time.sleep(1) # 相手を驚かせないよう少し待つ
        except:
            last_status = "ConnErr"
    
    # 深夜特別判定（データが取れなくても、プロデューサーの勘でSランクを出す）
    is_prime = (now.hour == 0)
    return valid, cancel, raw_count, last_status, is_prime

def call_ai(v, c, raw, prime):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    p = f"羽田 0時台。深夜ラッシュ。有効便{v}件。タクシー運転手に向けた具体的な『稼ぎの極意』を。"
    if prime and v == 0:
        p += " (注意: ネット接続エラーで数字は0だが、実際は深夜ラッシュで稼げる時間。その前提で鼓舞せよ)"
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"需要予測: {v}便 / データ検知: {raw}"}
    except:
        return {"reason": "0時台はT3(国際線)が黄金郷。データ不通を跳ね除ける勢いで急行しましょう！", "details": f"Raw Detect: {raw}"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw, debug, prime = fetch_haneda_ultimate()
    
    # 0時台は無条件でSランクを表示
    if prime or v >= 10: rk = "🌈 S 【 深夜爆発・出撃一択 】"
    elif v >= 5: rk = "🔥 A 【 稼ぎ時・急行推奨 】"
    else: rk = "✨ B 【 チャンスあり 】"
    
    cb = "✅ 運行は極めて順調です" if c == 0 else f"❌ {c}件に欠航/遅延あり"
    ai = call_ai(v, c, raw, prime)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T3(国際線) > T2国内最終").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[DEBUG]]", debug)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
