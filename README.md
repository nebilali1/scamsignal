# ScamSignal

**Explainable screening for suspicious messages and conversations.**

ScamSignal is a privacy-minded Streamlit prototype that lets people paste a text message, job offer, or conversation and inspect recognizable warning signs such as upfront payments, coercive deadlines, code requests, and unverified account links.

## What makes it useful
- Interactive demo with four preset scenarios and custom text input
- Pattern-by-pattern explanations, matched excerpts, and practical verification guidance
- No API key and no database; works locally
- Automated tests for key behavior
- Transparent limitations: heuristic score is **not** an ML confidence or probability of fraud

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Test it with `python -m pytest -q`.

## Architecture
`app.py` (user interface) → `detector.py` (regular-expression rule engine) → explanation and suggestions. `examples.py` holds four examples.

## Responsible use
This is not a fraud verdict or production-grade detection system. It can produce false positives or false negatives and shouldn't be used as the sole basis to block, accuse, or report a person. Avoid entering sensitive details. Messages are not intentionally stored by the app, but deployment infrastructure may log traffic.

## Future roadmap
- Evaluate a trained text classifier on appropriately licensed, labeled data
- Compare rule-based vs. learned detection with held-out precision, recall, and calibration
- Add conversation timeline highlighting and exportable redacted reports
- Conduct user testing and threat-model the interface

## Recruiter demo (30 seconds)
1. Select the fake job offer sample and click **Analyze conversation**.
2. Expand the upfront-fee finding and explain exactly what fired.
3. Select the ordinary conversation and show how it avoids those specific rule triggers.
4. Explain that this baseline creates an interpretable foundation for later ML research.
