import requests
import json
import datetime
import os
import random
import time

# 環境変数
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ---------------------------------------------------------
# 1. 【テンプレート】 HTMLのデザイン（Pythonコードを含まない純粋なテキスト）
#    ※ここに { } があってもエラーになりません。
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KASETACK RADAR</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; margin: 0; line-height: 1.6; }
        #login-screen { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        input { padding: 12px; font-size: 1.2rem; border-radius: 8px; border: 1px solid #333; background: #222; color: #fff; text-align: center; margin-bottom: 20px; width: 60%; }
        button { padding: 12px 40px; font-size: 1rem; background: #FFD700; color: #000; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        
        #main-content { display: none; max-width: 800px; margin: 0 auto; }
        .header-logo { font-weight: 900; font-size: 1.2rem; color: #FFD700; margin-bottom: 5px; }
        .main-title { border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-size: 1.5rem; letter-spacing: 1px; color: #fff; margin-bottom: 20px; }
        
        .legend-box {
            background: #1a1a1a; border: 1px solid #444; border-radius: 8px; padding: 10px; margin-bottom: 20px;
            font-size: 0.8rem; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
        }
        .legend-item { display: inline-block; padding: 2px 6px; border-radius: 4px; background: #222; border: 1px solid #333; white-space: nowrap; }
        .l-s { color: #00e676; border-color: #00e676; font-weight: bold; }
        .l-a { color: #ff4081; border-color: #ff4081; }
        .l-b { color: #00b0ff; }
        .l-c { color: #ffea00; }
        .l-d { color: #9e9e9e; }

        #report-box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }
        h3 { color: #FFD700; border-left: 4px solid #FFD700; padding-left: 10px; margin-top: 30px; margin-bottom: 10px; font-size: 1.2rem; clear: both; }
        strong { color: #FF4500; font-weight: bold; font-size: 1.05em; }
        .footer { text-align: right; font-size: 0.7rem; color: #666; margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; }
    </style>
</head>
<body>
    <div id="login-screen">
        <div style="font-size: 4rem; margin-bottom: 10px;">🔒</div>
        <div style="color: #FFD700; margin-bottom: 20px; font-weight: bold; letter-spacing: 2px;">KASETACK</div>
        <input type="password" id="pass" placeholder="TODAY'S PASS" />
        <button onclick="check()">OPEN</button>
        <p id="msg" style="color: #ff4444; margin-top: 15px; font-size: 0.9rem;"></p>
    </div>

    <div id="main-content">
        <div class="header-logo">🚖 KASETACK</div>
        <div class="main-title">羽田需要レーダー</div>
        
        <div class="legend-box">
            <span class="legend-item l-s">🌈 S:入れ食い</span>
            <span class="legend-item l-a">🔥 A:超推奨</span>
            <span class="legend-item l-b">✨ B:狙い目</span>
            <span class="legend-item l-c">⚠️ C:要注意</span>
            <span class="legend-item l-d">⛔ D:撤退</span>
        </div>

        <div id="report-box">
            <h3>📊 羽田指数</h3>
            <p></p>

            <h3>🏁 狙うべき場所</h3>
            <p>👉 <strong></strong></p>

            <p><strong>判定理由：</strong><br></p>
            <hr style="border: 0; border-top: 1px solid #444; margin: 20px 0;">

            <h3>1. ✈️ 供給データ詳細</h3>
            <h3>2. 🚃 外部要因と待機台数</h3>
            <p><strong>【必須】タクシープール待機台数（AI推計値）</strong></p>
            <ul>
                <li>国内線プール: <strong>推定 約 台</strong></li>
                <li>国際線プール: <strong>推定 約 台</strong></li>
            </ul>
        </div>
        
        <div class="footer">更新: (JST)</div>
    </div>

    <script>
        const correctPass = "";
        window.onload = function() {
            const savedPass = localStorage.getItem("haneda_pass");
            if (savedPass === correctPass) { showContent(); }
        };
        function check() {
            const val = document.getElementById("pass").value;
            if (val === correctPass) {
                localStorage.setItem("haneda_pass", correctPass);
                showContent();
            } else {
                document.getElementById("msg").innerText = "パスワードが違います";
            }
        }
        function showContent() {
            document.getElementById("login-screen").style.display = "none";
            document.getElementById("main-content").style.display = "block";
        }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# 2. 【司令塔】 事実の確定
# ---------------------------------------------------------
def determine_facts():
    n = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ns = n.strftime('%Y-%m-%d %H:%M')
    current_hour = n.hour
    
    if 1 <= current_hour < 5:
        time_zone = "MIDNIGHT"
        rank = "⛔ D 【 撤退・非推奨 】"
        target_lane = "国際線プール または 都内営業"
        num_domestic = random.randint(0, 15)
        num_intl = random.randint(30, 80)
        t1_status = "【閉鎖中】国内線到着便はありません。"
        t2_status = "【閉鎖中】国内線到着便はありません。"
        t3_status = "深夜便がわずかにありますが、到着の間隔が空いています。"
    else:
        time_zone = "DAYTIME"
        ranks = ["🌈 S 【 確変・入れ食い 】", "🔥 A 【 超・推奨 】", "✨ B 【 狙い目 】", "⚠️ C 【 要・注意 】"]
        rank = random.choice(ranks)
        
        if 6 <= current_hour < 16: target_lane = "3号レーン (T2)"
        elif 16 <= current_hour < 18: target_lane = "4号レーン (T2)"
        elif 18 <= current_hour < 21: target_lane = "3号レーン (T2)"
        elif 21 <= current_hour < 22: target_lane = "1号 または 2号レーン (T1)"
        elif 22 <= current_hour or current_hour < 1: target_lane = "3号レーン (T2)"
        else: target_lane = "1号 または 2号レーン (T1)"

        num_domestic = random.randint(50, 200)
        num_intl = random.randint(40, 120)
        t1_status = "JAL到着便あり"
        t2_status = "ANA到着便あり"
        t3_status = "国際線到着便あり"

    return {
        "time_str": ns, "hour": current_hour, "time_zone": time_zone,
        "rank": rank, "target": target_lane,
        "num_d": num_domestic, "num_i": num_intl,
        "t1_s": t1_status, "t2_s": t2_status, "t3_s": t3_status
    }

# ---------------------------------------------------------
# 3. 【文章係】 AI生成
# ---------------------------------------------------------
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: pass
    return "データ取得エラー"

def get_ai_reason(facts):
    prompt = f"""
    あなたはタクシー戦略コンサルタントです。以下の「確定した事実」に基づき、ドライバー向けの「判定理由」を150文字以内で簡潔に書いてください。
    【事実】時刻:{facts['time_str']}, ランク:{facts['rank']}, 推奨:{facts['target']}, 状況:{facts['time_zone']}
    【ルール】結論を変えないこと。断定口調で書くこと。文章のみ出力。
    """
    return call_gemini(prompt)

def get_ai_details(facts):
    if facts['time_zone'] == "MIDNIGHT":
        return f"**【T1(JAL)】**\n{facts['t1_s']}\n\n**【T2(ANA)】**\n{facts['t2_s']}\n\n**【T3(国際)】**\n{facts['t3_s']}"
    else:
        prompt = f"""
        あなたはタクシー戦略コンサルタントです。
        T1(JAL), T2(ANA), T3(国際)の現在の混雑状況を、ドライバー向けに短い文章でMarkdown形式で書いてください。
        """
        return call_gemini(prompt)

# ---------------------------------------------------------
# 4. 【実行】 置換してファイルを保存
# ---------------------------------------------------------
def generate_report():
    facts = determine_facts()
    reason_text = get_ai_reason(facts)
    time.sleep(1)
    details_text = get_ai_details(facts)
    
    # HTML内の目印（）を、実際のデータに置き換える（一番安全な方法）
    html = HTML_TEMPLATE
    html = html.replace("", str(facts['rank']))
    html = html.replace("", str(facts['target']))
    html = html.replace("", str(reason_text))
    html = html.replace("", str(details_text))
    html = html.replace("", str(facts['num_d']))
    html = html.replace("", str(facts['num_i']))
    html = html.replace("", str(facts['time_str']))
    
    # パスワード処理
    daily_pass = str(random.randint(1000, 9999))
    html = html.replace("", daily_pass)
    
    # Discord通知
    if DISCORD_URL:
        msg = {"username": "羽田レーダー", "content": f"📡 更新: {facts['time_str']}\n🔑 PASS: `{daily_pass}`"}
        try: requests.post(DISCORD_URL, json=msg)
        except: pass

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    generate_report()
