# Báo cáo cá nhân — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin | Nội dung                                                  |
|---|-----------------------------------------------------------|
| Họ và tên | Dương Tiến Dũng                                           |
| MSSV | 2A202602020                                               |
| Khóa/Lớp | K4                                                        |
| Vai trò chính | Phát triển giải pháp multi-agent deterministic end-to-end |
| Ngày hoàn thành | 2026-08-05                                                |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Data Repository | `src/ec_dispute/data_repository.py` | 9 CSV Olist và 50 input JSON | Các index lookup read-only | Hoàn thành |
| Domain Agents | `src/ec_dispute/agents/` | Claimed order và domain rows | Customer, order/product, payment, delivery facts | Hoàn thành |
| Policy Engine | `src/ec_dispute/policies/ec_policy_v2.py` | Structured facts | Primary issue, root cause, responsibility, refund | Hoàn thành |
| Coordinator và output | `orchestrator.py`, `output_builder.py` | Case input và agent handoff | Output đúng schema đề bài | Hoàn thành |
| Verifier | `src/ec_dispute/agents/verifier_agent.py` | Draft output và repository | Danh sách lỗi hoặc xác nhận hợp lệ | Hoàn thành |
| Observability | `src/ec_dispute/observability/` | Run/case events | `trace.jsonl`, `metadata.json` | Hoàn thành |
| Kiểm thử | `tests/` | Source và dữ liệu thật | Unit/integration test | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Chuẩn hóa tài liệu | Nhóm tích hợp | `architecture.md` mô tả agent, quyền đọc và handoff |
| Chuẩn hóa quy trình Git | Nhóm tích hợp | `HUONG_DAN_CA_NHAN.md` có lệnh chạy và quy tắc commit |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Kiểm tra input và khóa join | `DataRepository.validate_sources` | 50/50 claimed order tồn tại | `python -m ec_dispute.main --check-data` |
| Áp dụng policy | `ec_policy_v2.decide` | Đủ sáu primary issue đúng priority | `python -m unittest discover -s tests -v` |
| Sinh output | `OutputBuilder.build` | 50 JSON từ EC_001 đến EC_050 | `python -m ec_dispute.main --run-all` |
| Kiểm chứng output | `VerifierAgent.verify_draft` | 50 thành công, 0 thất bại | `logging/metadata.json` |
| Ghi handoff | `TraceWriter.write` | Trace JSONL của lần chạy mới nhất | `logging/trace.jsonl` |

Artifact cụ thể là `output/EC_002.json`: case được phân loại
`late_delivery_seller`, tổng payment 212.27 BRL, delivery variance 87.39 giờ,
refund freight 18.27 BRL và evidence seller/policy có thể đối chiếu trực tiếp.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline phải đối chiếu một order qua nhiều bảng có quan hệ one-to-many mà không
làm nhân bản item/payment, tìm đúng lịch sử khách hàng, tính tiền và timestamp
chính xác, sau đó áp dụng policy theo priority và chỉ xuất evidence tồn tại.

### Cách triển khai

Repository nạp CSV một lần và tạo index theo `order_id`, `customer_id`,
`customer_unique_id`, `product_id` và `seller_id`. Các agent chỉ nhận phần dữ liệu
thuộc domain. Tiền dùng `Decimal` và làm tròn hai chữ số; timestamp so sánh trực
tiếp không đổi múi giờ. Delivery Agent nhóm item theo seller, lấy shipping limit
sớm nhất của seller rồi so với carrier handoff. Policy Agent chạy chuỗi điều kiện
theo đúng thứ tự `EC_POLICY_V2`. Output Builder giữ thứ tự nguồn và giới hạn mảng.
Verifier kiểm tra ID, evidence, null handling, số tiền, refund/status và giới hạn
trước khi Coordinator ghi file.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `input/EC_XXX.json`, 9 CSV trong `data/` |
| Output | `output/EC_XXX.json` đúng schema README |
| Module phụ thuộc | `DataRepository`, domain agents, `ec_policy_v2` |
| Module sử dụng output | Verifier, CLI và quy trình chấm bài |
| Điều kiện lỗi cần xử lý | Order thiếu, item rỗng, timestamp null, split payment, nhiều seller, evidence sai, vượt array limit |

