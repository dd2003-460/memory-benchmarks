"""
LoCoMo temporal 快速 smoke 测试：convo0 前 5 sessions（验证时间锚定修复）

用法：
    cd tools/memory-benchmarks
    export $(grep -v '^#' .env | xargs)
    export NO_PROXY=100.112.53.47
    /Users/a1-6/Desktop/workspace/tools/mb-server-venv/bin/python -m benchmarks.locomo.smoke_temporal_quick
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

# 确保项目根目录在 sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from benchmarks.locomo.run import (
    load_locomo_dataset,
    chunk_sessions,
    ingest_conversation,
    predict_question,
    format_search_results,
    get_answer_generation_prompt,
)
from benchmarks.common.mem0_client import Mem0Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("smoke_temporal_quick")

# 配置
MEM0_SERVER = os.getenv("MEM0_SERVER", "http://127.0.0.1:8888")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", os.getenv("OPENAI_API_KEY"))
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", os.getenv("OPENAI_BASE_URL"))
DATASET_PATH = project_root / "datasets" / "locomo" / "locomo10.json"
OUTPUT_DIR = project_root / "runs" / "ablation-L1" / "smoke_temporal_quick"


async def main():
    logger.info("=" * 60)
    logger.info("LoCoMo temporal 快速 smoke 测试：convo0 前 5 sessions × temporal 题")
    logger.info("=" * 60)

    # 加载数据集
    dataset = load_locomo_dataset(str(DATASET_PATH))
    conversation = dataset[0]
    logger.info(f"✅ 加载对话 0: {conversation['name']}, {len(conversation['sessions'])} sessions")

    # 只取前 5 sessions
    sessions = conversation["sessions"][:5]
    logger.info(f"📋 使用 sessions 1-5（共 {len(sessions)} sessions）")

    # 初始化客户端
    mem0 = Mem0Client(MEM0_SERVER)
    answerer = LLMClient(VLLM_BASE_URL, VLLM_API_KEY)
    judge = LLMClient(VLLM_BASE_URL, VLLM_API_KEY)

    # 清理旧数据
    user_id = "locomo_0_smoke-temporal-quick"
    await mem0.delete_all_memories(user_id)
    logger.info(f"🧹 已清理用户 {user_id} 的旧记忆")

    # Ingest
    logger.info("\n[1/2] Ingest 对话（前 5 sessions，应用时间锚定修复）...")
    chunks = chunk_sessions(sessions)
    logger.info(f"  共 {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        try:
            await ingest_conversation(mem0, user_id, chunk, sessions)
            if i % 10 == 0:
                logger.info(f"  Ingested {i+1}/{len(chunks)} chunks")
        except Exception as e:
            logger.warning(f"  ADD chunk {i} failed: {e}")

    logger.info(f"✅ Ingest 完成：{len(chunks)} chunks")

    # 筛选 temporal 题（category == 4）
    qa_pairs = [qa for qa in conversation["qa"] if qa.get("category") == 4]
    logger.info(f"\n[2/2] Predict temporal 题：共 {len(qa_pairs)} 题")

    results = []
    for i, qa in enumerate(qa_pairs[:5]):  # 只测前 5 题
        question = qa["question"]
        gt_answer = qa.get("answer", "")
        reference_date = qa.get("reference_date", "")

        logger.info(f"\n  [{i+1}/5] Q: {question}")
        logger.info(f"        GT: {gt_answer} (ref: {reference_date})")

        # Search
        search_results = await mem0.search(question, user_id, top_k=5)
        results_text = format_search_results(search_results)

        # Generate answer
        prompt = get_answer_generation_prompt(
            question, results_text, reference_date, user_profile=""
        )
        predicted = await answerer.generate(prompt)

        # Judge
        judge_prompt = f"""Question: {question}
Correct Answer: {gt_answer}
Predicted Answer: {predicted}

Is the predicted answer correct? Answer with {{correct: true/false}}."""
        judge_response = await judge.generate_structured(judge_prompt)
        is_correct = judge_response.get("correct", False)

        results.append({
            "question": question,
            "gt_answer": gt_answer,
            "predicted_answer": predicted,
            "is_correct": is_correct,
        })
        logger.info(f"        Predicted: {predicted[:80]}...")
        logger.info(f"        Correct: {is_correct}")

    # 汇总
    correct = sum(1 for r in results if r["is_correct"])
    accuracy = correct / len(results) if results else 0

    logger.info("\n" + "=" * 60)
    logger.info(f"✅ 测试完成：{correct}/{len(results)} correct ({accuracy:.0%})")
    logger.info("=" * 60)

    # 保存结果
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accuracy": accuracy,
            "correct": correct,
            "total": len(results),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"📄 结果已保存：{output_file}")


class LLMClient:
    """简单的 LLM 客户端"""

    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def generate(self, prompt, max_tokens=1024):
        import aiohttp
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "qwen3.8-27b-w8a16",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"LLM API error {resp.status}: {text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def generate_structured(self, prompt, max_tokens=256):
        """生成结构化 JSON 响应"""
        import re
        response = await self.generate(prompt, max_tokens=max_tokens)
        # 提取 JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"correct": False, "raw": response}


if __name__ == "__main__":
    asyncio.run(main())
