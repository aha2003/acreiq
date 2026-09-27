### AcreIQ Benchmark Scorecard
*Executed on: 2026-09-27 22:23:20*

| Metric | Result | Benchmark Target |
| :--- | :--- | :--- |
| **Pass Rate** | **100.0%** (8/8) | > 90% |
| **Factual Grounding Rate** | **87.5%** | 100% on valid data |
| **Mean Latency** | **2.99s** | < 3.0s |
| **p95 Latency** | **5.89s** | < 5.0s |

#### Detailed Test Case Breakdown
| Test ID | Category | Status | Latency | Result / Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
| `tc_01` | standard_lookup | PASSED | 2.58s | Grounded to DLD registry |
| `tc_02` | alias_resolution | PASSED | 2.78s | Grounded to DLD registry |
| `tc_03` | direct_match | PASSED | 2.56s | Grounded to DLD registry |
| `tc_04` | direct_match | PASSED | 2.29s | Grounded to DLD registry |
| `tc_05` | abbreviation_alias | PASSED | 2.72s | Grounded to DLD registry |
| `tc_06` | abbreviation_alias | PASSED | 2.44s | Grounded to DLD registry |
| `tc_07` | adversarial_nonexistent | PASSED | 5.89s | Grounded to DLD registry |
| `tc_08` | direct_cadastral | PASSED | 2.67s | Grounded to DLD registry |
