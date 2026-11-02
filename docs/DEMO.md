# Recruiter demo

## 30-second pitch

“ScamSignal helps people spot where a conversation becomes suspicious. I combined a trained text classifier with an explainable rule engine, then built a timeline that shows the exact message and phrase behind each warning. The model achieved 94.5% F1 on a held-out SMS spam benchmark. I also show false positives, missed cases, and where rules and machine learning disagree—because a useful security tool needs to explain its limits.”

Use this only after reviewing the code and making sure you can explain the work. If asked about development tools, describe the AI assistance honestly and focus on the design decisions you understand and can defend.

## Live sequence

1. Open the deployed app before the conversation. Wake it if Community Cloud is asleep.
2. **Investigate → Fake job offer → Start.** The opening messages have no rule warning.
3. **First signal.** Message 3 introduces an equipment fee. Point to the exact highlight and explanation.
4. **Next message** twice. Payment-method and urgency evidence accumulate; the rule index increases without double-counting repeated rules.
5. **Model evidence.** The classifier can disagree with the rules; it was trained on older SMS spam, not all modern scams.
6. **Legitimate security advice.** Explain why “never share your password” differs from requesting one.
7. **Model lab.** Show 94.5% F1, seven false alarms, and seven misses. Mention the separate grouped train/validation/test split.
8. If there is time, show **Subtle impersonation** as a possible miss rather than pretending the system catches everything.

## How it works in plain language

The model learns which words and short phrases are associated with labelled spam. TF-IDF emphasises distinctive terms, and logistic regression combines their learned weights. The rules look for specific behaviours such as fees, requests for login codes, urgency, and remote-access demands. The app puts the two results side by side and raises concern when either crosses its explicit threshold.

## Questions you should be able to answer

**Why a small linear model?** It is fast on CPU, reproducible, inspectable, inexpensive to serve, and can explain its exact feature contributions. It does not need a large language model to establish a useful baseline.

**How did you avoid leakage?** Remove case/whitespace duplicates before splitting; keep normalised templates together; fit the vocabulary and IDF only on training messages; choose the threshold only on validation. Semantic duplicates may still remain.

**Does 94.5% mean it catches 94.5% of scams?** No. It is F1 on one older spam/ham SMS benchmark. It does not establish modern fraud-detection performance.

**Does combining rules and ML improve the benchmark?** Not on this test set. No SMS reaches the rules' high threshold, so hybrid results equal the model. The separate fictional demos illustrate coverage, not generalisation.

**What would you improve next?** Independently labelled contemporary fraud conversations, external evaluation, calibration, robust paraphrase handling, and operational monitoring with an explicit privacy policy.

**Where does the user's text go?** To the Streamlit server for inference. No external model API or message database is used. Session state retains it until cleared or expired; hosting infrastructure still processes traffic.
