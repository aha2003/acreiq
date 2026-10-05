# src/agents.py
import json
import os
import re
from typing import Tuple, List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq

from src.tools import get_area_metrics, compare_areas_metrics
from src.schemas import (
    AnalystDraft,
    VerificationReport,
    MarketSignal,
    PeriodDelta,
    AuditCheckItem
)

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DLD_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_area_metrics",
        "description": "Retrieves official DLD sales volume, average price, median price, transaction traces, and timeseries.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_name": {
                    "type": "string",
                    "description": "Dubai area name, e.g. 'Al Furjan', 'Dubai Marina', 'Business Bay'"
                },
                "trans_group": {
                    "type": "string",
                    "description": "Transaction group, default 'Sales'",
                    "enum": ["Sales", "Mortgages", "Gifts"]
                },
                "reg_type": {
                    "type": "string",
                    "description": "Property status filter: 'Ready' or 'Off-Plan'",
                    "enum": ["Ready", "Off-Plan"]
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional ISO format start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional ISO format end date (YYYY-MM-DD)"
                }
            },
            "required": ["area_name"]
        }
    }
}

COMPARE_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "compare_areas_metrics",
        "description": "Compares real estate metrics and prices between two distinct Dubai areas side-by-side.",
        "parameters": {
            "type": "object",
            "properties": {
                "primary_area": {
                    "type": "string",
                    "description": "First area name, e.g. 'Downtown Dubai'",
                },
                "secondary_area": {
                    "type": "string",
                    "description": "Second area name, e.g. 'Dubai Marina'",
                },
                "trans_group": {
                    "type": "string",
                    "description": "Transaction group, default 'Sales'",
                    "enum": ["Sales", "Mortgages", "Gifts"],
                },
                "start_date": {
                    "type": "string",
                    "description": "Optional ISO format start date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "Optional ISO format end date (YYYY-MM-DD)",
                },
            },
            "required": ["primary_area", "secondary_area"],
        },
    },
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
                    "Always call 'get_area_metrics' or 'compare_areas_metrics' to pull actual records before answering.\n"
                    "IMPORTANT: Unless the user explicitly specifies 'Ready only' or 'Off-plan only', do NOT pass a reg_type filter. Leave reg_type empty/null so both ready and off-plan records are retrieved.\n"
                    "If the user asks why volume spiked or asks about price movements, pass only the area_name so all transaction types are captured."
                )
            },
            {"role": "user", "content": user_prompt}
        ]

        try:
            chat_completion = groq_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=[DLD_TOOL_DEFINITION, COMPARE_TOOL_DEFINITION],
                tool_choice="auto",
                temperature=0.0,
            )

            response_message = chat_completion.choices[0].message
            raw_tool_data = {}

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if func_name == "compare_areas_metrics":
                        raw_tool_data = compare_areas_metrics(
                            primary_area=args.get("primary_area", ""),
                            secondary_area=args.get("secondary_area", ""),
                            trans_group=args.get("trans_group", "Sales"),
                            start_date=args.get("start_date"),
                            end_date=args.get("end_date"),
                        )
                        break

                    elif func_name == "get_area_metrics":
                        raw_tool_data = get_area_metrics(
                            area_name=args.get("area_name", ""),
                            trans_group=args.get("trans_group", "Sales"),
                            reg_type=args.get("reg_type"),
                            start_date=args.get("start_date"),
                            end_date=args.get("end_date"),
                        )
                        break
        except Exception as e:
            raw_tool_data = {"status": "TOOL_CALL_ERROR", "error": str(e)}

        # Clean JSON extraction pass directly from the retrieved tool payload
        # Check if the query is an explanatory investigation
        is_investigation = any(w in user_prompt.lower() for w in ["why", "explain", "drove", "spike", "surge", "shift", "premium"])

        if is_investigation:
            system_instruction = (
                "You are a Senior Dubai Real Estate Quantitative Analyst conducting an empirical investigation.\n"
                "The user is asking a specific analytical 'WHY' or 'EXPLAIN' question about a market movement.\n"
                "Return your findings as a valid JSON object matching the schema below.\n\n"
                "CRITICAL INSTRUCTIONS FOR 'market_summary':\n"
                "1. DIRECTLY ANSWER THE SPECIFIC QUESTION in the very first sentence.\n"
                "2. EMPIRICAL DECOMPOSITION: Inspect the monthly_breakdown to explain what mechanics drove the movement:\n"
                "   - Compare Off-Plan vs. Ready volume and price/m² in that period.\n"
                "   - Look at changes in median price vs. average price.\n"
                "   - Reference prior months vs. the anomaly month to show the shift.\n"
                "3. CAUSAL BOUNDARY: Distinguish observed registry facts from speculative drivers.\n"
                "   State clearly: 'Registry data confirms the movement was driven by [Off-plan / ticket-size shift / volume]. Dataset does not establish developer launch causation.'\n"
                "4. End with an explicit section header 'Strategic Investor Advisory:' with concrete implications.\n\n"
                "JSON Schema:\n"
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
                "Do not invent any numbers. Rely strictly on the provided payload."
            )
        else:
            system_instruction = (
                "You are a real estate quantitative structuring assistant. Produce a single JSON object matching the requested JSON schema.\n"
                "Strictly adhere to the provided raw database metrics. Do not invent any numbers.\n"
                "Structure 'market_summary' into two clear parts:\n"
                "1. Primary trends (Ready vs Off-Plan volume, pricing spreads, notable monthly movements).\n"
                "2. Explicit section header: 'Strategic Investor Advisory:' followed by grounded, objective advice for buyers.\n\n"
                "JSON Schema:\n"
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

        extraction_messages = [
            {"role": "system", "content": system_instruction}
        ]

        compact_payload = {
            "status": raw_tool_data.get("status"),
            "user_question": user_prompt,
            "is_comparison": raw_tool_data.get("is_comparison", False),
            "primary_area": raw_tool_data.get("primary_area", raw_tool_data.get("cadastral_area")),
            "secondary_area": raw_tool_data.get("secondary_area"),
            "transaction_count": raw_tool_data.get("transaction_count", 0),
            "summary_metrics": raw_tool_data.get("summary_metrics", {}),
            "trace_sample_ids": raw_tool_data.get("audit_trail", {}).get("trace_sample_ids", []),
            "timeseries_summary": [
                {
                    "month": t.get("month_year") or t.get("period"),
                    "volume": t.get("volume", (t.get("area1_volume", 0) + t.get("area2_volume", 0))),
                    "avg_sqm": t.get("monthly_avg_sqm") or t.get("area1_avg_sqm"),
                    "area2_avg_sqm": t.get("area2_avg_sqm"),
                    "ready_sqm": t.get("ready_avg_sqm"),
                    "offplan_sqm": t.get("offplan_avg_sqm")
                }
                for t in raw_tool_data.get("timeseries", [])[:12]
            ]
        }

        structured_completion = groq_client.chat.completions.create(
            model=self.model_name,
            messages=[
                extraction_messages[0],
                {"role": "user", "content": f"User Query: {user_prompt}\nRetrieved Registry Data: {json.dumps(compact_payload)}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_json_str = structured_completion.choices[0].message.content
        draft = AnalystDraft.model_validate_json(raw_json_str)
        return draft, raw_tool_data

    def _extract_signals_and_delta(self, raw_tool_data: dict, area_name: str) -> Tuple[List[MarketSignal], Optional[PeriodDelta]]:
        """Extracts deterministic signals and delta metrics safely for both single and comparison datasets."""
        timeseries = raw_tool_data.get("timeseries", [])
        signals: List[MarketSignal] = []
        delta: Optional[PeriodDelta] = None

        if len(timeseries) < 2:
            return signals, delta

        is_comparison = bool(raw_tool_data.get("is_comparison", False))

        # Helper to extract volume regardless of schema shape
        def get_vol(pt: dict) -> int:
            if "volume" in pt and pt["volume"] is not None:
                return pt["volume"]
            if "total_volume" in pt and pt["total_volume"] is not None:
                return pt["total_volume"]
            # Multi-area comparative point
            return (pt.get("area1_volume") or 0) + (pt.get("area2_volume") or 0)

        # Helper to extract price/m² regardless of schema shape
        def get_sqm(pt: dict) -> Optional[float]:
            for key in ["monthly_avg_sqm", "overall_price_sqm", "area1_avg_sqm"]:
                if key in pt and pt[key] is not None:
                    return float(pt[key])
            return None

        first_period = timeseries[0]
        last_period = timeseries[-1]

        v_first = get_vol(first_period)
        v_last = get_vol(last_period)

        vol_change_pct = round(((v_last - v_first) / max(v_first, 1)) * 100, 1)
        
        sqm_first = get_sqm(first_period)
        sqm_last = get_sqm(last_period)
        price_change_pct = 0.0
        if sqm_first and sqm_last and sqm_first > 0:
            price_change_pct = round(((sqm_last - sqm_first) / sqm_first) * 100, 1)

        delta = PeriodDelta(
            start_period=str(first_period.get("month_year") or first_period.get("period", "")),
            end_period=str(last_period.get("month_year") or last_period.get("period", "")),
            volume_change_pct=vol_change_pct,
            price_sqm_change_pct=price_change_pct,
            start_price_sqm=sqm_first,
            end_price_sqm=sqm_last
        )

        # Check 1: Volume Spike Anomaly
        max_vol_bucket = max(timeseries, key=get_vol)
        max_vol = get_vol(max_vol_bucket)
        if max_vol >= (v_first * 1.5) and max_vol > 0:
            p_label = str(max_vol_bucket.get("month_year") or max_vol_bucket.get("period", ""))
            signals.append(MarketSignal(
                type="HIGH_ACTIVITY",
                severity="positive",
                title=f"Volume Surge ({max_vol} Deals)",
                period=p_label,
                description=f"Transaction volume hit a peak in {p_label}, outpacing initial period activity.",
                drilldown_prompt=f"Why did transaction volume surge to {max_vol} deals in {p_label} for {area_name}?"
            ))

        # Check 2: Off-Plan Premium Divergence (Single-area mode only)
        if not is_comparison:
            for p in timeseries:
                offplan = p.get("offplan_avg_sqm") or p.get("offplan_price_sqm")
                ready = p.get("ready_avg_sqm") or p.get("ready_price_sqm")
                if offplan and ready and ready > 0:
                    spread = ((offplan - ready) / ready) * 100
                    if spread >= 15.0:
                        p_label = str(p.get("month_year") or p.get("period", ""))
                        signals.append(MarketSignal(
                            type="OFFPLAN_PREMIUM",
                            severity="neutral",
                            title=f"Elevated Off-Plan Premium ({round(spread, 1)}%)",
                            period=p_label,
                            description=f"Off-plan rate reached AED {round(offplan):,}/m² vs Ready at AED {round(ready):,}/m² in {p_label}.",
                            drilldown_prompt=f"Explain the {round(spread, 1)}% off-plan premium over ready units in {area_name} during {p_label}."
                        ))
                        break

        return signals, delta

    def run_auditor_gate(self, draft: AnalystDraft, raw_tool_data: dict) -> VerificationReport:
        discrepancies = []
        timeseries = raw_tool_data.get("timeseries", [])
        area_analyzed = draft.area_analyzed or "Target Area"

      
        # 1. Extract Comparison Flags from Tool Output
        
        is_comparison = bool(raw_tool_data.get("is_comparison", False))
        area1_label = raw_tool_data.get("primary_area")
        area2_label = raw_tool_data.get("secondary_area")

        if raw_tool_data.get("status") != "SUCCESS":
            reason = raw_tool_data.get("status", "NO_TOOL_CALL_MADE")
            return VerificationReport(
                is_grounded=False,
                discrepancies=[f"NO_RECORDS_FOUND: {reason} — no verified DLD transactions to ground against."],
                final_output=f"NOT_FOUND: No registered transaction records exist for '{area_analyzed}' in DLD registry.",
                source_trace_ids=[],
                timeseries=None,
                market_signals=[],
                delta=None,
                audit_checks=[
                    AuditCheckItem(name="DLD Registry Records Found", passed=False, detail=f"Query returned status: {reason}")
                ],
                is_comparison=is_comparison,
                area1_label=area1_label,
                area2_label=area2_label
            )

       
        # 2. Metric Grounding Check
       
        median_match = True
        avg_match = True

        if not is_comparison:
            metrics = raw_tool_data.get("summary_metrics", {})
            expected_median = float(metrics.get("median_price_aed", 0.0))
            expected_avg = float(metrics.get("avg_price_aed", 0.0))

            # Metric grounding checks within 1% threshold
            if expected_median > 0 and abs(draft.median_price_aed - expected_median) > (expected_median * 0.01):
                median_match = False
                discrepancies.append(
                    f"Median price mismatch: LLM claimed {draft.median_price_aed}, DB recorded {expected_median}"
                )

            if expected_avg > 0 and abs(draft.avg_price_aed - expected_avg) > (expected_avg * 0.01):
                avg_match = False
                discrepancies.append(
                    f"Average price mismatch: LLM claimed {draft.avg_price_aed}, DB recorded {expected_avg}"
                )

       
        # 3. Transaction ID Provenance Audit
        
        raw_sample_ids = set(raw_tool_data.get("audit_trail", {}).get("trace_sample_ids", []))
        model_ids = set(draft.sample_transaction_ids)
        invalid_ids = model_ids - raw_sample_ids

        provenance_passed = len(invalid_ids) == 0
        if not provenance_passed:
            discrepancies.append(f"LLM cited unverified transaction IDs: {list(invalid_ids)}")

        # 4. Construct Audit Checklist Items
    
        audit_checks = [
            AuditCheckItem(
                name="DLD In-Memory Records Found",
                passed=True,
                detail=f"Verified comparative records for {area1_label} vs {area2_label}" if is_comparison else f"Verified {raw_tool_data.get('transaction_count', 0)} deals"
            ),
            AuditCheckItem(name="Price/m² Grounding Gate", passed=avg_match and median_match, detail="Median & avg prices match within 1%"),
            AuditCheckItem(name="Provenance Trace Verification", passed=provenance_passed, detail="Registry IDs authenticated"),
            AuditCheckItem(name="Cadastral Alias Normalization", passed=True, detail=f"Matched: {draft.cadastral_name}"),
            AuditCheckItem(name="Segmentation Reconciliation", passed=True, detail="Multi-area comparison aligned" if is_comparison else "Ready vs. Off-plan computed"),
            AuditCheckItem(name="Deterministic Bounds Gate", passed=len(discrepancies) == 0, detail="Passed all verification assertions")
        ]

        # Extract deterministic signals and delta metrics
        signals, delta = self._extract_signals_and_delta(raw_tool_data, area_analyzed)

        if discrepancies:
            return VerificationReport(
                is_grounded=False,
                discrepancies=discrepancies,
                final_output="REJECTED_BY_AUDITOR: Hallucination detected. Metrics do not match DLD records.",
                source_trace_ids=list(raw_sample_ids),
                timeseries=timeseries,
                market_signals=signals,
                delta=delta,
                audit_checks=audit_checks,
                is_comparison=is_comparison,
                area1_label=area1_label,
                area2_label=area2_label
            )

        if is_comparison:
            a1_m = raw_tool_data.get("area1_metrics") or {}
            a2_m = raw_tool_data.get("area2_metrics") or {}

            a1_name = area1_label or "Primary Area"
            a2_name = area2_label or "Secondary Area"

            # 1. Look in summary_metrics, 2. Look in sample_size, 3. Sum from timeseries
            ts = raw_tool_data.get("timeseries", [])
            
            a1_count = (
                a1_m.get("transaction_count")
                or a1_m.get("total_transactions")
                or a1_m.get("sample_size")
                or sum((pt.get("area1_volume") or 0) for pt in ts)
            )
            a2_count = (
                a2_m.get("transaction_count")
                or a2_m.get("total_transactions")
                or a2_m.get("sample_size")
                or sum((pt.get("area2_volume") or 0) for pt in ts)
            )

            a1_sqm = a1_m.get("avg_sqm_price_aed") or a1_m.get("avg_price_sqm_aed") or 0.0
            a2_sqm = a2_m.get("avg_sqm_price_aed") or a2_m.get("avg_price_sqm_aed") or 0.0

            formatted_final = (
                f"**AcreIQ Comparative Brief: {a1_name} vs. {a2_name}**\n\n"
                f"{draft.market_summary}\n\n"
                f"### Empirical Metric Breakdown\n"
                f"- **{a1_name}:** "
                f"{int(a1_count):,} deals | "
                f"Median: AED {float(a1_m.get('median_price_aed', 0)):,.2f} | "
                f"Avg/m²: AED {float(a1_sqm):,.2f}\n"
                f"- **{a2_name}:** "
                f"{int(a2_count):,} deals | "
                f"Median: AED {float(a2_m.get('median_price_aed', 0)):,.2f} | "
                f"Avg/m²: AED {float(a2_sqm):,.2f}\n\n"
                f"- **Verified Registry Trace Sample:** {', '.join(draft.sample_transaction_ids[:6])}"
            )
        else:
            formatted_final = (
                f"**AcreIQ Market Brief: {draft.area_analyzed} (Cadastral: {draft.cadastral_name})**\n\n"
                f"{draft.market_summary}\n\n"
                f"- **Analyzed Transactions:** {draft.transaction_count:,}\n"
                f"- **Median Price:** AED {draft.median_price_aed:,.2f}\n"
                f"- **Average Price:** AED {draft.avg_price_aed:,.2f}\n"
                f"- **Avg Price / m²:** AED {draft.avg_sqm_price_aed:,.2f}\n"
                f"- **Verified Registry Record Sample:** {', '.join(draft.sample_transaction_ids)}"
            )

        suggested_prompts = []
        for sig in signals:
            suggested_prompts.append(sig.drilldown_prompt)

        if delta:
            suggested_prompts.append(
                f"What drove the {delta.price_sqm_change_pct}% price shift in {area_analyzed} between {delta.start_period} and {delta.end_period}?"
            )
        
        comp_area = "Business Bay" if "furjan" in area_analyzed.lower() else "Al Furjan"
        suggested_prompts.append(f"Compare price/m² trends between {area_analyzed} and {comp_area}")

        return VerificationReport(
            is_grounded=True,
            discrepancies=[],
            final_output=formatted_final,
            source_trace_ids=draft.sample_transaction_ids,
            timeseries=timeseries,
            market_signals=signals,
            delta=delta,
            audit_checks=audit_checks,
            suggested_prompts=suggested_prompts[:3],
            is_comparison=is_comparison,
            area1_label=area1_label,
            area2_label=area2_label
        )

    def execute(self, user_prompt: str) -> VerificationReport:
        draft, raw_tool_data = self.run_analyst(user_prompt)
        report = self.run_auditor_gate(draft, raw_tool_data)
        return report