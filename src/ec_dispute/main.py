import argparse
import json
import sys
from datetime import datetime

from .config import DATA_DIR, INPUT_DIR, LOGGING_DIR, OUTPUT_DIR
from .data_repository import DataRepository
from .observability.metadata_writer import write_metadata
from .observability.trace_writer import TraceWriter
from .orchestrator import Coordinator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Olist multi-agent dispute resolution")
    parser.add_argument("--check-data", action="store_true", help="Kiểm tra dữ liệu và 50 input")
    parser.add_argument("--inspect-case", metavar="CASE_ID", help="Thu thập facts cho một case")
    parser.add_argument("--run-all", action="store_true", help="Sinh và kiểm chứng output cho 50 case")
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
    if args.run_all:
        return run_all(repository)
    parser.print_help()
    return 0


def run_all(repository: DataRepository) -> int:
    errors = repository.validate_sources()
    if errors:
        for error in errors:
            print(f"LỖI: {error}")
        return 1
    run_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    trace = TraceWriter(LOGGING_DIR / "trace.jsonl", run_id)
    coordinator = Coordinator(repository)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_output in OUTPUT_DIR.glob("EC_*.json"):
        old_output.unlink()
    succeeded = 0
    failed = 0
    trace.write(None, "coordinator", "run_started", "success", {"case_count": 50})
    for case in repository.load_cases():
        try:
            output = coordinator.process_case(case, trace)
            path = OUTPUT_DIR / f"{case.case_id}.json"
            path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            trace.write(case.case_id, "coordinator", "output_written", "success", {"path": str(path.relative_to(OUTPUT_DIR.parent))})
            succeeded += 1
        except Exception as exc:
            failed += 1
            trace.write(case.case_id, "coordinator", "case_failed", "error", {"error": str(exc)})
            print(f"LỖI {case.case_id}: {exc}")
    final_status = "success" if failed == 0 else "error"
    trace.write(None, "coordinator", "run_completed", final_status, {"succeeded": succeeded, "failed": failed})
    write_metadata(LOGGING_DIR / "metadata.json", run_id, succeeded, failed)
    print(f"Hoàn tất: {succeeded} thành công, {failed} thất bại.")
    return 0 if failed == 0 and succeeded == 50 else 1


if __name__ == "__main__":
    raise SystemExit(main())
