import argparse
import sys

from .config import DATA_DIR, INPUT_DIR
from .data_repository import DataRepository
from .orchestrator import Coordinator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Olist multi-agent dispute resolution")
    parser.add_argument("--check-data", action="store_true", help="Kiểm tra dữ liệu và 50 input")
    parser.add_argument("--inspect-case", metavar="CASE_ID", help="Thu thập facts cho một case")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    repository = DataRepository(DATA_DIR, INPUT_DIR)
    if args.check_data:
        errors = repository.validate_sources()
        if errors:
            for error in errors:
                print(f"LỖI: {error}")
            return 1
        print("Dữ liệu hợp lệ: tìm thấy 50 input và toàn bộ claimed order.")
        return 0
    if args.inspect_case:
        cases = {case.case_id: case for case in repository.load_cases()}
        case = cases.get(args.inspect_case)
        if case is None:
            print(f"Không tìm thấy case {args.inspect_case}")
            return 1
        facts = Coordinator(repository).collect_facts(case.claimed_order_id)
        print(f"{case.case_id}: thu thập facts thành công")
        print(f"order_status={facts['order_context']['order']['order_status']}")
        print(f"primary_issue={facts['decision'].primary_issue}")
        print(f"payment_total={facts['payment'].payment_total}")
        print(f"delivery_variance_hours={facts['delivery'].delivery_variance_hours}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
