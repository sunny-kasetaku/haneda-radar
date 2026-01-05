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
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }
    h3 { color: #FFD700; margin-top:20px; border-left:5px solid #FFD700; padding-left:12px; font-size: 1.2rem; }
    strong { color: #FF4500; font-size: 1.1em; }
    .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.15); padding:12px; border-radius:8px; margin: 10px 0; border: 1px solid #ff4444; text-align: center; }
    .update-area { text-align: center; margin-top: 25px; background: #222; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px 0; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; }
    #timer { color: #FFD700; font-size: 1rem; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #666; margin-top: 20px; text-align: right; }
    .debug-text { color: #555; font-size: 0.7rem; margin-top: 10px; }
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
<div class="footer">更新: [[TIME]] (JST) | [[DEBUG]]<br>🔑 PASS: [[PASS]]</div>
</div>
<script>
    let s = 60;
    setInterval(() => { s--; document.getElementById('sec').innerText = s; if(s <= 0) location.reload(); }, 1000);
</script>
</body></html>
"""

def fetch_stealth_flights():
    # 💡 スマホ版URLに変更
    urls = ["https://transit.yahoo.co.jp/airport/23/arrival?kind=1", "https://transit.yahoo.co.jp/airport/23/arrival?kind=2"]
    # 🌟 より人間らしいヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Referer": "https://www.google.com/"
    }
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    valid, cancel, raw_count = 0, 0, 0
    status_code = 0

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            status_code = r.status_code
            html = r.text
            times = re.findall(r'(\d{1,2}):(\d{2})', html)
            raw_count += len(times)
            cancel += html.count("欠航")
            
            for h, m in times:
                f_time = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                if now.hour >= 20 and int(h) <= 5: f_time += datetime.timedelta(days=1)
                diff = (f_time - now).total_seconds() / 60
                # 💡 判定を21:00〜23:59など広い範囲に広げる
                if -20 < diff < 150:
                    valid += 1
        except: pass
    
    # 解析対象が多すぎる（フッターの時刻など）場合は調整
    valid = max(0, valid - 6) 
    return valid, cancel, raw_count, status_code

def call_ai(v, c, raw):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    # AIへの指示をさらに具体的に
    p = f"羽田空港: 有効便{v}件(検知{raw}, 欠航{c})。22時台の遅延状況を考慮し、タクシー運転手に『今から向かうべきか』アドバイスして。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=20).json()
        if "candidates" in res:
            return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"予測有効便: {v}便 / データ検知数: {raw}"}
        return {"reason": f"現在、解析対象数は{raw}です。移動時間20分を考慮中。","details": f"AI制限中(有効:{v}/検知:{raw})"}
    except: return {"reason": "通信エラー", "details": "再試行"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    v, c, raw, status = fetch_stealth_flights()
    
    if v >= 8: rk = "🔥 A 【 今すぐ出撃 】"
    elif v >= 3: rk = "✨ B 【 狙い目 】"
    else: rk = "⚠️ C 【 待機推奨 】"
    
    cb = f"❌ 欠航：{c} 便" if c > 0 else "✅ 運行は順調です"
    ai = call_ai(v, c, raw)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    debug_info = f"Status:{status} | Raw:{raw}"
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", "T2(国内線)またはT3").replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[DEBUG]]", debug_info)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
