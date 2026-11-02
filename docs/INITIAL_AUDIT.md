# Initial repository audit

Inspected baseline commit `6e673f7bcb6e44f1bd19ecaafbe15b065fcfb8cb`, including all source files, README, requirements, workflow, and both test files. The original nine tests passed before changes. The existing live Streamlit app was asleep; it was awakened and the baseline interface verified.

| Baseline limitation | Implemented response |
|---|---|
| Rules only; no trained model, labelled data, or measured evaluation | Licensed UCI corpus, offline classifier training, grouped splits, committed model and full metrics |
| One-shot results disappear on rerun | Separate draft/submitted text and persistent session analysis |
| Any password/code/payment-service mention is suspicious | Request-oriented credential/payment rules, local negation guards, explicit edge cases |
| Regex can match across different messages | Per-message screening with bounded non-newline spans |
| First match only, no exact offsets | All evidence spans, safe overlap-aware highlighting, stable rule IDs |
| Simple expandable timeline | Message replay, first signal jump, cumulative rule track and separate ML track |
| Four short samples | Eleven fictional conversation scenarios including benign and adversarial examples |
| No evaluation transparency | Confusion matrix, precision/recall/F1, baselines, validation explorer, model card |
| Minimal presentation | Responsive dashboard, evidence panel, model term chart, designed theme |
| Limited tests | Rule, ML, privacy, replay, data integrity, and full app regression tests |
| Short README, no methodology | Architecture, threat boundaries, audit, model card, dataset attribution, demo and deployment guide |

Preserved Streamlit and the original public detector/timeline APIs. No frontend/backend migration or external inference account was required. New high-concern thresholds and dataset scope are stated explicitly, including the absence of a hybrid improvement on this particular corpus.
