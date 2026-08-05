from datetime import datetime
from typing import Dict, Any, List, Optional

def parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    """Chuyển chuỗi YYYY-MM-DD HH:MM:SS thành datetime"""
    if not dt_str or dt_str.lower() == 'none' or dt_str.lower() == 'nan':
        return None
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def calc_hours_diff(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[float]:
    """Tính chênh lệch thời gian dt1 - dt2 tính bằng giờ (làm tròn 2 chữ số thập phân)"""
    if not dt1 or not dt2:
        return None
    diff_seconds = (dt1 - dt2).total_seconds()
    return round(diff_seconds / 3600.0, 2)

class CaseAnalytics:
    @staticmethod
    def analyze_delivery(context: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích thời gian giao hàng & thời gian seller bàn giao hàng"""
        delivered_at_str = context.get("order_delivered_customer_date")
        estimated_at_str = context.get("order_estimated_delivery_date")
        carrier_at_str = context.get("order_delivered_carrier_date")

        dt_delivered = parse_dt(delivered_at_str)
        dt_estimated = parse_dt(estimated_at_str)
        dt_carrier = parse_dt(carrier_at_str)

        # Tính độ lệch thời gian giao hàng (delivery_variance_hours)
        delivery_variance = calc_hours_diff(dt_delivered, dt_estimated)

        # Phân tích theo từng Seller
        items = context.get("items", [])
        seller_handoff_map = {}

        for item in items:
            seller_id = item["seller_id"]
            shipping_limit_str = item["shipping_limit_date"]
            dt_shipping_limit = parse_dt(shipping_limit_str)

            # Nếu 1 seller có nhiều item, lấy shipping_limit_date sớm nhất của seller đó
            if seller_id not in seller_handoff_map:
                seller_handoff_map[seller_id] = dt_shipping_limit
            else:
                if dt_shipping_limit and seller_handoff_map[seller_id]:
                    if dt_shipping_limit < seller_handoff_map[seller_id]:
                        seller_handoff_map[seller_id] = dt_shipping_limit

        seller_handoff_analysis = []
        late_handoff_seller_ids = []

        for seller_id, dt_limit in seller_handoff_map.items():
            handoff_variance = calc_hours_diff(dt_carrier, dt_limit)
            late_handoff = False
            
            # Seller bị muộn nếu carrier nhận hàng sau shipping_limit_date
            if handoff_variance is not None and handoff_variance > 0:
                late_handoff = True
                late_handoff_seller_ids.append(seller_id)

            limit_str = dt_limit.strftime("%Y-%m-%d %H:%M:%S") if dt_limit else None
            seller_handoff_analysis.append({
                "seller_id": seller_id,
                "shipping_limit_at": limit_str,
                "handoff_variance_hours": handoff_variance,
                "late_handoff": late_handoff
            })

        return {
            "delivered_at": delivered_at_str,
            "estimated_delivery_at": estimated_at_str,
            "carrier_handoff_at": carrier_at_str,
            "delivery_variance_hours": delivery_variance,
            "seller_handoff_analysis": seller_handoff_analysis,
            "late_handoff_seller_ids": late_handoff_seller_ids
        }

    @staticmethod
    def reconcile_payments(context: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích và đối soát tài chính thanh toán"""
        items = context.get("items", [])
        payments = context.get("payments", [])

        payment_total = round(sum(p["payment_value"] for p in payments), 2)
        payment_types = sorted(list(set(p["payment_type"] for p in payments)))

        # Nếu order không có item (đơn canceled/unavailable từ đầu)
        if not items:
            return {
                "currency": "BRL",
                "item_total_brl": None,
                "freight_total_brl": None,
                "expected_total_brl": None,
                "payment_total_brl": payment_total,
                "difference_brl": None,
                "reconciled": None,
                "payment_types": payment_types
            }

        # Đơn có sản phẩm
        item_total = round(sum(i["price"] for i in items), 2)
        freight_total = round(sum(i["freight_value"] for i in items), 2)
        expected_total = round(item_total + freight_total, 2)
        difference_brl = round(payment_total - expected_total, 2)
        reconciled = abs(difference_brl) <= 0.10

        return {
            "currency": "BRL",
            "item_total_brl": item_total,
            "freight_total_brl": freight_total,
            "expected_total_brl": expected_total,
            "payment_total_brl": payment_total,
            "difference_brl": difference_brl,
            "reconciled": reconciled,
            "payment_types": payment_types
        }


# --- Đoạn code test thử (chạy trực tiếp file này) ---
if __name__ == "__main__":
    from data_loader import OlistDataLoader
    import json

    loader = OlistDataLoader(data_dir="data")
    test_order_id = "9b75cdaf2d85857ef023980e15d01546" # Case EC_001
    context = loader.get_case_context(test_order_id)

    delivery_res = CaseAnalytics.analyze_delivery(context)
    payment_res = CaseAnalytics.reconcile_payments(context)

    print("\n--- KẾT QUẢ PHÂN TÍCH GIAO HÀNG ---")
    print(json.dumps(delivery_res, indent=2, ensure_ascii=False))

    print("\n--- KẾT QUẢ ĐỐI SOÁT THANH TOÁN ---")
    print(json.dumps(payment_res, indent=2, ensure_ascii=False))
