# src/agents.py
import json
import os
from typing import Tuple
from dotenv import load_dotenv
from groq import Groq

from src.tools import get_area_metrics
from src.schemas import AnalystDraft, VerificationReport

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DLD_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_area_metrics",
        "description": "Retrieves official DLD sales volume, average price, median price, and transaction traces for an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_name": {
                    "type": "string",
                    "description": "Dubai area name, e.g. 'Dubai Marina', 'Business Bay', 'Downtown Dubai'"
                },
                "trans_group": {
                    "type": "string",
                    "description": "Transaction group, default 'Sales'",
                    "enum": ["Sales", "Mortgages", "Gifts"]
                }
            },
            "required": ["area_name"]
        }
    }
}

class AcreIQWorkflow:
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.model_name = model_name

    def run_analyst(self, user_prompt: str) -> Tuple[AnalystDraft, dict]:
        """Agent 1: Executes DLD tool call and returns structured market briefing."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Dubai Real Estate Analyst. Answer user questions using official DLD transaction data.\n"
                    "Always call 'get_area_metrics' to pull actual records before answering. Never invent figures.\n"
                    "If the user asks about an area, identify the area name and call the tool."
                )
            },
            {"role": "user", "content": user_prompt}
        ]

        try:
            chat_completion = groq_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=[DLD_TOOL_DEFINITION],
                tool_choice="auto",
                temperature=0.0
            )

            response_message = chat_completion.choices[0].message
            raw_tool_data = {}

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "get_area_metrics":
                        args = json.loads(tool_call.function.arguments)
                        print(f"DEBUG: LLM called tool with args = {args}")
                        raw_tool_data = get_area_metrics(
                            area_name=args.get("area_name", ""),
                            trans_group=args.get("trans_group", "Sales")
                        )
        except Exception as e:
            raw_tool_data = {"status": "TOOL_CALL_ERROR", "error": str(e)}

        # Clean JSON extraction pass directly from the retrieved tool payload
        extraction_messages = [
            {
                "role": "system",
                "content": (
                    "You are a real estate data structuring assistant. Produce a single JSON object matching the requested schema.\n"
                    "Strictly adhere to the provided raw database metrics. Do not invent any numbers.\n"
                    "Schema:\n"
                    "{\n"
                    '  "area_analyzed": string,\n'
                    '  "cadastral_name": string,\n'
                    '  "transaction_count": integer,\n'
                    '  "avg_price_aed": float,\n'
                    '  "median_price_aed": float,\n'
                    '  "avg_sqm_price_aed": float,\n'
                    '  "market_summary": string,\n'
                    '  "sample_transaction_ids": list of strings\n'
                    "}\n"
                    "If the status is NOT_FOUND, set transaction_count, avg_price_aed, and median_price_aed to 0."
                )
            },
            {
                "role": "user",
                "content": f"User Query: {user_prompt}\nRetrieved Registry Data: {json.dumps(raw_tool_data)}"
            }
        ]

        structured_completion = groq_client.chat.completions.create(
            model=self.model_name,
            messages=extraction_messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_json_str = structured_completion.choices[0].message.content
        draft = AnalystDraft.model_validate_json(raw_json_str)
        return draft, raw_tool_data

    def run_auditor_gate(self, draft: AnalystDraft, raw_tool_data: dict) -> VerificationReport:
        discrepancies = []

        if raw_tool_data.get("status") != "SUCCESS":
            reason = raw_tool_data.get("status", "NO_TOOL_CALL_MADE")
            return VerificationReport(
                is_grounded=False,
                discrepancies=[f"NO_RECORDS_FOUND: {reason} — no verified DLD transactions to ground against."],
                final_output=f"NOT_FOUND: No registered transaction records exist for '{draft.area_analyzed}' in DLD registry.",
                source_trace_ids=[]
            )

        metrics = raw_tool_data.get("summary_metrics", {})
        expected_median = float(metrics.get("median_price_aed", 0.0))
        expected_avg = float(metrics.get("avg_price_aed", 0.0))
   

        # Check 2: Metric grounding within 1% threshold
        if expected_median > 0 and abs(draft.median_price_aed - expected_median) > (expected_median * 0.01):
            discrepancies.append(
                f"Median price mismatch: LLM claimed {draft.median_price_aed}, DB recorded {expected_median}"
            )

        if expected_avg > 0 and abs(draft.avg_price_aed - expected_avg) > (expected_avg * 0.01):
            discrepancies.append(
                f"Average price mismatch: LLM claimed {draft.avg_price_aed}, DB recorded {expected_avg}"
            )

        # Check 3: Transaction ID provenance audit
        raw_sample_ids = set(raw_tool_data.get("audit_trail", {}).get("trace_sample_ids", []))
        model_ids = set(draft.sample_transaction_ids)
        invalid_ids = model_ids - raw_sample_ids

        if invalid_ids:
            discrepancies.append(f"LLM cited unverified transaction IDs: {list(invalid_ids)}")

        if discrepancies:
            return VerificationReport(
                is_grounded=False,
                discrepancies=discrepancies,
                final_output="REJECTED_BY_AUDITOR: Hallucination detected. Metrics do not match DLD records.",
                source_trace_ids=list(raw_sample_ids)
            )

        formatted_final = (
            f"**AcreIQ Market Brief: {draft.area_analyzed} (Cadastral: {draft.cadastral_name})**\n\n"
            f"{draft.market_summary}\n\n"
            f"- **Analyzed Transactions:** {draft.transaction_count:,}\n"
            f"- **Median Price:** AED {draft.median_price_aed:,.2f}\n"
            f"- **Average Price:** AED {draft.avg_price_aed:,.2f}\n"
            f"- **Avg Price / m²:** AED {draft.avg_sqm_price_aed:,.2f}\n"
            f"- **Verified Registry Record Sample:** {', '.join(draft.sample_transaction_ids)}"
        )

        return VerificationReport(
            is_grounded=True,
            discrepancies=[],
            final_output=formatted_final,
            source_trace_ids=draft.sample_transaction_ids
        )

    def execute(self, user_prompt: str) -> VerificationReport:
        draft, raw_tool_data = self.run_analyst(user_prompt)
        report = self.run_auditor_gate(draft, raw_tool_data)
        return report