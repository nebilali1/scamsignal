# Release verification — November 2, 2026

Public demo: https://scamsignal-ai-nebil.recentcrown.chatgpt.site/

## Automated checks

- 70 local tests pass, with Node installed so browser checks execute.
- Python correctness lint passes (`ruff --select E9,F63,F7,F82,F401`).
- All 1,032 held-out browser model scores match the committed Python predictions within 1e-12.
- All 11 authored scenarios match Python rule severity, first-warning location, and peak model score.
- GitHub Actions runs the complete suite on Python 3.11 and 3.12 with Node 22. See the current workflow badge and run details for CI status.

## Actual browser checks

The public deployment was opened and used after publishing. The same build was inspected in a 390-pixel-wide frame before publishing.

- Fake job offer: severity 83, four rule patterns, first signal at message 3; model peak 48.1%, below its 49% threshold.
- Replay: Start reveals the opening only; First signal jumps to the equipment fee; later messages add payment, pressure, and secrecy evidence.
- Legitimate security advice: zero rule severity, no first rule warning.
- Custom input: “Never share your password” followed by a request for a verification code raises the warning at message 2, not message 1.
- Model evidence: learned signed word contributions can be inspected separately from rule explanations.
- Model Lab: confusion matrix `[[897,7],[7,121]]`; 94.5% precision, recall, and F1 on the held-out SMS test set.
- Moving the validation explorer to 0.85 changes validation precision to 100.0% and recall to 78.3%, while the deployed threshold remains 0.49 and held-out metrics remain unchanged.
- How it works: architecture, benchmark scope, attribution, privacy, and demo guidance render correctly.

Screenshots in `docs/screenshots/` show the published application, not design mockups.

## Deployment limitation

The original Streamlit URL showed “Oh no. Error running app” after its dependency and runtime updates. Owner-only management access is needed to inspect that host's logs and reboot it. The Python app is preserved and passes application tests; the public browser edition is ready to demonstrate independently of that host.

These checks establish a functioning portfolio demonstration. They do not establish production fraud-detection effectiveness or guaranteed hosting uptime.
