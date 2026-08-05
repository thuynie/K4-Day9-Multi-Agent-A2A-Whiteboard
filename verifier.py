from typing import Dict, Any, List

def deduplicate_list(lst: List[Any]) -> List[Any]:
    """Loại bỏ phần tử trùng lặp nhưng vẫn giữ nguyên thứ tự xuất hiện"""
    seen = set()
    res = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            res.append(item)
    return res

class VerifierAgent:
    @staticmethod
    def build_final_output(case_id: str, context: Dict[str, Any], delivery_analysis: Dict[str, Any], payment_reconcile: Dict[str, Any], policy_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo và audit schema JSON hoàn chỉnh cho 1 case"""
        
        order_id = context["order_id"]
        items = context.get("items", [])
        payments = context.get("payments", [])
        
        # 1. Affected Entities (Áp dụng giới hạn max items)
        item_ids = [f"{order_id}:{item['order_item_id']}" for item in items][:5]
        seller_ids = deduplicate_list([item["seller_id"] for item in items if item.get("seller_id")])[:3]
        payment_ids = [f"{order_id}:{pay['payment_sequential']}" for pay in payments][:5]
        
        affected_entities = {
            "order_ids": [order_id][:5],
            "item_ids": item_ids,
            "seller_ids": seller_ids,
            "payment_ids": payment_ids
        }
        
        # 2. Customer Context
        customer_context = {
            "customer_unique_id": context.get("customer_unique_id"),
            "related_order_ids": context.get("related_order_ids", [])[:5]
        }
        
        # 3. Product Context
        product_ids = deduplicate_list([item["product_id"] for item in items if item.get("product_id")])[:5]
        category_names = deduplicate_list([item["category_name"] for item in items if item.get("category_name")])[:5]
        
        product_context = {
            "product_ids": product_ids,
            "category_names": category_names
        }
        
        # 4. Root Cause Analysis
        ranked_causes = [
            {"cause_code": policy_eval["root_cause_code"], "rank": 1}
        ][:3]
        
        root_cause_analysis = {
            "ranked_causes": ranked_causes,
            "responsible_parties": policy_eval["responsible_parties"][:3]
        }
        
        # 5. Evidence IDs (Tối đa 20 evidence)
        evidence_ids = deduplicate_list(policy_eval["evidence_ids"])[:20]
        
        # 6. Resolution Actions (Tối đa 5 actions)
        resolution_actions = policy_eval["resolution_actions"][:5]

        # Ghép thành đối tượng JSON hoàn chỉnh
        final_output = {
            "case_id": case_id,
            "case_assessment": {
                "primary_issue": policy_eval["primary_issue"],
                "secondary_issues": policy_eval["secondary_issues"],
                "case_status": policy_eval["case_status"],
                "confidence": policy_eval["confidence"]
            },
            "affected_entities": affected_entities,
            "customer_context": customer_context,
            "product_context": product_context,
            "delivery_analysis": delivery_analysis,
            "payment_reconciliation": payment_reconcile,
            "root_cause_analysis": root_cause_analysis,
            "evidence_ids": evidence_ids,
            "financial_resolution": {
                "currency": "BRL",
                "recommended_refund_brl": policy_eval["recommended_refund_brl"]
            },
            "resolution_actions": resolution_actions
        }

        return final_output


# --- Đoạn code test thử (chạy trực tiếp file này) ---
if __name__ == "__main__":
    from data_loader import OlistDataLoader
    from analytics import CaseAnalytics
    from policy_engine import PolicyEngine
    import json

    loader = OlistDataLoader(data_dir="data")
    test_case_id = "EC_001"
    test_order_id = "9b75cdaf2d85857ef023980e15d01546"
    
    context = loader.get_case_context(test_order_id)
    delivery_res = CaseAnalytics.analyze_delivery(context)
    payment_res = CaseAnalytics.reconcile_payments(context)
    policy_res = PolicyEngine.evaluate_case(context, delivery_res, payment_res)

    final_json = VerifierAgent.build_final_output(
        test_case_id, context, delivery_res, payment_res, policy_res
    )

    print("\n--- KẾT QUẢ ĐẦU RA JSON HOÀN CHỈNH (SCHEMA COMPLIANT) ---")
    print(json.dumps(final_json, indent=2, ensure_ascii=False))
