import requests
import json
import datetime
import os

API_KEY = os.getenv("GEMINI_API_KEY")

def get_prompt(now_time):
    return f"羽田空港のリアルタイム需要分析（14時〜16時の到着便数と予測降機人数）をT1/T2/T3別に算出して。現在時刻：{now_time}"

def generate_report():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_str = now.strftime('%Y-%m-%d %H:%M')
    
    report_content = "有効なモデルが見つかりませんでした。"
    
    try:
        # 1. まず、このAPIキーで「今、何が使えるのか」をGoogleにリストアップさせます
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        models_res = requests.get(list_url).json()
        
        # 使えるモデル名を探す
        target_model = None
        if 'models' in models_res:
            for m in models_res['models']:
                # generateContent が可能なモデルを探す
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    target_model = m['name']
                    # 1.5 flashがあれば最優先、なければ最初に見つかったもの
                    if 'gemini-1.5-flash' in m['name']:
                        break
        
        if target_model:
            # 2. 見つかった「確実に動くモデル名」を使って分析を依頼します
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={API_KEY}"
            payload = {"contents": [{"parts": [{"text": get_prompt(now_str)}]}]}
            res = requests.post(gen_url, json=payload, timeout=30).json()
            
            if 'candidates' in res:
                report_content = res['candidates'][0]['content']['parts'][0]['text']
            else:
                report_content = f"モデル {target_model} は見つかりましたが、回答が得られませんでした。\n{json.dumps(res, ensure_ascii=False)}"
        else:
            report_content = f"このAPIキーで利用可能なGeminiモデルが見つかりませんでした。プロジェクトの設定を確認してください。\nリスト結果: {json.dumps(models_res, ensure_ascii=False)}"

    except Exception as e:
        report_content = f"実行エラー: {str(e)}"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>カセタク・羽田レーダー</title>
        <style>
            body {{ background: #121212; color: #FFD700; font-family: sans-serif; padding: 20px; }}
            h1 {{ border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.2rem; }}
            pre {{ background: #1e1e1e; padding: 15px; border-radius: 10px; white-space: pre-wrap; color: #fff; border: 1px solid #333; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div style="font-weight:bold;">🚖 KASETACK</div>
        <h1>羽田空港需要分析</h1>
        <pre>{report_content}</pre>
        <div style="text-align:right; font-size:0.7rem; color:#888; margin-top:20px;">最終更新: {now_str}</div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_report()
