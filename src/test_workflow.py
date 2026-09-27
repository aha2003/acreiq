# src/test_workflow.py
import json
from src.agents import AcreIQWorkflow

workflow = AcreIQWorkflow()

print("Running Query 1: Dubai Marina valuation...")
report = workflow.execute("What are the latest sales numbers and median price for apartments in Dubai Marina?")

print("\n--- AUDITOR VERIFICATION REPORT ---")
print(f"Grounded: {report.is_grounded}")
print(f"Discrepancies: {report.discrepancies}")
print(f"Source Records: {report.source_trace_ids}")
print("\n--- FINAL DELIVERED OUTPUT ---")
print(report.final_output)