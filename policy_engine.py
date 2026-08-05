from typing import Dict, Any, List

class PolicyEngine:
    @staticmethod
    def evaluate_case(context: Dict[str, Any], delivery_analysis: Dict[str, Any], payment_reconcile: Dict[str, Any]) -> Dict[str, Any]:
        """Đánh giá toàn bộ case theo quy tắc EC_POLICY_V2"""
        
        order_status = context.get("order_status")
        payment_total = payment_reconcile.get("payment_total_brl", 0.0)
        freight_total = payment_reconcile.get("freight_total_brl") or 0.0
        
        delivery_variance = delivery_analysis.get("delivery_variance_hours")
        late_sellers = delivery_analysis.get("late_handoff_seller_ids", [])
        
        items = context.get("items", [])
        payments = context.get("payments", [])
        related_orders = context.get("related_order_ids", [])

        # ----------------------------------------------------
        # 1. ĐÁNH GIÁ PRIMARY ISSUE (ƯU TIÊN THEO THỨ TỰ 1-6)
        # ----------------------------------------------------
        primary_issue = None
        root_cause_code = None
        responsible_parties = []
        recommended_refund = 0.0
        main_action = None

        # Rule 1: canceled_order_paid
        if order_status == "canceled" and payment_total > 0:
            primary_issue = "canceled_order_paid"
            root_cause_code = "ORDER_CANCELED_AFTER_PAYMENT"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund = payment_total
            main_action = "issue_full_refund"

        # Rule 2: unavailable_order_paid
        elif order_status == "unavailable" and payment_total > 0:
            primary_issue = "unavailable_order_paid"
            root_cause_code = "ORDER_UNAVAILABLE_AFTER_PAYMENT"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund = payment_total
            main_action = "issue_full_refund"

        # Rule 3: late_delivery_seller (Giao trễ khách & Carrier nhận hàng muộn hơn shipping_limit)
        elif delivery_variance is not None and delivery_variance > 0 and len(late_sellers) > 0:
            primary_issue = "late_delivery_seller"
            root_cause_code = "SELLER_HANDOFF_AFTER_LIMIT"
            responsible_parties = [{"party_type": "seller", "party_id": sid} for sid in late_sellers]
            recommended_refund = freight_total
            main_action = "refund_freight"

        # Rule 4: late_delivery_logistics (Giao trễ khách & Tất cả seller đều giao đúng hạn)
        elif delivery_variance is not None and delivery_variance > 0 and len(late_sellers) == 0:
            primary_issue = "late_delivery_logistics"
            root_cause_code = "CARRIER_DELIVERED_AFTER_ESTIMATE"
            responsible_parties = [{"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}]
            recommended_refund = freight_total
            main_action = "refund_freight"

        # Rule 5: valid_split_payment (Từ 2 payment rows trở lên & tiền khớp)
        elif len(payments) >= 2 and payment_reconcile.get("reconciled") is True:
            primary_issue = "valid_split_payment"
            root_cause_code = "MULTIPLE_PAYMENTS_RECONCILED"
            responsible_parties = []
            recommended_refund = 0.0
            main_action = "explain_valid_split_payment"

        # Rule 6: unsupported_late_claim (Mặc định: Giao đúng hạn, payment khớp)
        else:
            primary_issue = "unsupported_late_claim"
            root_cause_code = "DELIVERY_WITHIN_ESTIMATE"
            responsible_parties = []
            recommended_refund = 0.0
            main_action = "reject_late_refund"

        # ----------------------------------------------------
        # 2. ĐÁNH GIÁ SECONDARY ISSUES (THEO THỨ TỰ CỐ ĐỊNH 1-5)
        # ----------------------------------------------------
        secondary_issues = []
        
        # 1. multi_item_order
        if len(items) >= 2:
            secondary_issues.append("multi_item_order")
            
        # 2. multi_seller_order
        unique_sellers = set(item["seller_id"] for item in items)
        if len(unique_sellers) >= 2:
            secondary_issues.append("multi_seller_order")
            
        # 3. split_payment
        if len(payments) >= 2:
            secondary_issues.append("split_payment")
            
        # 4. repeat_customer
        if len(related_orders) >= 1:
            secondary_issues.append("repeat_customer")
            
        # 5. multiple_categories
        categories = set(item["category_name"] for item in items if item["category_name"])
        if len(categories) >= 2:
            secondary_issues.append("multiple_categories")

        # ----------------------------------------------------
        # 3. TẠO DANH SÁCH RESOLUTION ACTIONS
        # ----------------------------------------------------
        actions = [main_action]
        
        # Action bổ sung 1: Review handoff hoặc carrier
        if primary_issue == "late_delivery_seller" or len(late_sellers) > 0:
            actions.append("review_seller_handoff")
        elif primary_issue == "late_delivery_logistics":
            actions.append("review_carrier_delay")

        # Action bổ sung 2: Verify refund
        if recommended_refund > 0:
            actions.append("verify_refund_completion")

        # Action bổ sung 3: Coordinate multi seller
        if "multi_seller_order" in secondary_issues:
            actions.append("coordinate_multi_seller_case")

        # Action bổ sung 4: Verify payment allocation
        if "split_payment" in secondary_issues and primary_issue != "valid_split_payment":
            actions.append("verify_payment_allocation")

        # ----------------------------------------------------
        # 4. XÂY DỰNG EVIDENCE IDS
        # ----------------------------------------------------
        evidence_ids = []
        order_id = context["order_id"]
        evidence_ids.append(f"order:{order_id}")
        
        for item in items:
            evidence_ids.append(f"item:{order_id}:{item['order_item_id']}")
            
        for pay in payments:
            evidence_ids.append(f"payment:{order_id}:{pay['payment_sequential']}")
            
        for party in responsible_parties:
            if party["party_type"] == "seller":
                evidence_ids.append(f"seller:{party['party_id']}")
                
        evidence_ids.append(f"policy:{root_cause_code}")

        # ----------------------------------------------------
        # 5. ĐÓNG GÓI KẾT QUẢ
        # ----------------------------------------------------
        case_status = "action_required" if recommended_refund > 0 else "no_action"

        return {
            "primary_issue": primary_issue,
            "secondary_issues": secondary_issues,
            "case_status": case_status,
            "confidence": 0.95,
            "root_cause_code": root_cause_code,
            "responsible_parties": responsible_parties,
            "recommended_refund_brl": round(recommended_refund, 2),
            "resolution_actions": actions,
            "evidence_ids": evidence_ids
        }


# --- Đoạn code test thử (chạy trực tiếp file này) ---
if __name__ == "__main__":
    from data_loader import OlistDataLoader
    from analytics import CaseAnalytics
    import json

    loader = OlistDataLoader(data_dir="data")
    test_order_id = "9b75cdaf2d85857ef023980e15d01546" # EC_001
    context = loader.get_case_context(test_order_id)

    delivery_res = CaseAnalytics.analyze_delivery(context)
    payment_res = CaseAnalytics.reconcile_payments(context)
    policy_res = PolicyEngine.evaluate_case(context, delivery_res, payment_res)

    print("\n--- KẾT QUẢ ĐÁNH GIÁ POLICY ---")
    print(json.dumps(policy_res, indent=2, ensure_ascii=False))
