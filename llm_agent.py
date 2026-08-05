import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

def load_env():
    """Tự động nạp file .env nếu có"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

class GroqLLMAgent:
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        load_env()
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.model_name = model_name
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def analyze_dispute_with_llm(self, customer_message: str, case_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gửi prompt phân tích khiếu nại tới Groq LLM API thật.
        Trả về kết quả suy luận từ LLM.
        """
        if not self.api_key or self.api_key == "gsk_your_groq_api_key_here":
            return {
                "llm_status": "skipped_no_api_key",
                "reasoning": "Chưa nhập GROQ_API_KEY trong .env. Sử dụng Policy Engine chuẩn định hướng."
            }

        system_prompt = (
            "You are an expert E-commerce Dispute Resolution AI Agent. "
            "Analyze customer complaint messages and order facts strictly according to EC_POLICY_V2 rules. "
            "Determine primary_issue, refund recommendations, and responsible parties."
        )

        user_prompt = f"""
[CUSTOMER COMPLAINT MESSAGE]
"{customer_message}"

[CASE FACTS & DATA]
- Order ID: {case_facts.get('order_id')}
- Order Status: {case_facts.get('order_status')}
- Delivery Variance Hours: {case_facts.get('delivery_variance_hours')}
- Late Handoff Sellers: {case_facts.get('late_handoff_seller_ids')}
- Payment Reconciled: {case_facts.get('reconciled')}
- Total Payment (BRL): {case_facts.get('payment_total_brl')}
- Expected Total (BRL): {case_facts.get('expected_total_brl')}

Provide your assessment in concise JSON format.
"""

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            req = urllib.request.Request(
                self.endpoint, 
                data=json.dumps(payload).encode("utf-8"), 
                headers=headers, 
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result_json = json.loads(resp.read().decode("utf-8"))
                llm_response = result_json["choices"][0]["message"]["content"]
                return {
                    "llm_status": "success",
                    "model_used": self.model_name,
                    "llm_reasoning": llm_response
                }
        except Exception as e:
            return {
                "llm_status": "error",
                "error_message": str(e)
            }


if __name__ == "__main__":
    agent = GroqLLMAgent()
    test_facts = {
        "order_id": "9b75cdaf2d85857ef023980e15d01546",
        "order_status": "delivered",
        "delivery_variance_hours": -166.52,
        "late_handoff_seller_ids": [],
        "reconciled": True,
        "payment_total_brl": 237.34,
        "expected_total_brl": 237.34
    }
    res = agent.analyze_dispute_with_llm("Hãy điều tra khiếu nại giúp mình", test_facts)
    print("--- KẾT QUẢ CALL LLM THẬT ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))
