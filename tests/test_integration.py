import unittest
from collections import Counter

from ec_dispute.config import DATA_DIR, INPUT_DIR
from ec_dispute.data_repository import DataRepository
from ec_dispute.orchestrator import Coordinator


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = DataRepository(DATA_DIR, INPUT_DIR)
        coordinator = Coordinator(cls.repository)
        cls.outputs = [coordinator.process_case(case) for case in cls.repository.load_cases()]

    def test_primary_issue_distribution(self) -> None:
        actual = Counter(output["case_assessment"]["primary_issue"] for output in self.outputs)
        expected = Counter({
            "canceled_order_paid": 8,
            "unavailable_order_paid": 6,
            "late_delivery_seller": 10,
            "late_delivery_logistics": 10,
            "valid_split_payment": 8,
            "unsupported_late_claim": 8,
        })
        self.assertEqual(expected, actual)

    def test_all_cases_have_stable_ids_and_limits(self) -> None:
        limits = {
            "order_ids": 5, "item_ids": 5, "seller_ids": 3, "payment_ids": 5,
            "related_order_ids": 5, "product_ids": 5, "category_names": 5,
        }
        for case, output in zip(self.repository.load_cases(), self.outputs):
            self.assertEqual(case.case_id, output["case_id"])
            self.assertEqual([case.claimed_order_id], output["affected_entities"]["order_ids"])
            values = {**output["affected_entities"], **output["customer_context"], **output["product_context"]}
            for field, limit in limits.items():
                self.assertLessEqual(len(values[field]), limit, f"{case.case_id}: {field}")
            self.assertLessEqual(len(output["evidence_ids"]), 20)
            self.assertLessEqual(len(output["resolution_actions"]), 5)

    def test_unavailable_orders_use_required_nulls(self) -> None:
        unavailable = [
            output for output in self.outputs
            if output["case_assessment"]["primary_issue"] == "unavailable_order_paid"
        ]
        self.assertEqual(6, len(unavailable))
        for output in unavailable:
            payment = output["payment_reconciliation"]
            self.assertIsNone(payment["expected_total_brl"])
            self.assertIsNone(payment["difference_brl"])
            self.assertIsNone(payment["reconciled"])
            self.assertEqual([], output["affected_entities"]["item_ids"])

    def test_valid_split_payment_does_not_duplicate_allocation_action(self) -> None:
        split_cases = [
            output for output in self.outputs
            if output["case_assessment"]["primary_issue"] == "valid_split_payment"
        ]
        for output in split_cases:
            self.assertNotIn("verify_payment_allocation", output["resolution_actions"])

    def test_refund_and_status_are_consistent(self) -> None:
        for output in self.outputs:
            refund = output["financial_resolution"]["recommended_refund_brl"]
            status = output["case_assessment"]["case_status"]
            self.assertEqual("action_required" if refund > 0 else "no_action", status)


if __name__ == "__main__":
    unittest.main()
