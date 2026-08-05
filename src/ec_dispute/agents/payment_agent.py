from decimal import Decimal

from ..data_repository import DataRepository
from ..models import PaymentAnalysis
from ..utils import money, unique_in_order


class PaymentAgent:
    name = "payment_agent"

    def investigate(self, repository: DataRepository, order_id: str, item_total: Decimal, freight_total: Decimal, has_items: bool) -> PaymentAnalysis:
        payments = sorted(repository.payments_by_order.get(order_id, []), key=lambda row: int(row["payment_sequential"]))
        payment_total = money(sum((Decimal(row["payment_value"]) for row in payments), Decimal("0")))
        if not has_items:
            expected = difference = None
            reconciled = None
        else:
            expected = money(item_total + freight_total)
            difference = money(payment_total - expected)
            reconciled = abs(difference) <= Decimal("0.10")
        return PaymentAnalysis(
            item_total=item_total,
            freight_total=freight_total,
            expected_total=expected,
            payment_total=payment_total,
            difference=difference,
            reconciled=reconciled,
            payment_types=tuple(unique_in_order(row["payment_type"] for row in payments)),
            payment_row_count=len(payments),
        )
