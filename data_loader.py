import os
import sys
import pandas as pd
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class OlistDataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.load_datasets()

    def load_datasets(self):
        """Đọc sẵn 6 CSV chính vào RAM để tra cứu nhanh"""
        print("[INFO] Dang nap du lieu Olist CSV...")
        
        self.df_orders = pd.read_csv(os.path.join(self.data_dir, "olist_orders_dataset.csv"))
        self.df_customers = pd.read_csv(os.path.join(self.data_dir, "olist_customers_dataset.csv"))
        self.df_items = pd.read_csv(os.path.join(self.data_dir, "olist_order_items_dataset.csv"))
        self.df_payments = pd.read_csv(os.path.join(self.data_dir, "olist_order_payments_dataset.csv"))
        self.df_products = pd.read_csv(os.path.join(self.data_dir, "olist_products_dataset.csv"))
        self.df_translations = pd.read_csv(os.path.join(self.data_dir, "product_category_name_translation.csv"))

        # Tạo bản đồ dịch tên danh mục tiếng Bồ Đào Nha -> tiếng Anh
        self.category_map = dict(zip(
            self.df_translations['product_category_name'], 
            self.df_translations['product_category_name_english']
        ))
        print("[OK] Nap du lieu hoan tat!")

    def get_case_context(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Trích xuất toàn bộ dữ liệu thô liên quan đến 1 order_id.
        Trả về dict CaseContext chuẩn cho các agent phía sau xử lý.
        """
        # 1. Tìm thông tin Order
        order_rows = self.df_orders[self.df_orders['order_id'] == order_id]
        if order_rows.empty:
            print(f"[ERROR] Khong tim thay order_id: {order_id}")
            return None
        
        order = order_rows.iloc[0]
        customer_id = order['customer_id']

        # 2. Tìm thông tin Customer & Lịch sử đơn hàng
        cust_rows = self.df_customers[self.df_customers['customer_id'] == customer_id]
        customer_unique_id = None
        related_order_ids = []
        
        if not cust_rows.empty:
            customer_unique_id = cust_rows.iloc[0]['customer_unique_id']
            # Lấy tất cả customer_id của cùng 1 customer_unique_id
            all_cust_ids = self.df_customers[self.df_customers['customer_unique_id'] == customer_unique_id]['customer_id']
            # Lấy tất cả order_id tương ứng ngoại trừ order hiện tại
            all_orders = self.df_orders[self.df_orders['customer_id'].isin(all_cust_ids)]['order_id'].tolist()
            related_order_ids = [oid for oid in all_orders if oid != order_id]

        # 3. Tìm các Items thuộc Order
        item_rows = self.df_items[self.df_items['order_id'] == order_id]
        items = []
        
        for _, item in item_rows.iterrows():
            product_id = item['product_id']
            # Tìm category name
            prod_rows = self.df_products[self.df_products['product_id'] == product_id]
            category_en = None
            if not prod_rows.empty:
                cat_pt = prod_rows.iloc[0]['product_category_name']
                if pd.notna(cat_pt):
                    category_en = self.category_map.get(cat_pt, cat_pt)

            items.append({
                "order_item_id": int(item['order_item_id']),
                "product_id": str(product_id),
                "seller_id": str(item['seller_id']),
                "shipping_limit_date": str(item['shipping_limit_date']),
                "price": float(item['price']),
                "freight_value": float(item['freight_value']),
                "category_name": category_en
            })

        # 4. Tìm các Payments thuộc Order
        payment_rows = self.df_payments[self.df_payments['order_id'] == order_id]
        payments = []
        
        for _, pay in payment_rows.iterrows():
            payments.append({
                "payment_sequential": int(pay['payment_sequential']),
                "payment_type": str(pay['payment_type']),
                "payment_installments": int(pay['payment_installments']),
                "payment_value": float(pay['payment_value'])
            })

        # 5. Tổng hợp dữ liệu thô (CaseContext)
        return {
            "order_id": order_id,
            "order_status": str(order['order_status']),
            "order_purchase_timestamp": str(order['order_purchase_timestamp']) if pd.notna(order['order_purchase_timestamp']) else None,
            "order_delivered_carrier_date": str(order['order_delivered_carrier_date']) if pd.notna(order['order_delivered_carrier_date']) else None,
            "order_delivered_customer_date": str(order['order_delivered_customer_date']) if pd.notna(order['order_delivered_customer_date']) else None,
            "order_estimated_delivery_date": str(order['order_estimated_delivery_date']) if pd.notna(order['order_estimated_delivery_date']) else None,
            "customer_id": str(customer_id),
            "customer_unique_id": str(customer_unique_id) if customer_unique_id else None,
            "related_order_ids": related_order_ids,
            "items": items,
            "payments": payments
        }


if __name__ == "__main__":
    loader = OlistDataLoader(data_dir="data")
    test_order_id = "9b75cdaf2d85857ef023980e15d01546"
    context = loader.get_case_context(test_order_id)
    
    print("\n--- KET QUA TEST BUOC 1 ---")
    import json
    print(json.dumps(context, indent=2, ensure_ascii=False))
