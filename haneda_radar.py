import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    # 試すモデルの優先順位リスト（高速版がないなら、安定版、旧版と順に試します）
    candidates = [
        "models/gemini-1.5-flash",       # 本命（高速）
        "models/gemini-1.5-flash-001",   # 本命の別名
        "models/gemini-1.5-flash-002",   # 本命の最新版
        "models/gemini-1.5-pro",         # 高性能版
        "models/gemini-pro",             # 旧安定版（これなら絶対あるはず）
        "models/gemini-1.0-pro"          # 旧安定版の別名
    ]
    
    prompt = "羽田空港のT1/T2/T3別の現在（16時台）の到着便数と、タクシー需要予測をベテランのセオリーに基づいて短く解説して。"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    final_res = "すべてのモデルで失敗しました。"
    
    # 順番にノックしていきます
    for model in candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={K}"
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                # 成功したらループを抜けて終了！
                final_res = response.json()['candidates'][0]['content']['parts'][0]['text']
                final_res += f"\n\n(使用モデル: {model})" # どのモデルで成功したかメモ
                break
            else:
                # 失敗したら次へ
                continue
                
        except:
            continue

    h = f"""
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style='background:#121212;color:#FFD700;padding:20px;font-family:sans-serif;'>
        <h1 style='border-bottom:2px solid #FFD700;'>🚖 羽田需要レーダー</h1>
        <pre style='white-space:pre-wrap;color:#fff;background:#1e1e1e;padding:15px;border-radius:10px;line-height:1.6;'>{final_res}</pre>
        <p style='text-align:right;color:#888;font-size:0.8rem;'>更新:{ns} (JST)</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
