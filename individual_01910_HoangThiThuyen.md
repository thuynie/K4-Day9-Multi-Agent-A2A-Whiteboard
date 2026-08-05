# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung |
| --------------- | ------------ |
| Họ và tên       | Hoàng Thị Thuyên |
| MSSV            | 2A202601910 |
| Khóa/Lớp        | K4 |
| Vai trò chính   | Leader / Core Multi-Agent Engineer |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | ----------------- | ------------------------------------- |
| Data Extraction & Context Agent | `data_loader.py` (`OlistDataLoader`) | `claimed_order_id`, 9 CSV Olist | `CaseContext` dict | Hoàn thành |
| Delivery & Financial Analytics Agent | `analytics.py` (`CaseAnalytics`) | `CaseContext` dict | `delivery_analysis`, `payment_reconciliation` | Hoàn thành |
| Groq LLM Inference Agent | `llm_agent.py` (`GroqLLMAgent`) | Customer Message, Case Facts | LLM Reasoning completion | Hoàn thành |
| Business Policy Rules Engine Agent | `policy_engine.py` (`PolicyEngine`) | `CaseContext`, Analytics outputs | `policy_evaluation` dict | Hoàn thành |
| Verifier & Output Builder Agent | `verifier.py` (`VerifierAgent`) | All Agent Outputs | Compliant Output JSON | Hoàn thành |
| Multi-Agent Pipeline & Release | `run_pipeline.py`, `architecture.md`, `logging/metadata.json` | 50 Input JSONs | `output/*.json`, `logging/trace.jsonl` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------- | ----------------------------- | ----------------------- |
| Hướng dẫn tích hợp LLM & Git branch | Toàn nhóm (Dũng, Trung) | Khởi tạo 3 nhánh Git độc lập và tích hợp Groq API Key trong `.env` |
| Audit Schema & Limit Validation | Mọi module đầu ra | Đảm bảo 100% 50 file JSON tuân thủ các giới hạn mảng (max limits) và kiểu dữ liệu |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ------------------------- | --------------- |
| Xây dựng Data Extraction Layer | `data_loader.py` | Nạp 9 CSV, trích xuất chuẩn context order & lịch sử khách | `python data_loader.py` |
| Xây dựng Analytics Layer | `analytics.py` | Tính độ lệch giờ giao hàng & đối soát tiền hàng + freight | `python analytics.py` |
| Xây dựng Groq LLM Agent Layer | `llm_agent.py` | Gửi prompt phân tích khiếu nại tới LLM Groq (`llama-3.1-8b-instant`) | `python llm_agent.py` |
| Cài đặt Quy tắc Nghiệp vụ `EC_POLICY_V2` | `policy_engine.py` | Đánh giá chính xác Primary/Secondary issues, refund & actions | `python policy_engine.py` |
| Tự động hóa Pipeline 50 Cases | `run_pipeline.py` | Sinh ra 50 file JSON trong `output/` & log `logging/trace.jsonl` | `python run_pipeline.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

- **Artifact bàn giao:** 50 file JSON kết quả trong thư mục `output/` (từ `EC_001.json` đến `EC_050.json`), file nhật ký thực thi Multi-Agent `logging/trace.jsonl` ghi vết 50 trường hợp (bao gồm LLM reasoning), file khai báo model `logging/metadata.json` và sơ đồ kiến trúc hệ thống `architecture.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Xây dựng hệ thống Multi-Agent tích hợp LLM thật (Model $\le 10\text{B}$ parameters) tự động hóa việc điều tra, đối soát dữ liệu và ra quyết định xử lý 50 khiếu nại thương mại điện tử Olist theo bộ quy tắc `EC_POLICY_V2`, đảm bảo tính chính xác, không tự suy diễn sự kiện không tồn tại và tuân thủ các ràng buộc schema khắt khe.

### Cách triển khai

1. **`data_loader.py`**: Trích xuất dữ liệu từ 9 bảng CSV Olist, join giữa `orders`, `customers`, `order_items`, `order_payments`, `products` và bảng dịch danh mục tiếng Anh. Tìm `customer_unique_id` để lấy danh sách `related_order_ids` của khách.
2. **`analytics.py`**: Tính toán `delivery_variance_hours` và `handoff_variance_hours` (cho từng seller) bằng `datetime.strptime`. Tính tổng `item_total_brl`, `freight_total_brl`, `expected_total_brl`, `payment_total_brl` và gán `reconciled = abs(difference_brl) <= 0.10`.
3. **`llm_agent.py`**: Khởi tạo `GroqLLMAgent` gọi tới Groq API Endpoint với model `llama-3.1-8b-instant` (8B params), gửi tin nhắn khiếu nại của khách hàng cùng dữ liệu thô để LLM phân tích lập luận.
4. **`policy_engine.py`**: Xếp loại `primary_issue` theo 6 bậc ưu tiên khắt khe (`canceled_order_paid`, `unavailable_order_paid`, `late_delivery_seller`, `late_delivery_logistics`, `valid_split_payment`, `unsupported_late_claim`). Thêm các `secondary_issues` theo thứ tự quy định. Tạo danh sách `resolution_actions` và `evidence_ids`.
5. **`verifier.py`**: Đóng gói đối tượng JSON cuối cùng, loại bỏ trùng lặp, áp dụng giới hạn max limit cho các mảng (order_ids <= 5, item_ids <= 5, seller_ids <= 3, payment_ids <= 5, evidence_ids <= 20, v.v.), làm tròn số 2 chữ số thập phân (`round(x, 2)`).

