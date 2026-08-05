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

## 2. Chạy toàn bộ bài

Chạy test trước, sau đó chạy pipeline:

```powershell
python -m unittest discover -s tests -v
python -m ec_dispute.main --run-all
```

`--run-all` xóa các `output/EC_*.json` cũ, truncate trace cũ, xử lý 50 case,
chỉ ghi output sau khi verifier pass và tạo metadata của lần chạy mới nhất.

Kiểm tra số file và nội dung ZIP trước khi nộp:

```powershell
(Get-ChildItem output -Filter "EC_*.json").Count
Compress-Archive -Path output\EC_*.json -DestinationPath output.zip -Force
tar -tf output.zip
```

ZIP chỉ dùng để nộp, không commit `output.zip` vào repository.

## 3. Mốc kiểm chứng

```text
canceled_order_paid       8
unavailable_order_paid    6
late_delivery_seller     10
late_delivery_logistics  10
valid_split_payment       8
unsupported_late_claim    8
```

## 4. Quy tắc commit đề xuất

```text
feat: xây dựng giải pháp multi-agent xử lý khiếu nại Olist
test: bổ sung kiểm thử chính sách và 50 trường hợp đầu vào
docs: hoàn thiện kiến trúc và báo cáo cá nhân
data: cập nhật output và nhật ký của lần chạy đã kiểm chứng
```

Trước mỗi commit:

```powershell
git status --short
git diff
python -m unittest discover -s tests -v
git diff --cached
```

Không commit `.env`, API key, `.idea`, `.venv` hoặc `output.zip`.
