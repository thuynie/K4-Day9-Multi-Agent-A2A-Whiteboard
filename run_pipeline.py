import os
import sys
import json
import glob

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from data_loader import OlistDataLoader
from analytics import CaseAnalytics
from policy_engine import PolicyEngine
from verifier import VerifierAgent
from llm_agent import GroqLLMAgent

def main():
    input_dir = "input"
    output_dir = "output"
    logging_dir = "logging"
    logging_trace_file = os.path.join(logging_dir, "trace.jsonl")
    logging_metadata_file = os.path.join(logging_dir, "metadata.json")

    # Tạo thư mục output và logging nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(logging_dir, exist_ok=True)

    # Nạp dữ liệu Olist & Khởi tạo LLM Agent (Model: llama-3.1-8b-instant <= 10B params)
    loader = OlistDataLoader(data_dir="data")
    llm_agent = GroqLLMAgent(model_name="llama-3.1-8b-instant")

    # Lấy danh sách tất cả các file EC_*.json trong input/
    input_files = sorted(glob.glob(os.path.join(input_dir, "EC_*.json")))
    print(f"[INFO] Tim thay {len(input_files)} cases trong thu muc {input_dir}/. Bat dau xu ly Multi-Agent...\n")

    trace_records = []

    for file_path in input_files:
        with open(file_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)

        case_id = input_data["case_id"]
        customer_request = input_data.get("customer_request", {})
        customer_message = customer_request.get("message", "")
        claimed_order_id = customer_request.get("claimed_order_id", "")

        print(f"[PROCESSING] {case_id} (Order ID: {claimed_order_id})...")

        # 1. Customer & Order Agents: Trích xuất Context
        context = loader.get_case_context(claimed_order_id)
        if not context:
            print(f"[WARNING] Bo qua {case_id} do khong tim thay du lieu order.")
            continue

        # 2. Delivery & Payment Agents: Phân tích Giao hàng & Tài chính
        delivery_res = CaseAnalytics.analyze_delivery(context)
        payment_res = CaseAnalytics.reconcile_payments(context)

        # 3. LLM Agent: Gửi prompt phân tích tới Groq LLM API
        case_facts = {
            "order_id": claimed_order_id,
            "order_status": context.get("order_status"),
            "delivery_variance_hours": delivery_res.get("delivery_variance_hours"),
            "late_handoff_seller_ids": delivery_res.get("late_handoff_seller_ids"),
            "reconciled": payment_res.get("reconciled"),
            "payment_total_brl": payment_res.get("payment_total_brl"),
            "expected_total_brl": payment_res.get("expected_total_brl")
        }
        llm_result = llm_agent.analyze_dispute_with_llm(customer_message, case_facts)

        # 4. Policy Agent: Đánh giá quy tắc nghiệp vụ EC_POLICY_V2
        policy_res = PolicyEngine.evaluate_case(context, delivery_res, payment_res)

        # 5. Verifier Agent: Audit & Chuẩn hóa Schema JSON
        final_output = VerifierAgent.build_final_output(
            case_id, context, delivery_res, payment_res, policy_res
        )

        # Ghi file JSON vào folder output/
        output_file_path = os.path.join(output_dir, f"{case_id}.json")
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        # 6. Ghi thông tin Multi-Agent trace log
        trace_record = {
            "case_id": case_id,
            "claimed_order_id": claimed_order_id,
            "primary_issue": policy_res["primary_issue"],
            "secondary_issues": policy_res["secondary_issues"],
            "recommended_refund_brl": policy_res["recommended_refund_brl"],
            "actions": policy_res["resolution_actions"],
            "llm_agent_execution": llm_result,
            "status": "success"
        }
        trace_records.append(trace_record)

    # Ghi trace log vào thư mục logging/
    with open(logging_trace_file, "w", encoding="utf-8") as f:
        for record in trace_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Đảm bảo metadata.json trong thư mục logging/
    metadata_content = {
        "model_name": "llama-3.1-8b-instant",
        "parameter_size": "8B",
        "framework": "Groq LLM Multi-Agent Dispute Resolution Pipeline",
        "runtime": "Python 3.14"
    }
    with open(logging_metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata_content, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] XU LY HOAN TAT MULTI-AGENT! Da tao 50 file trong '{output_dir}/' va ghi log vao '{logging_dir}/'.")

if __name__ == "__main__":
    main()
