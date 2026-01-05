import requests
import datetime
import os
import random
import re

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TRAVEL_TIME = 20 

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .header-logo { color: #FFD700; font-weight: bold; font-size: 1.1rem; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; padding-bottom: 5px; color: #fff; }
    #report-box { background: #1e1e1e; padding: 25px; border-radius: 15px; border: 1px solid #444; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
    h3 { color: #FFD700; margin-top:20px; border-left:6px solid #FFD700; padding-left:15px; font-size: 1.3rem; }
    .rank-text { font-size: 1.8rem; font-weight: bold; text-shadow: 0 0 10px rgba(255,215,0,0.3); }
    .ai-advice { line-height: 1.8; font-size: 1.1rem; color: #fff; background: #2a2a2a; padding: 20px; border-radius: 10px; border: 1px solid #555; }
    .update-area { text-align: center; margin-top: 30px; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 22px 0; width: 100%; font-size: 1.5rem; font-weight: bold; border-radius: 12px; cursor: pointer; box-shadow: 0 6px 0 #b89b00; }
    .reload-btn:active { transform: translateY(4px); box-shadow: none; }
    #timer { color: #FFD700; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #555; margin-top: 25px; text-align: right; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p class="rank-text">[[RANK]]</p>
    <div style="background:rgba(255,68,68,0.1); padding:10px; border-radius:8px; margin:15px 0; color:#ff6666; text-align:center;">[[CANCEL_BLOCK]]</div>
    <h3>🏁 推奨アクション</h3>
    <p>👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice"><strong>判定：</strong><br>[[REASON]]</div>
    <hr style="border:0; border-top:1px solid #333; margin:25px 0;">
    <h3>✈️ 需要データ詳細</h3>
    <div style="font-size: 1rem; color:#aaa;">[[DETAILS]]</div>
    <div class="update-area">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
        <div id="timer">次回自動更新まで あと <span id="sec">60</span> 秒</div>
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

def fetch_haneda_rescue():
    # 💡 404を避けるための「複数の入り口」
    t = str(int(datetime.datetime.now().timestamp()))
    urls = [
        f"https://transit.yahoo.co.jp/airport/arrival/23?v={t}",
        f"https://transit.yahoo.co.jp/airport/arrival/23/?kind=2&v={t}",
        f"https://transit.yahoo.co.jp/airport/23/arrival?v={t}"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, cancel, raw_count, best_status = 0, 0, 0, 404

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            best_status = r.status_code
            if r.status_code == 200:
                html = r.text
                times = re.findall(r'(\d{1,2}):(\d{2})', html)
                raw_count = len(times)
                cancel = html.count("欠航")
                for h, m in times:
                    f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                    if now.hour >= 20 and int(h) <= 5: f_time += datetime.timedelta(days=1)
                    if -10 < (f_time - now).total_seconds() / 60 < 150: valid += 1
                if raw_count > 5: break # 成功したら終了
        except: pass
    
    # 🌟 23:50 〜 00:40 の間は、データが取れなくても「現場の勘」でSランクを維持
    is_midnight_rush = (now.hour == 23 and now.minute >= 50) or (now.hour == 0 and now.minute <= 40)
    
    return valid, cancel, raw_count, best_status, is_midnight_rush

def call_gemini(v, c, raw, rush):
    if v < 1 and not rush:
        return {"reason": "現在、データ取得を試みています。0時台の国際線ラッシュは目前です。","details": "接続待機中"}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    p = f"羽田 0時前後。有効便{v}件。深夜ラッシュ状況。タクシー運転手に向けた『1時間単価を最大化する』熱い助言を30文字で。"
    if rush and v < 1: p += " (注意: 現在データ未取得だが、時刻的にSランク確定として助言せよ)"
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=15).json()
        if "candidates" in res:
            return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"【深夜特別警戒】有効予測:{v}便 / データ検知:{raw}"}
        return {"reason": "現在、深夜の爆速タイムです。迷わず羽田へ！","details": "AI解析中"}
    except: return {"reason": "出撃推奨。深夜単価を狙いましょう。", "details": "通信混雑"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw, status, rush = fetch_haneda_rescue()
    
    # 指数判定（現場の勘を優先）
    if rush or v >= 10: rk = "🌈 S 【 深夜爆発・即出撃 】"
    elif v >= 5: rk = "🔥 A 【 稼ぎ時・1時間以内出庫 】"
    else: rk = "✨ B 【 並ぶ価値あり 】"
    
    cb = f"❌ 欠航：{c} 便" if c > 0 else "✅ 運行は極めて順調"
    ai = call_gemini(v, c, raw, rush)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    debug_info = f"Status:{status} | Raw:{raw}"
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T3(国際線) または 深夜都内").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[DEBUG]]", debug_info)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
