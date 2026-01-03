import requests
import json
import datetime
import os

K = os.getenv("GEMINI_API_KEY")

def generate_report():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    
    prompt = "羽田空港のT1/T2/T3別の14時〜16時の到着便数と、タクシー需要予測を短く教えて。"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    report_content = "有効なモデルが見つかりませんでした。"
    
    try:
        # 1. まず、このAPIキーで「今、何が使えるのか」をGoogleに白状させます
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={K}"
        models_res = requests.get(list_url).json()
        
        target_model = None
        if 'models' in models_res:
            for m in models_res['models']:
                # 生成機能（generateContent）が許可されているモデルを自動抽出
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    target_model = m['name']
                    # gemini-1.5-flashがあれば優先、なければ何でもいいから使う
                    if 'gemini-1.5-flash' in m['name']:
                        break
        
        if target_model:
            # 2. 見つかった「確実に許可されているモデル」で実行
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={K}"
            res = requests.post(gen_url, json=payload, timeout=30).json()
            
            if 'candidates' in res:
                report_content = res['candidates'][0]['content']['parts'][0]['text']
            else:
                report_content = f"モデル {target_model} は見つかりましたが、回答が得られませんでした。\n{json.dumps(res, ensure_ascii=False)}"
        else:
            report_content = f"このAPIキーで使えるGeminiモデルが1つもありません。\nリスト結果: {json.dumps(models_res, ensure_ascii=False)}"

    except Exception as e:
        report_content = f"実行エラー: {str(e)}"

    h = f"""
    <html>
    <body style='background:#121212;color:#FFD700;padding:20px;font-family:sans-serif;'>
        <h1 style='border-bottom:2px solid #FFD700;'>🚖 羽田需要レーダー</h1>
        <pre style='white-space:pre-wrap;color:#fff;background:#1e1e1e;padding:15px;border-radius:10px;line-height:1.6;'>{report_content}</pre>
        <p style='text-align:right;color:#888;font-size:0.8rem;'>更新:{ns} (JST)</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(h)

if __name__ == "__main__":
    generate_report()
