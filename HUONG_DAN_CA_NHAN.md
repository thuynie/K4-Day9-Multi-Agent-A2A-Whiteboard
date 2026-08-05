# Hướng dẫn làm bài trên nhánh cá nhân

## 1. Chuẩn bị và chạy bộ khung

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ec_dispute.main --check-data
python -m ec_dispute.main --inspect-case EC_002
python -m unittest discover -s tests -v
```

Nếu chưa cài package editable, có thể chạy tạm bằng:

```powershell
$env:PYTHONPATH = "src"
python -m ec_dispute.main --check-data
python -m unittest discover -s tests -v
```

## 2. Thứ tự hoàn thiện

1. Mở rộng Delivery Agent để xuất `seller_handoff_analysis` cho từng seller.
2. Xây secondary issues và resolution actions theo đúng thứ tự README.
3. Xây output builder đủ toàn bộ schema.
4. Xây evidence builder chỉ dùng ID whitelist.
5. Mở rộng Verifier để tái tính mọi field quan trọng và kiểm tra array limit.
6. Tích hợp TraceWriter, tạo `metadata.json` và lệnh `--run-all`.
7. Chỉ ghi output khi verifier pass.
8. Thêm unit/integration tests, chạy 50 case và hoàn thiện báo cáo cá nhân.

## 3. Mốc kiểm chứng

```text
canceled_order_paid       8
unavailable_order_paid    6
late_delivery_seller     10
late_delivery_logistics  10
valid_split_payment       8
unsupported_late_claim    8
```

## 4. Quy tắc commit

```text
chore: cấu hình bộ khung dự án cá nhân
feat: xây dựng tầng truy xuất dữ liệu Olist
feat: triển khai các tác nhân phân tích domain
feat: áp dụng chính sách EC_POLICY_V2
feat: bổ sung verifier và sinh output cho 50 case
test: kiểm chứng policy và toàn bộ output
docs: hoàn thiện kiến trúc và báo cáo cá nhân
```

Trước mỗi commit:

```powershell
git status --short
git diff
python -m unittest discover -s tests -v
git diff --cached
```

Không commit `.env`, API key, `.idea`, `.venv` hoặc `output.zip`.
