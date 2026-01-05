import requests
import datetime
import os
import random
import re

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TRAVEL_TIME = 20  # 移動想定時間（分）

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
    .ai-text { line-height: 1.8; font-size: 1.05rem; }
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
    <p><strong>判定理由：</strong><br><span class="ai-text">[[REASON]]</span></p>
    <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
    <h3>✈️ 供給データ詳細</h3>
    <div class="ai-text">[[DETAILS]]</div>
    <div class="update-area">
        <button class="reload-btn" onclick="location.reload()">最新情報に更新</button>
        <div id="timer">次回自動更新まで あと <span id="sec">60</span> 秒</div>
    </div>
</div>
<div class="footer">更新: [[TIME]] (JST) | 移動想定: [[T_TIME]]分<br>🔑 PASS: [[PASS]]</div>
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

def fetch_flights_brute_force():
    urls = ["https://transit.yahoo.co.jp/airport/arrival/23/?kind=1", "https://transit.yahoo.co.jp/airport/arrival/23/?kind=2"]
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    total_valid = 0
    c_count = 0
    d_count = 0
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = "utf-8"
            html = r.text
            
            # 欠航と遅延のカウント（テキストから直接）
            c_count += html.count("欠航")
            d_count += html.count("遅れ") + html.count("延着") + html.count("変更")
            
            # 💡 時刻（XX:XX）をすべて抽出
            times = re.findall(r'(\d{1,2}):(\d{2})', html)
            for h, m in times:
                f_hour, f_min = int(h), int(m)
                f_time = now.replace(hour=f_hour, minute=f_min, second=0, microsecond=0)
                
                # 深夜の翌日補正 (例: 現在23時、便が01時なら翌日とする)
                if now.hour >= 20 and f_hour <= 4:
                    f_time += datetime.timedelta(days=1)
                
                diff = (f_time - now).total_seconds() / 60
                
                # 移動時間(TRAVEL_TIME)の20分後から、その先2時間までを「有効需要」とする
                if (TRAVEL_TIME - 10) < diff < (TRAVEL_TIME + 120):
                    total_valid += 1
        except:
            pass
    # ページ上部の現在時刻なども拾ってしまうため、少し多めに出るのを補正(各ページ5件分くらいを共通パーツとして引く)
    total_valid = max(0, total_valid - 10)
    return total_valid, c_count, d_count

def call_ai(total, cancel, delay):
    if not GEMINI_KEY: return {"reason": "Key Error", "details": "N/A"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    # プロンプトを日本語で直接指示
    p = f"羽田タクシー需要予測: 今から{TRAVEL_TIME}分後に到着した場合、有効便数は{total}便(遅延{delay}, 欠航{cancel})。運転手への助言を100文字以内で。"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=20).json()
        if "candidates" in res:
            return {"reason": res["candidates"][0]["content"]["parts"][0]["text"], "details": f"✈️ 2時間以内の予測有効便: {total}便 / 遅延傾向あり"}
        return {"reason": f"【システム推計】有効便数 {total}便。移動時間 {TRAVEL_TIME}分を考慮し、現在は慎重な判断を。","details": f"AI制限中 (生データ有効便数: {total})"}
    except: return {"reason": "通信エラー", "details": "再試行"}

def generate_report():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    n = datetime.datetime.now(jst)
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    v, c, d = fetch_flights_brute_force()
    
    # ランク判定
    if v >= 15: rk = "🌈 S 【 激アツ・即出撃 】"
    elif v >= 7: rk = "🔥 A 【 推奨・1時間以内出庫 】"
    elif v >= 3: rk = "✨ B 【 狙い目・効率重視 】"
    else: rk = "⚠️ C 【 ハマる危険大 】"
    
    target = "T2(国内線)またはT3" if v > 5 else "T3(国際線)または都内"
    cb = f"❌ 欠航：{c} 便 / ⚠️ 遅延：{d} 便" if (c + d) > 0 else "✅ 順調な運行です"
    ai = call_ai(v, c, d)
    
    random.seed(n.strftime('%Y%m%d'))
    pw = str(random.randint(1000, 9999))
    
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[TARGET]]", target).replace("[[REASON]]", ai['reason']).replace("[[DETAILS]]", ai['details']).replace("[[TIME]]", ns).replace("[[PASS]]", pw).replace("[[CANCEL_BLOCK]]", cb).replace("[[T_TIME]]", str(TRAVEL_TIME))
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    generate_report()
