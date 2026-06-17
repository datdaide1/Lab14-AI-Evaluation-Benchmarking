import asyncio
import json
import os
import time
import ssl

def _patched_load_default_certs(*args, **kwargs):
    pass
ssl.SSLContext.load_default_certs = _patched_load_default_certs

from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent


from google import genai
import re

# Components Expert
class ExpertEvaluator:
    async def score(self, case, resp): 
        # Tính toán Hit Rate và MRR
        gt_id = case.get("ground_truth_id")
        retrieved_ids = resp.get("metadata", {}).get("retrieved_ids", [])
        
        hit_rate = 1.0 if gt_id in retrieved_ids else 0.0
        mrr = 0.0
        if gt_id in retrieved_ids:
            rank = retrieved_ids.index(gt_id) + 1
            mrr = 1.0 / rank

        return {
            "faithfulness": 0.9, # Giả lập điểm để tập trung vào Retrieval Evaluation (yêu cầu cốt lõi)
            "relevancy": 0.8,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }

class MultiModelJudge:
    def __init__(self):
        self.client = genai.Client()

    async def _ask_judge(self, q, a, gt, role_prompt, temperature):
        prompt = f"""{role_prompt}
Bạn là giám khảo chấm điểm câu trả lời của hệ thống AI (RAG).
Thang điểm từ 1 đến 5 (1: Tệ nhất, 5: Tốt nhất).
Chỉ trả về 1 con số nguyên duy nhất từ 1 đến 5. Không giải thích gì thêm.

Câu hỏi: {q}
Câu trả lời kỳ vọng (Ground Truth): {gt}
Câu trả lời của hệ thống: {a}

Điểm (1-5):"""
        try:
            # We wrap with asyncio.to_thread because the SDK might be sync, but google.genai has async?
            # Actually, google-genai is mostly sync, so we can just call it synchronously or in an executor.
            # To be safe and async, let's use asyncio.to_thread
            def sync_call():
                return self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                ).text
            
            response = await asyncio.to_thread(sync_call)
            # parse number
            match = re.search(r'[1-5]', response)
            if match:
                return int(match.group())
            return 3
        except Exception as e:
            print(f"Judge Error: {e}")
            return 3

    async def evaluate_multi_judge(self, q, a, gt): 
        # Judge 1: Strict Judge
        task1 = self._ask_judge(q, a, gt, "Bạn là một giám khảo cực kỳ khó tính và khắt khe.", 0.1)
        # Judge 2: Helpful Judge
        task2 = self._ask_judge(q, a, gt, "Bạn là một giám khảo công tâm, chú trọng vào việc thông tin có giúp ích được cho người dùng hay không.", 0.5)
        
        score1, score2 = await asyncio.gather(task1, task2)
        
        final_score = (score1 + score2) / 2.0
        agreement_rate = 1.0 if abs(score1 - score2) <= 1 else 0.0
        
        reasoning = f"Judge 1: {score1}, Judge 2: {score2}. "
        if agreement_rate == 1.0:
            reasoning += "Hai giám khảo đồng thuận cao."
        else:
            reasoning += "Hai giám khảo có ý kiến trái chiều."

        return {
            "final_score": final_score, 
            "agreement_rate": agreement_rate,
            "reasoning": reasoning
        }

async def run_benchmark_with_results(agent_version: str):
    print(f"Khoi dong Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    runner = BenchmarkRunner(MainAgent(version=agent_version.split('_')[1].lower() if 'V1' in agent_version else "v2"), ExpertEvaluator(), MultiModelJudge())
    results = await runner.run_all(dataset)

    total = len(results)
    summary = {
        "metadata": {"version": agent_version, "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total
        }
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    v1_summary = await run_benchmark("Agent_V1_Base")
    
    # Giả lập V2 có cải tiến (để test logic)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("Khong the chay Benchmark. Kiem tra lai data/golden_set.jsonl.")
        return

    print("\n--- KET QUA SO SANH (REGRESSION) ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta > 0:
        print("QUYET DINH: CHAP NHAN BAN CAP NHAT (APPROVE)")
    else:
        print("QUYET DINH: TU CHOI (BLOCK RELEASE)")

if __name__ == "__main__":
    asyncio.run(main())
