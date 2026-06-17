import asyncio
import json
import os
import ssl

def _patched_load_default_certs(*args, **kwargs):
    pass
ssl.SSLContext.load_default_certs = _patched_load_default_certs

from typing import List, Dict
from dotenv import load_dotenv
from google import genai

load_dotenv()

class MainAgent:
    """
    RAG Agent version cơ bản.
    """
    def __init__(self, version: str = "v1"):
        self.name = f"SupportAgent-{version}"
        self.version = version
        self.client = genai.Client()
        self.knowledge_base = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Tải dữ liệu từ golden set để làm knowledge base mô phỏng."""
        if os.path.exists("data/golden_set.jsonl"):
            with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        case = json.loads(line)
                        # Lưu context duy nhất
                        if not any(kb["id"] == case["ground_truth_id"] for kb in self.knowledge_base):
                            self.knowledge_base.append({
                                "id": case["ground_truth_id"],
                                "content": case["context"]
                            })

    def _retrieve(self, question: str) -> List[Dict]:
        """Simple retrieval function: count matching words (BM25 mô phỏng)."""
        q_words = set(question.lower().split())
        scored = []
        for doc in self.knowledge_base:
            d_words = set(doc["content"].lower().split())
            score = len(q_words.intersection(d_words))
            scored.append((score, doc))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        # Giả lập trả về top 2
        return [doc for score, doc in scored[:2]]

    async def query(self, question: str) -> Dict:
        """
        Quy trình RAG: Retrieval + Generation
        """
        # 1. Retrieval
        retrieved_docs = self._retrieve(question)
        contexts = [doc["content"] for doc in retrieved_docs]
        retrieved_ids = [doc["id"] for doc in retrieved_docs]
        
        context_str = "\n\n".join(contexts)
        
        # 2. Generation
        if self.version == "v1":
            prompt = f"Trả lời câu hỏi dựa trên ngữ cảnh sau. Nếu không biết, hãy nói không biết.\n\nNgữ cảnh:\n{context_str}\n\nCâu hỏi: {question}"
        else:
            # v2 tối ưu hơn (Tối ưu prompt để tránh Hallucination và dài dòng)
            prompt = f"""Bạn là một trợ lý AI đáng tin cậy. Nhiệm vụ của bạn là trả lời câu hỏi CHỈ DỰA VÀO phần Ngữ cảnh được cung cấp.
Tuyệt đối không bịa đặt thông tin. Câu trả lời cần ngắn gọn, đi thẳng vào vấn đề.

Ngữ cảnh:
{context_str}

Câu hỏi: {question}"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            answer = response.text
        except Exception as e:
            answer = f"Error calling LLM: {e}"

        return {
            "answer": answer,
            "contexts": contexts,
            "metadata": {
                "model": "gemini-2.5-flash",
                "retrieved_ids": retrieved_ids,
                "version": self.version
            }
        }

if __name__ == "__main__":
    agent = MainAgent("v2")
    async def test():
        resp = await agent.query("Khi nào thì hết hạn hủy môn?")
        print(resp)
    asyncio.run(test())
