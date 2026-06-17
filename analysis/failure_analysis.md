# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 60
- **Tỉ lệ Pass/Fail:** 55/5 (Tỉ lệ Pass 91.6%)
- **Điểm RAGAS trung bình:**
    - Faithfulness: 0.90
    - Relevancy: 0.80
    - Hit Rate: 1.0 (Do sử dụng chiến lược mapping tài liệu chuẩn xác)
    - MRR: 1.0
- **Điểm LLM-Judge trung bình:** 4.7 / 5.0 (Cho Agent_V2_Optimized)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Hallucination | 2 | Do câu hỏi có tính chất gài bẫy (adversarial), mô hình LLM đôi khi vẫn cố gắng trả lời vượt ngoài context hoặc sinh ra thông tin dựa trên kiến thức nền. |
| Incomplete | 2 | Câu hỏi yêu cầu tổng hợp từ nhiều nguồn khác nhau, nhưng Retrieval chỉ trả về top-K dẫn đến thiếu ý. |
| Strict formatting | 1 | Giám khảo khó tính (Judge 1) trừ điểm vì câu trả lời dài dòng hơn mức cần thiết, không đi thẳng vào vấn đề theo yêu cầu. |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Lỗi Hallucination khi gặp câu hỏi Adversarial
1. **Symptom:** Agent bị trừ điểm nặng vì cung cấp thông tin không có trong tài liệu quy định thư viện.
2. **Why 1:** LLM đã trả lời dựa trên kiến thức nền thay vì chỉ dựa vào Context.
3. **Why 2:** Prompt không đủ mạnh để ép LLM từ chối trả lời (fallback) khi thông tin không có trong context.
4. **Why 3:** LLM vẫn tìm thấy một số từ khóa trùng khớp (ví dụ: mượn sách) nên lầm tưởng context có đủ thông tin.
5. **Why 4:** Câu hỏi cố tình chèn thêm thông tin sai lệch về "Thẻ VIP thư viện".
6. **Root Cause:** Thiếu cơ chế xử lý câu hỏi lừa (Adversarial Guardrail) trong Generation Prompt.

### Case #2: Thiếu thông tin (Incomplete)
1. **Symptom:** Câu trả lời không liệt kê đủ 3 hình thức đóng học phí.
2. **Why 1:** LLM chỉ trích xuất hình thức chuyển khoản và quét mã, bỏ sót quẹt thẻ tín dụng.
3. **Why 2:** Độ dài của câu trả lời bị giới hạn hoặc LLM hiểu sai mức độ chi tiết cần thiết.
4. **Why 3:** Prompt không quy định rõ "Hãy liệt kê toàn bộ".
5. **Why 4:** System prompt cũ quá sơ sài.
6. **Root Cause:** Kỹ thuật Prompt Engineering chưa tối ưu cho các câu hỏi yêu cầu liệt kê đa mục.

### Case #3: Bất đồng quan điểm giữa 2 Judge (Conflict)
1. **Symptom:** Judge 1 chấm 2 điểm, Judge 2 chấm 5 điểm, dẫn đến điểm trung bình 3.5.
2. **Why 1:** Judge 1 đóng vai trò "khắt khe" yêu cầu câu trả lời phải có format cụ thể.
3. **Why 2:** Agent V1 sinh ra câu trả lời chứa nhiều từ nối không cần thiết ("Dựa trên tài liệu hệ thống, tôi xin trả lời...").
4. **Why 3:** Chưa có bước làm sạch hoặc tối ưu hóa luồng trả lời trước khi gửi cho user.
5. **Why 4:** (Đã được khắc phục trong Agent V2 bằng cách rút gọn prompt).
6. **Root Cause:** Format trả lời của Agent V1 quá rườm rà, vi phạm tiêu chí về sự súc tích.

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Nâng cấp Agent lên Version 2 với System Prompt tối ưu hơn ("Tuyệt đối không bịa đặt thông tin. Ngắn gọn, đi thẳng vấn đề.").
- [ ] Thêm Guardrails để nhận diện và từ chối xử lý các câu hỏi Adversarial.
- [ ] Cải thiện kỹ thuật Retrieval bằng Hybrid Search (kết hợp BM25 và Vector Embeddings) để xử lý các câu hỏi yêu cầu tổng hợp thông tin từ nhiều context khác nhau.
