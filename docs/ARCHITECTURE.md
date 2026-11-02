# Architecture and trust boundaries

## Browser edition

`web/engine.mjs` reproduces the trained word/bigram TF-IDF and logistic model in JavaScript. The build embeds the numeric model, evaluation, exported Python rule definitions, and authored scenarios into a single HTML file. Analysis uses only in-memory state, performs no network requests, and writes no localStorage, cookies, or message database. Clearing or closing the tab removes that in-memory conversation; downloaded reports remain on the device. Hosting still receives normal page requests.

Cross-language tests compare every held-out score within 1e-12 and each demo’s rule severity/first warning against Python. Browser QA verified replay, benign examples, Model Lab, learned evidence, and the responsive layout at a 390-pixel viewport. JavaScript Unicode handling is not guaranteed identical for every possible string outside tested inputs.

`python -m scripts.build_web` regenerates `web/dist/index.html`. Rebuild after changing model, rules, scenarios, evaluation, or web source; a test detects stale embedded artifacts. Static hosting deploys that build. The browser edition was added after the existing Streamlit deployment required owner-level diagnosis; it does not remove the original app.

## Streamlit runtime

A single Streamlit process serves the dashboard. The original `app.py` entrypoint, `detector.analyze`, and timeline APIs remain. There is no separate backend, external model provider, database, or account setup.

| Module | Responsibility |
|---|---|
| `app.py` | Navigation, per-session state, analysis actions, charts, evaluation display |
| `detector.py` | Eleven weighted regex rules, exact spans, per-match negation guards |
| `timeline.py` | Line parsing, input validation, message analysis, first signals, cumulative summaries |
| `ml.py` | JSON model loading, batch TF-IDF inference, signed linear feature contributions |
| `settings.py` | Input bounds and explicit hybrid triage policy |
| `presentation.py` | Escaped highlights and privacy-conscious JSON export |
| `scripts/train_model.py` | Data integrity, grouped splits, training, validation selection, test evaluation |
| `artifacts/` | Model, metrics, split manifest, and test predictions |

Model and evaluation caches hold immutable shared artifacts. Conversations are held only in session state; they are not passed to Streamlit's global data cache. Draft input is separate from submitted input, so editing cannot silently relabel old results. Navigation preserves drafts and results. Clearing removes the current conversation and report state from the app session; it does not claim to erase provider logs or downloaded files.

## Message and decision semantics

Each nonempty line is one message. A short `Sender: ` prefix is separated from content; a raw URL is not parsed as a sender. Messages are screened independently. Rules are accumulated by stable ID across the prefix, counting each rule weight once (cap 100). The first rule match and first model flag are separate fields. Replay statistics use only revealed messages.

The model returns a per-message spam score with threshold 0.49. The summary shows the maximum message score, **not** a conversation fraud probability. Triage is explicit:

| Condition | Result |
|---|---|
| Cumulative rule severity ≥55 OR any ML spam flag | Elevated concern |
| Otherwise, at least one rule match | Review suggested |
| Otherwise | No strong signal |

No strong signal never means safe. If the model is unavailable, the UI explicitly switches to rules only. Unknown-vocabulary messages produce no ML prediction; no fake confidence is inserted.

Rule evidence is exact regex text. ML evidence is `TF-IDF value × coefficient`, an additive log-odds contribution. Only the strongest terms are displayed; the intercept and other terms also affect the final output. These are associations, not causal explanations.

## Security and privacy

- Conversation text, sender labels, matched phrases, and evidence are HTML-escaped before any custom markup. Highlights merge overlapping spans.
- Links in conversations remain plain escaped text. There is no URL fetch, redirect following, attachment parsing, subprocess execution, or tool invocation based on submitted content.
- Input is capped at 12,000 characters and 80 messages. Regex patterns use bounded spans and no unbounded nested repetition.
- Model artifacts are trusted repository numeric JSON, not executable pickle. Their hash is recorded and tested.
- No chat contents are deliberately logged, saved, or sent to third-party inference APIs.
- Default analysis export excludes messages, sender names, exact evidence, and learned terms. The user can explicitly include original text. The export covers the full submitted conversation, which the UI labels even during partial replay.
- In the Streamlit edition, the provider handles network traffic and server-side inference. That edition does not provide client-only processing or a zero-retention infrastructure guarantee. The browser edition runs inference locally, as described above.
- Streamlit usage telemetry is disabled in the checked-in configuration. Provider-level telemetry is outside the app's control.

## Tests and operations

Unit tests check rule context/negation, exact spans, injection escaping, input bounds, deterministic inference, artifact identity, split isolation, metric consistency, and export privacy. AppTest exercises scenario changes, replay, navigation, custom input, empty input, clearing, and the validation explorer. GitHub Actions executes the suite on Python 3.11 and 3.12.

The app uses precomputed model artifacts, avoiding training on launch. A health endpoint is provided by Streamlit at `/_stcore/health`. Community Cloud handles serving and sleep/restart behaviour. Authentication, rate limiting, distributed sessions, audit retention, incident workflows, and operational monitoring are not implemented; those are future production requirements, not completed features.
