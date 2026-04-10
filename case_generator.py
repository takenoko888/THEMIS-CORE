"""
Themis-Core — Case Generator
乱数で事件のパラメータを生成し、LLMに事件概要を肉付けさせる。
"""

import random
from prompts import get_case_generation_prompt

def generate_case(client, day: int, memory: dict) -> dict:
    """LLMを使って事件概要を生成"""

    prompt = get_case_generation_prompt(day, memory)

    print(f"  📋 AIに事件データの自動生成を依頼中...")
    print(f"  🔄 LLMに事件概要の生成を要求中...")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "あなたは司法システムのケースファイル生成エンジンです。指示に従い事件概要を生成してください。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        max_tokens=1000,
    )

    case_text = response.choices[0].message.content.strip()

    return {
        "text": case_text,
        "day": day,
    }
