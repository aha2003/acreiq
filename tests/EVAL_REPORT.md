### AcreIQ Benchmark Scorecard
*Executed on: 2026-10-05 18:11:47*

| Metric | Result | Benchmark Target |
| :--- | :--- | :--- |
| **Pass Rate** | **100.0%** (8/8) | > 90% |
| **Factual Grounding Rate** | **87.5%** | 100% on valid data |
| **Mean Latency** | **6.91s** | < 3.0s |
| **p95 Latency** | **10.66s** | < 5.0s |

#### Detailed Test Case Breakdown
| Test ID | Category | Status | Latency | Result / Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
| `tc_01` | standard_lookup | PASSED | 4.59s | Grounded to DLD registry |
| `tc_02` | alias_resolution | PASSED | 8.72s | Grounded to DLD registry |
| `tc_03` | direct_match | PASSED | 6.95s | Grounded to DLD registry |
| `tc_04` | direct_match | PASSED | 7.77s | Grounded to DLD registry |
| `tc_05` | abbreviation_alias | PASSED | 10.66s | Grounded to DLD registry |
| `tc_06` | abbreviation_alias | PASSED | 6.56s | Grounded to DLD registry |
| `tc_07` | adversarial_nonexistent | PASSED | 5.24s | Grounded to DLD registry |
| `tc_08` | direct_cadastral | PASSED | 4.77s | Grounded to DLD registry |
