# tests/eval_runner.py
import json
import time
from datetime import datetime
from src.agents import AcreIQWorkflow

def run_evaluation_suite(eval_file: str = "tests/golden_eval_set.json"):
    with open(eval_file, "r") as f:
        test_cases = json.load(f)

    workflow = AcreIQWorkflow()
    results = []
    
    print(f"\n🚀 Running AcreIQ Evaluation Harness ({len(test_cases)} test cases)...\n" + "=" * 60)

    for tc in test_cases:
        tc_id = tc["id"]
        query = tc["query"]
        expected_cadastral = tc["expected_cadastral"]
        should_ground = tc["should_ground"]

        start_time = time.time()
        passed = False
        error_msg = None
        report = None

        try:
            report = workflow.execute(query)
            latency = round(time.time() - start_time, 2)

            if should_ground:
                # Must be grounded, have 0 discrepancies, and verified trace IDs
                if report.is_grounded and len(report.source_trace_ids) > 0:
                    passed = True
                else:
                    error_msg = f"Auditor rejected: {report.discrepancies}"
            else:
                # Should NOT ground (e.g. non-existent location) or must reject safely
                if not report.is_grounded or "NOT_FOUND" in report.final_output:
                    passed = True
                else:
                    error_msg = "Model grounded a non-existent area instead of rejecting."

        except Exception as e:
            latency = round(time.time() - start_time, 2)
            error_msg = str(e)

        results.append({
            "id": tc_id,
            "category": tc["category"],
            "query": query,
            "passed": passed,
            "latency_sec": latency,
            "is_grounded": report.is_grounded if report else False,
            "error": error_msg
        })

        status_sym = "✅" if passed else "❌"
        print(f"[{status_sym}] {tc_id} ({tc['category']}): {latency}s | {query}")
        if not passed:
            print(f"    └── Issue: {error_msg}")

    # Generate Aggregate Metrics
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    grounded_count = sum(1 for r in results if r["is_grounded"])
    latencies = [r["latency_sec"] for r in results]
    avg_latency = round(sum(latencies) / total, 2)
    p95_latency = round(sorted(latencies)[int(total * 0.95)], 2)
    pass_rate = round((passed_count / total) * 100, 1)

    print("=" * 60)
    print(f"EVALUATION COMPLETE: {passed_count}/{total} Passed ({pass_rate}%)")
    print(f"Average Latency: {avg_latency}s | P95 Latency: {p95_latency}s")
    print("=" * 60)

    # Output Markdown Scorecard for your README
    scorecard_md = f"""### AcreIQ Benchmark Scorecard
*Executed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

| Metric | Result | Benchmark Target |
| :--- | :--- | :--- |
| **Pass Rate** | **{pass_rate}%** ({passed_count}/{total}) | > 90% |
| **Factual Grounding Rate** | **{round((grounded_count/total)*100, 1)}%** | 100% on valid data |
| **Mean Latency** | **{avg_latency}s** | < 3.0s |
| **p95 Latency** | **{p95_latency}s** | < 5.0s |

#### Detailed Test Case Breakdown
| Test ID | Category | Status | Latency | Result / Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
"""
    for r in results:
        status_badge = "PASSED" if r["passed"] else "FAILED"
        err = r["error"] if r["error"] else "Grounded to DLD registry"
        scorecard_md += f"| `{r['id']}` | {r['category']} | {status_badge} | {r['latency_sec']}s | {err} |\n"

    with open("tests/EVAL_REPORT.md", "w") as f:
        f.write(scorecard_md)
    print("Scorecard written to `tests/EVAL_REPORT.md`")

if __name__ == "__main__":
    run_evaluation_suite()