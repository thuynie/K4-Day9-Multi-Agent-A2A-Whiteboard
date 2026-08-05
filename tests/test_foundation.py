import unittest
from decimal import Decimal

from ec_dispute.config import DATA_DIR, INPUT_DIR
from ec_dispute.data_repository import DataRepository
from ec_dispute.orchestrator import Coordinator
from ec_dispute.utils import hours_between, money, unique_in_order


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = DataRepository(DATA_DIR, INPUT_DIR)

    def test_has_exactly_50_valid_cases(self) -> None:
        self.assertEqual([], self.repository.validate_sources())
        self.assertEqual(50, len(self.repository.load_cases()))

    def test_money_rounds_to_two_decimals(self) -> None:
        self.assertEqual(Decimal("10.13"), money(Decimal("10.125")))

    def test_hours_between(self) -> None:
        self.assertEqual(Decimal("1.50"), hours_between("2018-01-01 11:30:00", "2018-01-01 10:00:00"))

    def test_unique_preserves_source_order(self) -> None:
        self.assertEqual(["b", "a", "c"], unique_in_order(["b", "a", "b", "c"]))

    def test_known_case_ec_002_is_late_delivery_seller(self) -> None:
        case = self.repository.load_cases()[1]
        facts = Coordinator(self.repository).collect_facts(case.claimed_order_id)
        self.assertEqual("late_delivery_seller", facts["decision"].primary_issue)


if __name__ == "__main__":
    unittest.main()
