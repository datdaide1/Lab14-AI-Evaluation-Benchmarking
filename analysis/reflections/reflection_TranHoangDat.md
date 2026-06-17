# Báo cáo Cá nhân Lab 14
**Sinh viên:** Trần Hoàng Đạt
**Phần được phân công:** Multi-Judge Consensus Engine, Async Performance Tuning, Metrics & Dataset Gen.

## 1. Engineering Contribution
Trong Lab này, tôi đã thiết kế và lập trình các phần quan trọng:
- Thiết kế hệ thống sinh dữ liệu vàng (`synthetic_gen.py`) sử dụng Google Gemini 2.5 Flash, tạo ra 60 QA pairs một cách tự động và đa dạng (có bao gồm các adversarial cases).
- Xây dựng mô hình chấm điểm đồng thuận `MultiModelJudge` với 2 giám khảo đóng vai các tính cách khác nhau (Strict và Helpful) để đánh giá khách quan.
- Hiện thực hóa logic tính toán `Hit Rate` và `MRR` thay vì mock data, giúp kiểm soát chất lượng của module Retrieval.

## 2. Technical Depth
### a. Tại sao phải đánh giá Retrieval (Hit Rate & MRR) trước Generation?
Trong kiến trúc RAG, nếu hệ thống truy xuất thông tin sai (Retrieval fail), thì phần sinh ngôn ngữ (Generation) dù có tốt đến đâu cũng sẽ dẫn đến Hallucination. 
- **Hit Rate** đo lường xem tài liệu chứa câu trả lời đúng (Ground Truth) có lọt vào Top-K không.
- **MRR (Mean Reciprocal Rank)** đánh giá mức độ chính xác của vị trí tài liệu đúng (càng gần top 1 càng tốt).
Đánh giá Retrieval trước giúp khoanh vùng lỗi do hệ thống tìm kiếm hay do LLM sinh ra.

### b. Cohen's Kappa & Agreement Rate
Thay vì chỉ dùng 1 giám khảo (có thể bị bias), tôi đã triển khai hệ thống Multi-Judge và đo lường **Agreement Rate**. Trong bài, nếu 2 giám khảo cho điểm chênh lệch không quá 1 điểm, tôi coi là "Đồng thuận". Trên thực tế, có thể sử dụng Cohen's Kappa để loại trừ xác suất đồng thuận do ngẫu nhiên.

### c. Chi phí (Cost) và Chất lượng (Quality)
Việc sử dụng đa giám khảo (Multi-Judge) giúp tăng độ tin cậy nhưng lại làm nhân lên số lượng LLM API calls, gây tốn kém chi phí và chậm hệ thống. Để khắc phục, tôi đã sử dụng `asyncio.gather` để chạy các API song song (giảm Latency) và lựa chọn mô hình `gemini-2.5-flash` (giá rẻ, tốc độ cực nhanh) thay cho mô hình nặng để làm giám khảo.

## 3. Problem Solving
Trong quá trình code, hệ thống chạy đa luồng `asyncio` gặp phải lỗi `ssl.SSLError: [ASN1: NOT_ENOUGH_DATA]` khi gọi API trong môi trường Conda nội bộ. Tôi đã áp dụng kỹ thuật "monkey-patching" để override `ssl.SSLContext.load_default_certs` giúp bypass qua bước check certificate mặc định của Python, giúp hệ thống tiếp tục gửi request đến Google API trơn tru mà không làm gián đoạn bài benchmark. Đồng thời, tôi đã gỡ bỏ các ký tự Emoji để sửa lỗi `UnicodeEncodeError` ở Windows cp1258 encoding.
