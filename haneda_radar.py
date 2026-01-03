import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # 【ここが修正の核心】 v1beta をやめて v1 (安定版) に固定します
    u1 = "https://generativelanguage.googleapis.com/v1/"
    u2 = "models/gemini-1.5-flash:generateContent?key="
    url = u1 + u2 + str(K)
    
    prompt = "羽田空港のT1/T2/T3別の14時〜16時の到着便数と、タクシー需要予測を短く教えて。"
    p = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        r = requests.post(url, json=p, timeout=30)
        j = r.json()
        if r.status_code == 200:
            res = j['candidates'][0]['content']['parts'][0]['text']
        else:
            # もしv1でもダメなら、予備でgemini-proを試す
            u2_alt = "models/gemini-pro:generateContent?key="
            url_alt = u1 + u2_alt + str(K)
            r_alt = requests.post(url_alt, json=p, timeout=30)
            if r_alt.status_code == 200:
                res = r_alt.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                res = f"API Error: {r.status_code}\nメッセージ: {json.dumps(j, ensure_ascii=False)}"
    except Exception as e:
        res = "Error: " + str(e)

    h = f"""
    <html>
    <body style='background:#121212;color:#FFD700;padding:20px;font-family:sans-serif;'>
        <h1 style='border-bottom:2px solid #FFD700;'>🚖 羽田需要レーダー</h1>
        <pre style='white-space:pre-wrap;color:#fff;background:#1e1e1e;padding:15px;border-radius:10px;line-height:1.6;'>{res}</pre>
        <p style='text-align:right;color:#888;font-size:0.8rem;'>更新:{ns} (JST)</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
