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
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
    h3 { color: #FFD700; margin-top:20px; border-left:5px solid #FFD700; padding-left:12px; font-size: 1.2rem; }
    strong { color: #FF4500; font-size: 1.2em; }
    .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.15); padding:12px; border-radius:8px; margin: 10px 0; border: 1px solid #ff4444; text-align: center; }
    .update-area { text-align: center; margin-top: 25px; background: #222; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px 0; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; transition: 0.2s; box-shadow: 0 5px 0 #b89b00; }
    .reload-btn:active { transform: translateY(3px); box-shadow: 0 2px 0 #b89b00; }
    #timer { color: #FFD700; font-size: 1rem; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #666; margin-top: 20px; text-align: right; }
    .ai-advice { line-height: 1.6; font-size: 1.05rem; color: #fff; background: #2a2a2a; padding: 15px; border-radius: 8px; border-left: 4px solid #FFD700; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田出撃指数</h3>
    <p style="font-size: 1.5rem; font-weight: bold;">[[RANK]]</p>
    <div class="cancel-info">[[CANCEL_BLOCK]]</div>
    <h3>🏁 推奨アクション</h3>
    <p>👉 <strong>[[TARGET]]</strong></p>
    <div class="ai-advice"><strong>判定（[[T_TIME]]分後到着想定）：</strong><br>[[REASON]]</div>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 需要データ詳細</h3>
    <div style="font-size: 1rem;">[[DETAILS]]</div>
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

def fetch_midnight_flights():
    # 💡 パラメータを明示した絶対アドレス
    urls = [
        "https://transit.yahoo.co.jp/airport/arrival/23/?kind=1",
        "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"
    ]
    # 🌟 一般的なWindows Chromeブラウザに完全偽装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.yahoo.co.jp/"
    }
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, cancel, raw_count, status_code = 0, 0, 0, 200

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if r.status_code != 200: status_code = r.status_code
            html = r.text
            times = re.findall(r'(\d{1,2}):(\d{2})', html)
            raw_count += len(times)
            cancel += html.count("欠航")
            
            for h, m in times:
                f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                if now.hour >= 20 and int(h) <= 5: f_time += datetime.timedelta(days=1)
                diff = (f_time - now).total_seconds() / 60
                # 💡 需要の判定範囲を広げ、20分後〜3時間後までを捕捉
                if (TRAVEL_TIME - 30) < diff < (TRAVEL_TIME + 150):
                    valid += 1
        except:
            status_code = 999
    
    # ノイズ削減（最小限）
    valid = max(0, valid - 6)
    return valid, cancel, raw_count, status_code

def call_ai(v, c, raw):
    if v < 1: return {"reason": "有効な便データが取得できていません。まもなく深夜ラッシュが反映されます。","details": f"Status: OK / Raw Detect: {raw}"}
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    p = f"羽田空港 深夜需要: 有効便{v}件。移動時間{TRAVEL_TIME}分。タクシー運転手に向けた具体的な出撃アドバイスを。1時間単価を意識して。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=20).json()
        if "candidates" in res:
            return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"到着予定: 約{v}便 / 24時台の需要が非常に高いです。"}
        return {"reason": f"現在、予測有効便は {v}件です。出撃を推奨します。","details": "AI解析中"}
    except: return {"reason": "通信混雑", "details": "再試行中"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw, status = fetch_midnight_flights()
    
    # 23時〜0時台の特別判定
    if v >= 12: rk = "🌈 S 【 爆速回転確定・即急行 】"
    elif v >= 6: rk = "🔥 A 【 1時間以内出庫・推奨 】"
    elif v >= 3: rk = "✨ B 【 並ぶ価値あり 】"
    else: rk = "⚠️ C 【 待機推奨・都内優先 】"
    
    cb = f"❌ 欠航：{c} 便" if c > 0 else "✅ 運行は極めて順調です"
    ai = call_ai(v, c, raw)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    debug_info = f"Status:{status} | Raw:{raw}"
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T3(国際線) または T2最終便").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[DEBUG]]", debug_info).replace("[[T_TIME]]", str(TRAVEL_TIME))
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
