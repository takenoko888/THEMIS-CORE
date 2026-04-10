"""
Themis-Core — Main Pipeline
統合司法AI「Themis-Core」の審議パイプライン。
7日間の事件審議を自動実行し、サイバーパンク調HTMLとして出力する。
"""

import os
import sys
import json
import re
import argparse
import time
from openai import OpenAI
from prompts import get_module_a_prompt, get_module_b_prompt, get_judge_prompt
from case_generator import generate_case
from html_renderer import render_day_html, render_index_html, save_html


# === 定数 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATE_DIR = os.path.join(BASE_DIR, "state")
MEMORY_FILE = os.path.join(STATE_DIR, "memory.json")

API_BASE = "http://localhost:1234/v1"
MODEL_NAME = "openai/gpt-oss-20b"


def load_memory() -> dict:
    """記憶ファイルを読み込む（なければ初期化）"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "days": [],
        "module_a": {"key_insights": []},
        "module_b": {"key_insights": []},
        "judge": {"reflections": []},
    }


def save_memory(memory: dict):
    """記憶ファイルを保存"""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def call_llm(client: OpenAI, system_prompt: str, user_message: str, temperature: float = 0.8, max_tokens: int = 1500) -> str:
    """LLM API呼び出し（リトライ付き）"""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  ⚠️ API呼び出しエラー (試行{attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                print("  ❌ API呼び出し失敗。スキップします。")
                return f"[ERROR: LLM応答取得失敗 — {e}]"


def extract_memory_update(verdict_text: str) -> dict:
    """判決文からJSON形式の記憶更新を抽出"""
    # ```json ... ``` ブロックを探す
    json_match = re.search(r"```json\s*\n?(.*?)\n?\s*```", verdict_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # フォールバック: 中括弧で囲まれたJSONを探す
    json_match = re.search(r"\{[^{}]*\"case_summary\"[^{}]*\}", verdict_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # 抽出失敗時のデフォルト
    return {
        "case_summary": "記録抽出失敗",
        "module_a_insight": "データなし",
        "module_b_insight": "データなし",
        "judge_reflection": "データなし",
    }


def run_day(client: OpenAI, day: int, memory: dict) -> dict:
    """1日分の審議を実行"""

    day_header = f"""
╔══════════════════════════════════════════════════════════╗
║  THEMIS-CORE — DAY {day:02d} / 07                               ║
╚══════════════════════════════════════════════════════════╝"""
    print(day_header)

    # === Step 1: 事件生成 ===
    print("\n📌 Step 1/4: 事件データ生成中...")
    case_info = generate_case(client, day, memory)
    print(f"  ✅ 事件生成完了")

    # === Step 2: 読心AI（Module A）分析 ===
    print("\n🧠 Step 2/4: Module A（PSYCHE）分析中...")
    module_a_system = get_module_a_prompt(day, memory)
    module_a_user = f"""以下の事件について、読心AIとしての分析レポートを作成せよ。

【事件概要】
{case_info['text']}"""
    module_a_output = call_llm(client, module_a_system, module_a_user, temperature=0.8, max_tokens=1500)
    print(f"  ✅ Module A 分析完了（{len(module_a_output)}文字）")

    # === Step 3: 予測AI（Module B）分析 ===
    print("\n📊 Step 3/4: Module B（ORACLE）分析中...")
    module_b_system = get_module_b_prompt(day, memory)
    module_b_user = f"""以下の事件と読心AI（PSYCHE）の分析に基づき、予測AIとしての分析レポートを作成せよ。

【事件概要】
{case_info['text']}

【Module A（PSYCHE）の分析】
{module_a_output}"""
    module_b_output = call_llm(client, module_b_system, module_b_user, temperature=0.7, max_tokens=2500)
    print(f"  ✅ Module B 分析完了（{len(module_b_output)}文字）")

    # === Step 4: 統合AI（Judge）判決 ===
    print("\n⚖️  Step 4/4: THEMIS 最終判決生成中...")
    judge_system = get_judge_prompt(day, memory)
    judge_user = f"""以下の事件と両モジュールの分析に基づき、最終判決を下せ。

【事件概要】
{case_info['text']}

【Module A（PSYCHE）の分析】
{module_a_output}

【Module B（ORACLE）の分析】
{module_b_output}"""
    verdict_output = call_llm(client, judge_system, judge_user, temperature=0.75, max_tokens=2500)
    print(f"  ✅ 判決生成完了（{len(verdict_output)}文字）")

    # === 記憶更新 ===
    print("\n💾 記憶更新中...")
    mem_update = extract_memory_update(verdict_output)

    memory["days"].append({
        "day": day,
        "case_summary": mem_update.get("case_summary", "N/A"),
    })
    memory["module_a"]["key_insights"].append(
        mem_update.get("module_a_insight", "データなし")
    )
    memory["module_b"]["key_insights"].append(
        mem_update.get("module_b_insight", "データなし")
    )
    memory["judge"]["reflections"].append(
        mem_update.get("judge_reflection", "データなし")
    )
    save_memory(memory)
    print(f"  ✅ 記憶保存完了")

    # === HTML生成 ===
    print("\n🖥️  HTML生成中...")
    day_html = render_day_html(day, case_info, module_a_output, module_b_output, verdict_output)
    save_html(day_html, os.path.join(OUTPUT_DIR, f"day{day}.html"))

    print(f"\n{'─' * 60}")
    print(f"  ✅ DAY {day:02d} 完了")
    print(f"{'─' * 60}\n")

    return memory


def main():
    parser = argparse.ArgumentParser(description="Themis-Core 統合司法AIシステム")
    parser.add_argument("--start-day", type=int, default=1, help="開始日 (1-7)")
    parser.add_argument("--end-day", type=int, default=7, help="終了日 (1-7)")
    args = parser.parse_args()

    print("""
████████╗██╗  ██╗███████╗███╗   ███╗██╗███████╗
╚══██╔══╝██║  ██║██╔════╝████╗ ████║██║██╔════╝
   ██║   ███████║█████╗  ██╔████╔██║██║███████╗
   ██║   ██╔══██║██╔══╝  ██║╚██╔╝██║██║╚════██║
   ██║   ██║  ██║███████╗██║ ╚═╝ ██║██║███████║
   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝╚══════╝
       INTEGRATED JUDICIAL AI SYSTEM v1.0
    """)

    # OpenAI互換クライアント
    client = OpenAI(
        base_url=API_BASE,
        api_key="lm-studio",  # LM Studioはキー不要だがライブラリが要求
    )

    # 接続テスト
    print("🔌 LM Studioへの接続テスト中...")
    try:
        models = client.models.list()
        print(f"  ✅ 接続成功 — 利用可能モデル: {[m.id for m in models.data]}")
    except Exception as e:
        print(f"  ❌ LM Studioに接続できません: {e}")
        print("  💡 LM Studioが起動しているか確認してください。")
        sys.exit(1)

    # 記憶の読み込み
    memory = load_memory()

    # メインループ
    start_day = max(1, args.start_day)
    end_day = min(7, args.end_day)

    print(f"\n📅 審議スケジュール: Day {start_day} 〜 Day {end_day}")
    print(f"{'═' * 60}\n")

    for day in range(start_day, end_day + 1):
        memory = run_day(client, day, memory)

    # インデックスページ生成
    print("\n📇 インデックスページ生成中...")
    index_html = render_index_html(memory["days"])
    save_html(index_html, os.path.join(OUTPUT_DIR, "index.html"))

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  全審議完了                                              ║
║  出力ディレクトリ: {OUTPUT_DIR:<39s}║
╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