### Input, output và contract

| Thành phần | Mô tả |
| ----------------------- | -------------------------------------- |
| Input | 50 file `input/EC_xxx.json`, 9 file CSV Olist trong `data/`, API Key trong `.env` |
| Output | 50 file `output/EC_xxx.json` tuân thủ Schema đề bài, `logging/trace.jsonl`, `logging/metadata.json`, `architecture.md` |
| Module phụ thuộc | `pandas`, `datetime`, `json`, `urllib.request`, `glob`, `os` |
| Module sử dụng output | Giám khảo / Hệ thống chấm điểm tự động |
| Điều kiện lỗi cần xử lý | Đơn không có item (canceled/unavailable): gán các trường tài chính là `null`, mảng item/seller/product để rỗng `[]` |

### Cách xác minh

```bash
python run_pipeline.py
```

- **Kết quả mong đợi:** Xử lý thành công toàn bộ 50 case, sinh đủ 50 file JSON trong `output/` và ghi vết LLM reasoning trong `logging/trace.jsonl`.
- **Kết quả thực tế:** Hệ thống chạy thành công 50/50 cases mà không gặp bất kỳ ngoại lệ (exception) nào.
- **Artifact/log:** `output/EC_001.json` -> `output/EC_050.json`, `logging/trace.jsonl`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Tích hợp LLM thực tế vào Multi-Agent Pipeline mà vẫn đảm bảo 100% tiêu chuẩn format JSON và tốc độ chạy.
- **Các phương án đã cân nhắc:** 
  1. Cho LLM trực tiếp tạo ra toàn bộ JSON đầu ra (Dễ bị ảo giác / sai schema / vỡ mảng max limit).
  2. Kết hợp LLM Agent phân tích lập luận + Policy Engine & Verifier Agent chuẩn hóa dữ liệu đầu ra.
- **Phương án đã chọn:** Phương án 2 (Multi-Agent Hybrid Architecture).
- **Lý do:** Đảm bảo hệ thống sử dụng LLM thật suy luận tự nhiên, nhưng vẫn giữ được độ chính xác tuyệt đối 100% theo tiêu chuẩn chấm thi tự động.
- **Bằng chứng quyết định phù hợp:** File `logging/trace.jsonl` ghi nhận cả LLM Agent completion và kết quả phân tích chuẩn xác.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'NoneType'` khi tính chênh lệch thời gian giao hàng.
- **Lệnh hoặc bước tái hiện:** `python analytics.py` với đơn hàng bị hủy chưa có ngày giao thực tế (`order_delivered_customer_date` là NaN/None).
- **Nguyên nhân gốc:** Cột `order_delivered_customer_date` trong CSV có giá trị NaN do đơn bị hủy trước khi giao.
- **Cách xử lý:** Viết hàm trợ giúp `parse_dt()` kiểm tra `None`/`NaN` và hàm `calc_hours_diff()` trả về `None` an toàn nếu thiếu mốc thời gian.
- **Cách xác minh sau khi sửa:** Chạy `python run_pipeline.py` mượt mà cho cả 50 cases mà không bị sập chương trình.
- **Điều học được:** Luôn phải kiểm tra tính khả dụng của dữ liệu thời gian (null safety) trước khi thực hiện phép toán datetime.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Luồng dữ liệu trong hệ thống Multi-Agent Dispute Resolution:** Dữ liệu khiếu nại đầu vào từ khách hàng (`claimed_order_id`) được Coordinator tiếp nhận, chuyển qua Data Agents để join với 9 CSV Olist. Dữ liệu thô sau đó được gửi đến LLM Agent (`llama-3.1-8b-instant`) để phân tích tin nhắn khiếu nại, đồng thời Analytics Agents tính toán chênh lệch thời gian và tài chính, trước khi Policy Agent áp dụng bộ luật `EC_POLICY_V2` đưa ra quyết định xử lý.
2. **Vai trò của Verifier Agent:** Verifier đóng vai trò kiểm soát chất lượng (QA), tự động audit toàn bộ dữ liệu trước khi xuất file: ép kiểu dữ liệu, cắt tỉa mảng quá độ dài quy định (max limits), làm tròn tiền tệ và kiểm tra tính hợp lệ của Evidence IDs.
3. **Ý nghĩa của `logging/trace.jsonl`:** File nhật ký kiểm toán (Audit Trail) ghi lại từng bước suy luận của LLM Agent, quyết định issue và hành động của Agent cho từng case, giúp đảm bảo tính minh bạch và khả năng tái hiện (reproducibility).
4. **Phân biệt `case_status` (`action_required` vs `no_action`):** Trạng thái `action_required` được gán khi có khoản hoàn tiền (`recommended_refund_brl > 0`). Trạng thái `no_action` được gán khi không phát sinh khoản hoàn (chỉ giải thích hoặc từ chối khiếu nại).
5. **Tiêu chí đánh giá bài tập Multi-Agent:** Điểm số được tính dựa trên tổng có trọng số của 7 thành phần (Issues, Affected Entities, Context, Delivery Analysis, Payment Reconciliation, Root Cause & Evidence, Financial Resolution & Actions) trên trung bình 50 cases.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Thị Thuyên  
**Ngày xác nhận:** 2026-08-05
