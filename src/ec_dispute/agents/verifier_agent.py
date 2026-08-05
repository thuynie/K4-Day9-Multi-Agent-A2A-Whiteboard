class VerifierAgent:
    name = "verifier_agent"

    def verify_draft(self, draft: dict) -> list[str]:
        """Bộ khung verifier; cần bổ sung cross-check trước khi sinh output."""
        required = {
            "case_id", "case_assessment", "affected_entities", "customer_context",
            "product_context", "delivery_analysis", "payment_reconciliation",
            "root_cause_analysis", "evidence_ids", "financial_resolution",
            "resolution_actions",
        }
        missing = required.difference(draft)
        return [f"Thiếu trường output: {sorted(missing)}"] if missing else []
