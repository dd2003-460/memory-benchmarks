#!/usr/bin/env python3
"""
LoCoMo temporal 专用 smoke 测试
- 测试 conv0 的 temporal 问题（category 4）
- 验证时间锚定修复效果
- 使用方法: /Users/a1-6/Desktop/workspace/tools/mb-server-venv/bin/python -m benchmarks.locomo.smoke_temporal
"""
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from benchmarks.common.mem0_client import Mem0Client
from benchmarks.common.llm_client import LLMClient
from benchmarks.locomo.run import (
    GracefulShutdown,
    Checkpoint,
    ingest_conversation,
    process_question,
    load_dataset,
    download_dataset,
    DEFAULT_DATASET_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 测试参数
CONVO_IDX = 0  # 第 1 个对话
MAX_QUESTIONS = 5  # 最多 5 题（temporal）
OUTPUT_DIR = Path("/tmp/locomo-smoke-temporal")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("LoCoMo temporal 专用 smoke 测试：convo0 × 5 题（验证时间锚定修复）")
    logger.info("=" * 60)
    
    # 1. 初始化 LLM client
    answerer = LLMClient(model="qwen3.8-27b-w8a16", provider="openai", rpm=30)
    judge_llm = LLMClient(model="qwen3.8-27b-w8a16", provider="openai", rpm=30)
    
    # 2. 初始化 mem0 client
    mem0 = Mem0Client(
        host="http://127.0.0.1:8888",
        api_key=None,
        rpm=30,
    )
    
    # 3. 加载 LoCoMo 数据集
    dataset_path = download_dataset(DEFAULT_DATASET_DIR, logger)
    dataset = load_dataset(dataset_path)
    
    if not dataset:
        logger.error("❌ 无法加载 LoCoMo 数据集")
        return
    
    convo = dataset[CONVO_IDX]
    logger.info(f"✅ 加载对话 {CONVO_IDX}: {len(convo.get('conversation', []))} sessions")
    
    # 4. 初始化 shutdown 和 checkpoint
    shutdown = GracefulShutdown()
    checkpoint = Checkpoint(OUTPUT_DIR)
    
    # 5. Ingest 对话（应用时间锚定修复）
    logger.info("\n[1/2] Ingest 对话（应用时间锚定修复）...")
    start_time = time.time()
    
    success, user_id, total_processed = await ingest_conversation(
        conv_idx=CONVO_IDX,
        entry=convo,
        mem0=mem0,
        logger=logger,
        run_id="smoke-temporal-fix",
        project_name="locomo-smoke-temporal",
        output_dir=str(OUTPUT_DIR),
        shutdown=shutdown,
        debug=False,
    )
    
    ingest_time = time.time() - start_time
    logger.info(f"✅ Ingest 完成: {total_processed} chunks, 耗时 {ingest_time:.1f}s")
    
    if not success:
        logger.error("❌ Ingest 失败")
        return
    
    # 6. Predict temporal 问题（最多 5 题，category 4）
    logger.info("\n[2/2] Predict temporal 问题（最多 5 题，category 4）...")
    start_time = time.time()
    
    questions = convo.get("qa", convo.get("qa_pairs", []))
    # 筛选 temporal 问题（category 4）
    temporal_qs = [(qi, qa) for qi, qa in enumerate(questions) if qa.get("category") == 4]
    
    # 取前 5 个 temporal 问题
    test_qs = temporal_qs[:MAX_QUESTIONS]
    
    if not test_qs:
        logger.error("❌ conv0 没有 temporal 问题")
        return
    
    logger.info(f"✅ 找到 {len(test_qs)} 个 temporal 问题")
    
    results = []
    for qi, qa in test_qs:
        qid = f"conv{CONVO_IDX}_q{qi}"
        
        logger.info(f"\n--- 处理 {qid} ---")
        logger.info(f"  Question: {qa.get('question', '')}")
        logger.info(f"  Answer: {qa.get('answer', '')}")
        
        try:
            result = await process_question(
                qa=qa,
                qa_idx=qi,
                conv_idx=CONVO_IDX,
                user_id=user_id,
                mem0=mem0,
                answerer=answerer,
                judge_llm=judge_llm,
                cutoffs=[10],  # 只用 top-10
                top_k=10,
                reference_date_human=None,
                user_profile=None,
                evidence_lookup=None,
                predict_only=False,
                logger=logger,
                score_debug=False,
            )
            
            # 提取结果
            cutoff_results = result.get("cutoff_results", {})
            top10 = cutoff_results.get("top10", {})
            
            is_correct = top10.get("correct", False)
            predicted = top10.get("generated_answer", "")
            
            logger.info(f"  Predicted: {predicted[:100]}")
            logger.info(f"  Correct: {'✅' if is_correct else '❌'}")
            
            results.append({
                "question_id": qid,
                "question": qa.get("question", ""),
                "ground_truth": qa.get("answer", ""),
                "predicted": predicted,
                "correct": is_correct,
            })
            
            # 保存结果
            result_path = OUTPUT_DIR / f"{qid}.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "question_id": qid,
                "question": qa.get("question", ""),
                "ground_truth": qa.get("answer", ""),
                "predicted": None,
                "correct": False,
                "error": str(e),
            })
    
    predict_time = time.time() - start_time
    logger.info(f"\n✅ Predict 完成: {len(results)} 题, 耗时 {predict_time:.1f}s")
    
    # 7. 输出结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果：")
    logger.info("=" * 60)
    
    correct = 0
    for r in results:
        is_correct = r.get("correct", False)
        if is_correct:
            correct += 1
        
        logger.info(f"  {r.get('question_id')}: {'✅' if is_correct else '❌'}")
        if not is_correct:
            logger.info(f"    Predicted: {r.get('predicted', '')[:100]}")
            logger.info(f"    Ground truth: {r.get('ground_truth', '')[:100]}")
    
    accuracy = correct / len(results) if results else 0
    logger.info(f"\n总准确率: {correct}/{len(results)} = {accuracy:.2%}")
    
    # 8. 保存结果
    output_file = OUTPUT_DIR / "smoke_temporal_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "convo_idx": CONVO_IDX,
            "total_questions": len(results),
            "correct": correct,
            "accuracy": accuracy,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 结果已保存: {output_file}")
    
    # 9. 清理
    await mem0.close()

if __name__ == "__main__":
    asyncio.run(main())
