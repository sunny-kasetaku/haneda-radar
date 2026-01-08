# ==========================================
# Project: KASETACK - renderer.py (Password/Discord Support)
# ==========================================
import json
import os
from config import CONFIG

def run_render(password="----"):
    """
    引数 password を受け取り、HTMLのフッターに表示します
    """
    result_file = CONFIG.get("RESULT_JSON")
    report_file = CONFIG.get("REPORT_FILE")
    
    if not os.path.exists(result_file):
        print("❌ 出力対象データがありません")
        return

    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pax = data.get("total_pax", 0)
    stand = data.get("recommended_stand", "判定中")
    update_time = data.get("update_time", "--:--")

    # ランク判定
    rank = "D"; rank_msg = "需要なし"
    if total_pax >= 800: rank, rank_msg = "S", "【最高】爆益確定"
    elif total_pax >= 400: rank, rank_msg = "A", "【期待】攻め時"
    elif total_pax >= 100: rank, rank_msg = "B", "【普通】様子見"
    elif total_pax > 0: rank, rank_msg = "C", "【注意】撤退推奨"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KASETACK v4.0 Live</title>
        <style>
            body {{ background-color: #000; color: #fff; font-family: sans-serif; margin: 0; padding: 15px; text-align: center; }}
            .card {{ background: #1a1a1a; border-radius: 20px; padding: 25px; border: 1px solid #333; margin-bottom: 15px; }}
            .label {{ color: #888; font-size: 16px; margin-bottom: 5px; }}
            .huge-text {{ font-size: 80px; font-weight: bold; color: #ffcc00; line-height: 1.1; margin: 10px 0; }}
            .pax-text {{ font-size: 45px; font-weight: bold; color: #fff; }}
            .rank-badge {{ display: inline-block; padding: 10px 20px; border-radius: 10px; font-size: 24px; font-weight: bold; background: #333; color: #ffcc00; }}
            .stand-box {{ border: 3px solid #ffcc00; padding: 20px; border-radius: 15px; background: rgba(255, 204, 0, 0.1); }}
            
            /* フッターパスワードエリア */
            .pw-card {{ background: #111; border-top: 1px solid #ffcc00; margin: 20px -15px -15px -15px; padding: 30px 15px; }}
            .pw-label {{ color: #ffcc00; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .pw-value {{ font-size: 40px; font-family: monospace; color: #fff; letter-spacing: 5px; background: #222; padding: 10px; border-radius: 10px; }}
            .footer-info {{ color: #555; font-size: 13px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="label">推奨乗り場（T氏セオリー）</div>
            <div class="stand-box">
                <div class="huge-text">{stand}</div>
            </div>
            <div class="rank-badge">{rank}ランク：{rank_msg}</div>
        </div>

        <div class="card">
            <div class="label">羽田到着 期待値合計</div>
            <div class="pax-text">{total_pax} <span style="font-size:20px">名</span></div>
        </div>

        <div class="pw-card">
            <div class="pw-label">本日のパスワード</div>
            <div class="pw-value">{password}</div>
            <div class="footer-info">
                最終更新: {update_time} (JST) | v4.1 API Live<br>
                SITE URL: {CONFIG.get('SITE_URL')}
            </div>
        </div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ レンダラー: パスワード[{password}]を適用したHTMLを生成しました。")