### Cách xác minh

```powershell
$env:PYTHONPATH = "src"
python -m ec_dispute.main --check-data
python -m unittest discover -s tests -v
python -m ec_dispute.main --run-all
```

- **Kết quả mong đợi:** 50 output hợp lệ, 0 case thất bại.
- **Kết quả thực tế:** 50 thành công, 0 thất bại; toàn bộ test pass.
- **Artifact/log:** `output/`, `logging/trace.jsonl`, `logging/metadata.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Các rule của bài là phép tính và taxonomy cố định, trong khi LLM có thể làm sai số tiền, ID hoặc thứ tự policy.
- **Các phương án đã cân nhắc:** Đưa toàn bộ CSV vào prompt LLM; hoặc dùng agent deterministic trao đổi structured facts và verifier độc lập.
- **Phương án đã chọn:** Multi-agent deterministic bằng Python, contract rõ ràng, policy và verifier bằng code.
- **Lý do:** Tái lập được, không hallucination, không phát sinh chi phí model, dễ kiểm thử và tuân thủ giới hạn model không quá 10B.
- **Bằng chứng:** Chạy lại cùng dữ liệu tạo cùng phân bố 8/6/10/10/8/8 và 50/50 case pass.

## 6. Một lỗi đã xử lý

- **Triệu chứng:** CLI phát sinh `UnicodeEncodeError` khi in tiếng Việt trên PowerShell dùng encoding cp1252.
- **Bước tái hiện:** `$env:PYTHONPATH="src"; python -m ec_dispute.main --check-data`.
- **Nguyên nhân gốc:** `sys.stdout` kế thừa code page không biểu diễn được ký tự tiếng Việt.
- **Cách xử lý:** Cấu hình lại stdout sang UTF-8 trong `main()`.
- **Cách xác minh:** Chạy lại `--check-data` và `--inspect-case EC_002`, nội dung tiếng Việt hiển thị bình thường và exit code bằng 0.
- **Điều học được:** Encoding của source UTF-8 không đảm bảo terminal cũng dùng UTF-8; CLI cần xử lý runtime encoding rõ ràng.

## 7. Hiểu biết về luồng end-to-end

1. Coordinator đọc `claimed_order_id`, repository lookup order rồi các agent lấy customer, item, seller, product, payment và timestamps từ index tương ứng.
2. `customer_id` đại diện cho customer record của một order; phải đổi sang `customer_unique_id` mới tìm được các order khác của cùng người mua.
3. Payment Agent tính `expected_total = sum(price) + sum(freight)`, `difference = payment_total - expected_total` và reconciled khi trị tuyệt đối sai lệch không quá 0.10 BRL. Không nhân payment với installments.
4. Delivery Agent xác định order giao trễ bằng estimated date. Nếu carrier nhận sau shipping limit sớm nhất của ít nhất một seller thì seller chịu trách nhiệm; nếu không thì logistics chịu trách nhiệm.
5. Policy Agent ưu tiên canceled, unavailable, late seller, late logistics, valid split payment rồi unsupported late claim. Vì vậy split payment không lấn át canceled hoặc late delivery.
6. Verifier đối chiếu affected ID với repository, kiểm tra evidence whitelist, null handling, payment consistency, refund/status và giới hạn mảng.
7. Trace ghi các sự kiện case started, handoff completed của từng agent, verification, output written và run completed; nhờ đó có thể chứng minh luồng phối hợp thật.

## 8. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi chỉ ghi kết quả đã được chạy và kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không sao chép báo cáo của thành viên khác.

**Họ và tên:** Dương Tiến Dũng  
**Ngày xác nhận:** 2026-08-05
