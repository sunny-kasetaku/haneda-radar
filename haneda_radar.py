import requests
import datetime
import os
import random
import re
from bs4 import BeautifulSoup

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# 待機理論値（時間ごとの標準的な回転の良さ）
EFFICIENCY_DATA = {
    21:{"limit":60, "target":"T3(国際線)"}, 22:{"limit":45, "target":"T2付近"},
    23:{"limit":40, "target":"T1/T2"}, 0:{"limit":30, "target":"T3/都内"}
}

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK RADAR</title>
<style>
    body { background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 15px; display: flex; justify-content: center; }
    .container { max-width: 600px; width: 100%; }
    .header-logo { color: #FFD700; font-weight: bold; font-size: 1.1rem; }
    .main-title { border-bottom: 3px solid #FFD700; margin-bottom: 15px; font-size: 1.6rem; padding-bottom: 5px; color: #fff; }
    #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    h3 { color: #FFD700; margin-top:20px; border-left:5px solid #FFD700; padding-left:12px; font-size: 1.2rem; }
    strong { color: #FF4500; font-size: 1.2em; }
    .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.15); padding:12px; border-radius:8px; margin: 10px 0; border: 1px solid #ff4444; font-size: 1.1rem; text-align: center; }
    .update-area { text-align: center; margin-top: 25px; background: #222; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px 0; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 0 #b89b00; transition: 0.1s; }
    .reload-btn:active { transform: translateY(4px); box-shadow: none; }
    #timer { color: #FFD700; font-size: 1rem; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #666; margin-top: 20px; text-align: right; }
    .ai-text { line-height: 1.8; font-size: 1.05rem; }
</style></head>
<body><div class="container">
<div class="header-logo">🚖 KASETACK</div>
<div class="main-title">羽田需要レーダー</div>
<div id="report-box">
    <h3>📊 羽田指数</h3>
    <p style="font-size: 1.2rem;">[[RANK]]</p>
    <div class="cancel-info">[[CANCEL_BLOCK]]</div>
    <h3>🏁 狙うべき場所</h3>
    <p>👉 <strong>[[TARGET]]</strong></p>
    <p><strong>判定理由（時間効率重視）：</strong><br><span class="ai-text">[[REASON]]</span></p>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 供給データ詳細</h3>
    <div class="ai-text">[[DETAILS]]</div>
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

def fetch_future_flights():
    """現在から120分先までの便を抽出し、遅延便も救済する"""
    urls = ["https://transit.yahoo.co.jp/airport/arrival/23/?kind=1", "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"]
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"}
    
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    total_valid = 0
    cancel_count = 0
    delay_count = 0
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            cancel_count += r.text.count("欠航")
            
            items = soup.select('li.element, tr')
            for item in items:
                txt = item.get_text()
                # 時刻抽出
                m = re.search(r'(\d{1,2}):(\d{2})', txt)
                if m:
                    f_hour, f_min = int(m.group(1)), int(m.group(2))
                    # 簡易的に本日分として判定
                    f_time = now.replace(hour=f_hour, minute=f_min, second=0, microsecond=0)
                    
                    # 既に到着済みの判定（Yahoo!のテキストに「到着済」があれば除外）
                    if "到着済" in txt: continue
                    if "欠航" in txt: continue
                    
                    # 未来の便（今から2時間以内）をカウント
                    diff = (f_time - now).total_seconds() / 60
                    if -30 < diff < 120: # 30分前（遅延中）から120分先まで
                        total_valid += 1
                        if "遅れ" in txt or "変更" in txt: delay_count += 1
        except: pass
    return total_valid, cancel_count, delay_count

def call_gemini_efficiency(total, cancel, delay):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    # AIに「時間効率」を考えさせるプロンプト
    prompt = f"HND Update: Arrivals next 120min={total}, Cancel={cancel}, Delay={delay}. Focus on 'Time Efficiency' (Hourly rate). If wait > 60min, tell them to avoid. Format:Reason:(text)\nDetails:(bullets)"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        if "candidates" in res:
            t = res["candidates"][0]["content"]["parts"][0]["text"]
            p = t.split("Details:")
            return {"reason": p[0].replace("Reason:","").strip(), "details": p[1].strip() if len(p)>1 else "解析中"}
        return {"reason": "【システム推計】時間効率を計算中。","details": "AI制限につき、過去データから推計しています。"}
    except: return {"reason": "通信混雑", "details": "再試行中"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    valid_f, cancel, delay = fetch_future_flights()
    
    # ランク判定（単なる便数ではなく、遅延も考慮した「需要密度」で判定）
    density = valid_f + (delay * 0.5) # 遅延便は期待値として加算
    if density >= 25: rk = "🌈 S 【 爆速回転確定 】"
    elif density >= 12: rk = "🔥 A 【 1時間以内出庫 】"
    elif density >= 6: rk = "✨ B 【 効率重視ならアリ 】"
    else: rk = "⚠️ C 【 ハマる危険大 】"
    
    h = n.hour
    target = EFFICIENCY_DATA.get(h, {"target":"国際線/都内"})["target"]
    
    cb = f"❌ 欠航：{cancel} 便 / ⚠️ 遅延：{delay} 便" if (cancel + delay) > 0 else "✅ 順調な運行です"
    
    ai = call_gemini_efficiency(valid_f, cancel, delay)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", target).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
