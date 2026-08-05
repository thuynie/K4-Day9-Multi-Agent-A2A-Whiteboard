from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .models import CaseInput


class DataRepository:
    """Nạp CSV một lần và cung cấp lookup read-only cho các agent."""

    def __init__(self, data_dir: Path, input_dir: Path) -> None:
        self.data_dir = data_dir
        self.input_dir = input_dir
        self.orders = self._by_key("olist_orders_dataset.csv", "order_id")
        self.customers = self._by_key("olist_customers_dataset.csv", "customer_id")
        self.products = self._by_key("olist_products_dataset.csv", "product_id")
        self.sellers = self._by_key("olist_sellers_dataset.csv", "seller_id")
        self.items_by_order = self._grouped("olist_order_items_dataset.csv", "order_id")
        self.payments_by_order = self._grouped("olist_order_payments_dataset.csv", "order_id")
        self.orders_by_unique_customer = self._index_customer_history()

    def _rows(self, filename: str) -> list[dict[str, str]]:
        with (self.data_dir / filename).open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    def _by_key(self, filename: str, key: str) -> dict[str, dict[str, str]]:
        return {row[key]: row for row in self._rows(filename)}

    def _grouped(self, filename: str, key: str) -> dict[str, list[dict[str, str]]]:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in self._rows(filename):
            grouped[row[key]].append(row)
        return dict(grouped)

    def _index_customer_history(self) -> dict[str, list[str]]:
        history: dict[str, list[str]] = defaultdict(list)
        for order_id, order in self.orders.items():
            customer = self.customers[order["customer_id"]]
            history[customer["customer_unique_id"]].append(order_id)
        return dict(history)

    def load_cases(self) -> list[CaseInput]:
        cases: list[CaseInput] = []
        for path in sorted(self.input_dir.glob("EC_*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            request = raw["customer_request"]
            scope = raw["investigation_scope"]
            cases.append(CaseInput(
                case_id=raw["case_id"],
                claimed_order_id=request["claimed_order_id"],
                policy_version=raw["policy_version"],
                include_customer_history=scope["include_customer_history"],
                include_product_context=scope["include_product_context"],
            ))
        return cases

    def validate_sources(self) -> list[str]:
        errors: list[str] = []
        cases = self.load_cases()
        if len(cases) != 50:
            errors.append(f"Cần đúng 50 input, hiện có {len(cases)}")
        for case in cases:
            if case.claimed_order_id not in self.orders:
                errors.append(f"{case.case_id}: order không tồn tại")
        return errors
