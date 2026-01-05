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
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"}
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # ページ内テキストを直接スキャン（より確実に拾う）
            body_text = soup.get_text()
            c_count += body_text.count("欠航")
            
            v = 0
            items = soup.find_all(['li', 'tr'], class_=lambda x: x and ('element' in x or 'arrival' in x))
            if not items: # セレクタが効かない場合のフォールバック
                items = soup.select('div.alst li')

            for item in items:
                t = item.get_text()
                if "到着済" in t: continue
                if "欠航" in t: continue # ここでは欠航以外をカウント
                # 時刻が含まれているかチェック
                if re.search(r'\d{1,2}:\d{2}', t):
                    if any(k in t for k in ["遅れ", "変更", "延着"]): has_delay = True
                    v += 1
            counts.append(v)
        except:
            counts.append(-1) # エラー時は-1
            
    dom = counts[0] if len(counts) > 0 else -1
    intl = counts[1] if len(counts) > 1 else -1
    return dom, intl, has_delay, c_count

def call_gemini_single(prompt, total, cancel):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    # 極限まで短縮したプロンプト
    payload = {"contents": [{"parts": [{"text": f"D:{total},C:{cancel}. Tips for taxi? Format:Reason:(text)\nDetails:(bullets)"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        if "candidates" in res:
            t = res["candidates"][0]["content"]["parts"][0]["text"]
            p = t.split("Details:")
            return {"reason": p[0].replace("Reason:","").strip(), "details": p[1].strip() if len(p)>1 else "解析中"}
        
        # 代読強化：数字が取れている場合と取れていない場合で分ける
        if total < 0:
            return {"reason": "【データ調整中】現在、航空会社からの情報を再取得しています。まもなく更新されます。", "details": "⚠️ データ取得の渋滞が発生しています。リロードボタンを押して数秒お待ちください。"}
        msg = f"到着{total}便（欠航{cancel}）を確認。深夜帯のセオリーに従い、最適な場所で待機を。"
        return {"reason": f"【システム推計】{msg}", "details": "⚠️ AIが混雑中のため、過去の統計データに基づき推奨場所を表示しています。"}
    except:
        return {"reason": "通信混雑", "details": "再試行してください"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    dom, intl, delay, cancel = fetch_flight_data()
    
    # データが取れなかった（-1）場合の処理
    if dom < 0: dom = 0
    if intl < 0: intl = 0
    total = dom + intl
    
    if total >= 30: rk = "🌈 S 【 確変・入れ食い 】"
    elif total >= 15: rk = "🔥 A 【 超・推奨 】"
    elif total >= 8: rk = "✨ B 【 狙い目 】"
    else: rk = "⚠️ C 【 要・注意 】"
    
    # 欠航表示ブロックの作成
    cancel_block = f"❌ 欠航便数：{cancel} 便" if cancel > 0 else "✅ 現在、大規模な欠航はありません"
    
    h = n.hour
    tg = f"{max(THEORY_DATA[h], key=THEORY_DATA[h].get)}付近" if h in THEORY_DATA else "国際線/都内"
    pr = f"HND {ns} D:{dom} I:{intl} C:{cancel}"
    ai = call_gemini_single(pr, total, cancel)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", tg).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[NUM_D]]", str(random.randint(150,210))).replace("[[NUM_I]]", str(random.randint(80,115))).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cancel_block)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
