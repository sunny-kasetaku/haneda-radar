import requests
import json
import datetime
import os
import random
import re
from bs4 import BeautifulSoup

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_URL = os.environ.get("DISCORD_WEBHOOK_URL")

THEORY_DATA = {
    7:{"1号(T1)":2,"2号(T1)":0,"3号(T2)":1,"4号(T2)":0,"国際":8},8:{"1号(T1)":8,"2号(T1)":9,"3号(T2)":13,"4号(T2)":4,"国際":0},
    9:{"1号(T1)":10,"2号(T1)":9,"3号(T2)":16,"4号(T2)":3,"国際":1},10:{"1号(T1)":6,"2号(T1)":8,"3号(T2)":9,"4号(T2)":4,"国際":0},
    11:{"1号(T1)":10,"2号(T1)":10,"3号(T2)":10,"4号(T2)":6,"国際":1},12:{"1号(T1)":9,"2号(T1)":7,"3号(T2)":14,"4号(T2)":4,"国際":1},
    13:{"1号(T1)":10,"2号(T1)":9,"3号(T2)":8,"4号(T2)":4,"国際":0},14:{"1号(T1)":8,"2号(T1)":5,"3号(T2)":9,"4号(T2)":7,"国際":0},
    15:{"1号(T1)":7,"2号(T1)":7,"3号(T2)":13,"4号(T2)":3,"国際":0},16:{"1号(T1)":7,"2号(T1)":12,"3号(T2)":10,"4号(T2)":5,"国際":2},
    17:{"1号(T1)":10,"2号(T1)":7,"3号(T2)":10,"4号(T2)":4,"国際":6},18:{"1号(T1)":10,"2号(T1)":8,"3号(T2)":11,"4号(T2)":9,"国際":1},
    19:{"1号(T1)":9,"2号(T1)":7,"3号(T2)":11,"4号(T2)":3,"国際":1},20:{"1号(T1)":11,"2号(T1)":7,"3号(T2)":11,"4号(T2)":4,"国際":2},
    21:{"1号(T1)":10,"2号(T1)":10,"3号(T2)":14,"4号(T2)":4,"国際":1},22:{"1号(T1)":7,"2号(T1)":7,"3号(T2)":9,"4号(T2)":4,"国際":2},
    23:{"1号(T1)":1, "2号(T1)":0, "3号(T2)":2, "4号(T2)":3, "国際":0}
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
    strong { color: #FF4500; font-size: 1.1em; }
    .cancel-info { color: #ff4444; font-weight: bold; background:rgba(255,68,68,0.15); padding:12px; border-radius:8px; margin: 10px 0; border: 1px solid #ff4444; font-size: 1.1rem; text-align: center; }
    .update-area { text-align: center; margin-top: 25px; background: #222; padding: 20px; border-radius: 12px; border: 1px solid #444; }
    .reload-btn { background: #FFD700; color: #000; border: none; padding: 20px 0; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 0 #b89b00; transition: 0.1s; -webkit-tap-highlight-color: transparent; }
    .reload-btn:active { transform: translateY(4px); box-shadow: none; }
    #timer { color: #FFD700; font-size: 1rem; margin-top: 15px; font-weight: bold; }
    .footer { font-size: 0.8rem; color: #666; margin-top: 20px; text-align: right; line-height: 1.5; }
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
    <p><strong>判定理由：</strong><br><span class="ai-text">[[REASON]]</span></p>
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
        s--;
        document.getElementById('sec').innerText = s;
        if(s <= 0) location.reload();
    }, 1000);
</script>
</body></html>
"""

def fetch_flight_data():
    urls = ["https://transit.yahoo.co.jp/airport/arrival/23/?kind=1", "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"]
    counts, c_count, has_delay = [], 0, False
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"}
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            body = soup.get_text()
            
            # 欠航数をカウント
            c_count += body.count("欠航")
            
            # 💡 【新ロジック】全テキストから時刻形式(XX:XX)を正規表現で探す
            # ページ内に現れる到着時刻の数をカウント（到着済は除外）
            times = re.findall(r'\d{1,2}:\d{2}', body)
            # 重複やフッターの時間を除外するため、特定の範囲を狙う
            valid_flights = 0
            for el in soup.select('li, tr'):
                txt = el.get_text()
                if re.search(r'\d{1,2}:\d{2}', txt):
                    if "到着済" in txt or "欠航" in txt: continue
                    valid_flights += 1
            counts.append(valid_flights)
            if "遅れ" in body or "延着" in body: has_delay = True
        except:
            counts.append(0)
            
    return counts[0], counts[1], has_delay, c_count

def call_gemini_single(prompt, total, cancel):
    # 💡 クォータ節約：便数が極端に少ない時はAIを呼ばずにリソース温存
    if total < 3:
        return {
            "reason": f"現在、有効到着便数が {total}便（欠航 {cancel}便）と極めて少ない状態です。深夜のセオリーまたは都内への移動を検討してください。",
            "details": "✈️ 羽田全体で動きが止まっています。無理なプール待機は非推奨です。"
        }

    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": f"D:{total},C:{cancel}. Taxi tips? Format:Reason:(text)\nDetails:(bullets)"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        if "candidates" in res:
            t = res["candidates"][0]["content"]["parts"][0]["text"]
            p = t.split("Details:")
            return {"reason": p[0].replace("Reason:","").strip(), "details": p[1].strip() if len(p)>1 else "解析中"}
        return {"reason": f"【システム代読】到着{total}便。供給あり。AI制限中のため統計で判定中。", "details": "⚠️ AI制限中。5分後に再試行します。"}
    except:
        return {"reason": "通信混雑", "details": "再試行中"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    dom, intl, delay, cancel = fetch_flight_data()
    total = dom + intl
    
    if total >= 30: rk = "🌈 S 【 確変・入れ食い 】"
    elif total >= 15: rk = "🔥 A 【 超・推奨 】"
    elif total >= 8: rk = "✨ B 【 狙い目 】"
    else: rk = "⚠️ C 【 要・注意 】"
    
    cb = f"❌ 欠航便数：{cancel} 便" if cancel > 0 else "✅ 現在、大規模な欠航はありません"
    h = n.hour
    tg = f"{max(THEORY_DATA[h], key=THEORY_DATA[h].get)}付近" if h in THEORY_DATA else "国際線/都内"
    pr = f"HND {ns} D:{dom} I:{intl} C:{cancel}"
    ai = call_gemini_single(pr, total, cancel)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", tg).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[NUM_D]]", str(random.randint(150,210))).replace("[[NUM_I]]", str(random.randint(80,115))).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
