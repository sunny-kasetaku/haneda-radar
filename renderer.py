# ==========================================
# Project: KASETACK - renderer.py (Mobile High-Visibility)
# ==========================================
import json
import os
from config import CONFIG

def run_render():
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

    # ランク判定（現場感覚に合わせたS〜D判定）
    rank = "D"
    rank_msg = "需要なし"
    if total_pax >= 800: rank, rank_msg = "S", "【最高】爆益確定"
    elif total_pax >= 400: rank, rank_msg = "A", "【期待】攻め時"
    elif total_pax >= 100: rank, rank_msg = "B", "【普通】様子見"
    elif total_pax > 0: rank, rank_msg = "C", "【注意】撤退推奨"

    # 現場特化型HTML（ダークモード・デカ文字・ユニバーサルデザイン）
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
            .footer {{ color: #555; font-size: 14px; margin-top: 20px; }}
            .flight-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            .flight-table td {{ padding: 10px; border-bottom: 1px solid #222; }}
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

        <div class="footer">
            最終更新: {update_time} (JST) | v4.0 API Live<br>
            ⚠️ データは15分ごとに自動更新されます
        </div>
    </body>
    </html>
    """

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ デザイン適用完了: {report_file} を更新しました。")
