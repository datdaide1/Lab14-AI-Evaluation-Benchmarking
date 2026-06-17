import json
import asyncio
import os
import ssl

def _patched_load_default_certs(*args, **kwargs):
    pass
ssl.SSLContext.load_default_certs = _patched_load_default_certs

from typing import List, Dict
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

async def generate_qa_from_text(text: str, context_id: str, num_pairs: int = 10) -> List[Dict]:
    """
    Sử dụng Gemini API để tạo các cặp (Question, Expected Answer, Context)
    từ đoạn văn bản cho trước.
    """
    print(f"Generating QA pairs for context: {context_id}...")
    client = genai.Client()
    
    prompt = f"""
    Bạn là một chuyên gia tạo dữ liệu đánh giá hệ thống RAG.
    Dựa vào đoạn văn bản (Context) dưới đây, hãy tạo ra đúng {num_pairs} test cases.
    Mỗi test case phải bao gồm:
    - question: Câu hỏi có thể được trả lời từ văn bản. Thêm một số câu hỏi khó, yêu cầu suy luận hoặc có một số từ khóa gây nhiễu (adversarial).
    - expected_answer: Câu trả lời ngắn gọn, chính xác dựa trên văn bản.
    - difficulty: Mức độ khó ('easy', 'medium', 'hard'). Cần ít nhất 2 câu 'hard'.
    - type: Phân loại câu hỏi ('fact-check', 'inference', 'adversarial').
    
    Đoạn văn bản (Context):
    {text}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={"type": "array", "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "expected_answer": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["question", "expected_answer", "difficulty", "type"]
            }}
        ),
    )
    
    try:
        data = json.loads(response.text)
        results = []
        for item in data:
            results.append({
                "question": item["question"],
                "expected_answer": item["expected_answer"],
                "context": text,
                "ground_truth_id": context_id,
                "metadata": {
                    "difficulty": item["difficulty"],
                    "type": item["type"]
                }
            })
        return results
    except Exception as e:
        print(f"Error parsing JSON for {context_id}: {e}")
        return []

async def main():
    contexts = {
        "doc_1": "Quy định Đào tạo: Sinh viên VinUni đăng ký tín chỉ vào đầu mỗi học kỳ qua hệ thống SIS. Thời hạn hủy môn không ghi nhận điểm F là tuần thứ 4 của học kỳ. Sinh viên muốn bảo lưu kết quả học tập phải nộp đơn lên Phòng Đào tạo ít nhất 2 tuần trước kỳ thi cuối kỳ và chỉ được bảo lưu tối đa 2 học kỳ liên tiếp. Sinh viên cần hoàn thành ít nhất 120 tín chỉ để tốt nghiệp.",
        "doc_2": "Quy định IT: Để reset mật khẩu email sinh viên, hãy truy cập portal.vinuni.edu.vn và chọn 'Forgot Password', sau đó nhập mã OTP gửi về số điện thoại đăng ký. Mạng wifi 'eduroam' dành cho giảng viên và sinh viên, yêu cầu đăng nhập bằng tài khoản email trường. Mỗi sinh viên được cấp 1TB dung lượng lưu trữ trên OneDrive. Việc chia sẻ tài khoản IT cho người ngoài là vi phạm nội quy nghiêm trọng.",
        "doc_3": "Quy định Ký túc xá: Ký túc xá đóng cửa vào lúc 11:30 PM mỗi ngày. Sinh viên về muộn phải điền form giải trình tại phòng bảo vệ. Việc đăng ký khách qua đêm (bạn bè, người thân) bị cấm hoàn toàn vì lý do an ninh. Các hành vi sử dụng bếp điện cá nhân, nấu ăn trong phòng sẽ bị lập biên bản, tịch thu thiết bị và phạt 500,000 VNĐ cho lần vi phạm đầu tiên.",
        "doc_4": "Thông tin Thư viện: Thư viện mở cửa 24/7. Sinh viên được mượn tối đa 10 cuốn sách trong 14 ngày. Có thể gia hạn mượn sách tối đa 1 lần (thêm 7 ngày) qua cổng thông tin thư viện trực tuyến nếu sách đó chưa có ai đặt trước. Để truy cập các cơ sở dữ liệu số như IEEE, ProQuest khi ở ngoài khuôn viên trường, sinh viên phải dùng VPN của VinUni. Trả sách trễ hạn sẽ bị phạt 10,000 VNĐ/ngày/cuốn.",
        "doc_5": "Quy định Tài chính: Học phí được thu thành 2 đợt mỗi năm, vào tháng 8 và tháng 1. Sinh viên có thể đóng học phí qua hình thức chuyển khoản ngân hàng, quét mã VNPAY hoặc quẹt thẻ tín dụng tại phòng kế toán. Nếu nộp trễ quá 15 ngày so với hạn chót, sinh viên sẽ phải chịu phí phạt 0.5% số tiền nợ cho mỗi tuần trễ. Nếu nợ học phí quá 30 ngày, tài khoản sinh viên sẽ bị khóa và không thể đăng ký môn học tiếp theo.",
        "doc_6": "Hướng dẫn y tế: Phòng y tế trực 24/7 nằm tại tầng 1 tòa nhà G. Để khám chữa bệnh, sinh viên mang thẻ sinh viên đến quầy lễ tân y tế. Để yêu cầu bảo hiểm y tế hoàn tiền cho các hóa đơn khám ngoài, sinh viên cần nộp bản gốc hóa đơn đỏ và giấy khám bệnh tại phòng Dịch vụ Sinh viên trong vòng 30 ngày kể từ ngày khám. Trong trường hợp khẩn cấp, gọi hotline an ninh 0912-345-678 hoặc hotline y tế 0912-876-543."
    }
    
    all_qa_pairs = []
    
    # We run them concurrently to save time
    tasks = []
    for cid, text in contexts.items():
        tasks.append(generate_qa_from_text(text, cid, num_pairs=10))
        
    results = await asyncio.gather(*tasks)
    
    for res in results:
        all_qa_pairs.extend(res)
    
    print(f"Generated a total of {len(all_qa_pairs)} QA pairs.")
    
    # Save to data/golden_set.jsonl
    os.makedirs("data", exist_ok=True)
    with open("data/golden_set.jsonl", "w", encoding="utf-8") as f:
        for pair in all_qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print("Done! Saved to data/golden_set.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
