from __future__ import annotations

import re

from ..data_repository import DataRepository
from ..models import CaseInput


class VerifierAgent:
    name = "verifier_agent"

    LIMITS = {
        "order_ids": 5, "item_ids": 5, "seller_ids": 3, "payment_ids": 5,
        "related_order_ids": 5, "product_ids": 5, "category_names": 5,
        "ranked_causes": 3, "responsible_parties": 3, "evidence_ids": 20,
        "resolution_actions": 5,
    }
    EVIDENCE_PATTERN = re.compile(
        r"^(order:[0-9a-f]+|item:[0-9a-f]+:\d+|payment:[0-9a-f]+:\d+|seller:[0-9a-f]+|policy:[A-Z_]+)$"
    )

    def verify_draft(self, case: CaseInput, draft: dict, repository: DataRepository) -> list[str]:
        required = {
            "case_id", "case_assessment", "affected_entities", "customer_context",
            "product_context", "delivery_analysis", "payment_reconciliation",
            "root_cause_analysis", "evidence_ids", "financial_resolution",
            "resolution_actions",
        }
        errors: list[str] = []
        missing = required.difference(draft)
        if missing:
            return [f"Thiếu trường output: {sorted(missing)}"]
        if draft["case_id"] != case.case_id:
            errors.append("case_id không khớp input")
        affected = draft["affected_entities"]
        if affected["order_ids"] != [case.claimed_order_id]:
            errors.append("affected order phải chỉ chứa claimed order")
        expected_items = {
            f"{case.claimed_order_id}:{row['order_item_id']}"
            for row in repository.items_by_order.get(case.claimed_order_id, [])
        }
        if not set(affected["item_ids"]).issubset(expected_items):
            errors.append("affected item không tồn tại trong order")
        expected_payments = {
            f"{case.claimed_order_id}:{row['payment_sequential']}"
            for row in repository.payments_by_order.get(case.claimed_order_id, [])
        }
        if not set(affected["payment_ids"]).issubset(expected_payments):
            errors.append("affected payment không tồn tại trong order")
        expected_sellers = {
            row["seller_id"] for row in repository.items_by_order.get(case.claimed_order_id, [])
        }
        if not set(affected["seller_ids"]).issubset(expected_sellers):
            errors.append("affected seller không tồn tại trong order")
        if set(draft["customer_context"]["related_order_ids"]) & set(affected["order_ids"]):
            errors.append("related order không được nằm trong affected entities")
        self._check_limits(draft, errors)
        self._check_financial_consistency(draft, errors)
        for evidence in draft["evidence_ids"]:
            if not self.EVIDENCE_PATTERN.fullmatch(evidence):
                errors.append(f"Evidence sai định dạng: {evidence}")
        valid_evidence = (
            {f"order:{case.claimed_order_id}"}
            | {f"item:{value}" for value in expected_items}
            | {f"payment:{value}" for value in expected_payments}
            | {f"seller:{value}" for value in expected_sellers}
            | {f"policy:{row['cause_code']}" for row in draft["root_cause_analysis"]["ranked_causes"]}
        )
        if not set(draft["evidence_ids"]).issubset(valid_evidence):
            errors.append("Evidence không thể kiểm chứng từ dữ liệu/policy")
        return errors

    def _check_limits(self, draft: dict, errors: list[str]) -> None:
        values = {
            **draft["affected_entities"],
            **draft["customer_context"],
            **draft["product_context"],
            **draft["root_cause_analysis"],
            "evidence_ids": draft["evidence_ids"],
            "resolution_actions": draft["resolution_actions"],
        }
        for field, limit in self.LIMITS.items():
            if len(values[field]) > limit:
                errors.append(f"{field} vượt giới hạn {limit}")

    @staticmethod
    def _check_financial_consistency(draft: dict, errors: list[str]) -> None:
        assessment = draft["case_assessment"]
        refund = draft["financial_resolution"]["recommended_refund_brl"]
        expected_status = "action_required" if refund > 0 else "no_action"
        if assessment["case_status"] != expected_status:
            errors.append("case_status không khớp refund")
        confidence = assessment["confidence"]
        if not 0 <= confidence <= 1:
            errors.append("confidence nằm ngoài [0, 1]")
        payment = draft["payment_reconciliation"]
        if payment["expected_total_brl"] is None:
            if payment["difference_brl"] is not None or payment["reconciled"] is not None:
                errors.append("Order không item phải có difference/reconciled null")
        else:
            expected = round(payment["item_total_brl"] + payment["freight_total_brl"], 2)
            difference = round(payment["payment_total_brl"] - expected, 2)
            if payment["expected_total_brl"] != expected or payment["difference_brl"] != difference:
                errors.append("Payment reconciliation không nhất quán")
