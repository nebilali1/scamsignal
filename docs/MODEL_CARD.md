# Model card: sms-lr-v1

## Purpose and intended use

An explainable **SMS spam classifier** within ScamSignal's scam-screening demonstration. Intended for educational exploration and portfolio discussion. Its output is one signal for human review, not a finding of fraud, a sender identity check, or a basis for automatic enforcement.

## Provenance and licensing

- Source: UCI SMS Spam Collection, https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- Citation: Almeida, T. & Hidalgo, J. (2011). *SMS Spam Collection* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CC84
- UCI license listing: CC BY 4.0; https://creativecommons.org/licenses/by/4.0/
- Corpus includes contributions from Grumbletext, NUS SMS Corpus, Caroline Tagg's thesis corpus, and SMS Spam Corpus v0.1 Big, described by UCI and the original readme.
- Source bytes: 477,907. SHA-256: `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`.
- The bundled source is unmodified. Transformations are duplicate removal, template grouping, TF-IDF feature extraction, and learned model parameters. Authored demo examples are excluded from training, threshold selection, and benchmarking.

## Experiment design

1. Parse 5,574 labelled lines as UTF-8, splitting once on the first tab. Validate labels; fail on contradictory exact duplicates.
2. Canonicalise case and whitespace for exact deduplication. Remove 415 duplicates, leaving 5,159 messages.
3. Define template groups using lowercased, whitespace-normalised text with URLs, emails, numeric sequences, and punctuation normalised. This produces 5,097 groups. It is a heuristic, not semantic deduplication.
4. `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` supplies the first test fold. On the remaining pool, the first fold of a 4-fold grouped splitter with seed 43 supplies validation.
5. Fit vocabulary, document frequencies, and logistic coefficients on the 3,095 training messages only. Validation and test never contribute vocabulary or IDF.
6. Among thresholds 0.20 through 0.85 (step 0.01), choose maximum validation F1 with precision at least 0.95. Tie-break by precision then the larger threshold. Fall back to maximum F1 only if no threshold qualifies. The selected threshold is **0.49**; validation precision **95.93%**, recall **91.47%**, F1 **93.65%**.
7. Evaluate the held-out 1,032 messages without tuning against test errors. Evaluate the rule and hybrid policies on the same messages.

| Split | Ham | Spam | Total | Template groups |
|---|---:|---:|---:|---:|
| Train | 2,710 | 385 | 3,095 | 3,058 |
| Validation | 903 | 129 | 1,032 | 1,019 |
| Test | 904 | 128 | 1,032 | 1,020 |

## Model and export

`TfidfVectorizer(ngram_range=(1,2), min_df=2, max_features=16000, sublinear_tf=True, strip_accents='unicode')` yields 7,369 features. Lowercased words of at least two characters are tokens. L2 normalisation and smoothed IDF use sklearn defaults. `LogisticRegression(C=6, class_weight='balanced', solver='liblinear', max_iter=1000, random_state=42)` fits the classifier. Hyperparameters are fixed, not test-selected.

The artifact contains vocabulary, IDF values, coefficients, intercept, schema/model version, and threshold as compressed JSON. Inference reconstructs the same vectorizer and computes `sigmoid(x @ coefficients + intercept)`. No pickle or joblib deserialisation is used. Training checks numerical export parity on all test inputs, and tests independently reproduce committed predictions.

For vocabulary-free input the app abstains (`score=None`, `flag=None`) rather than showing a confident-looking prior. One held-out message meets this condition. It contributes no alert in benchmark confusion matrices; the model's numerical prior lies below the selected threshold. No calibrated fraud probability is claimed. Class weighting and deployment distribution shift limit score interpretation.

## Results and uncertainty

Test precision, recall, and F1 are each **0.9453125**. Accuracy **0.9864341**, ROC AUC **0.9877627**, average precision **0.9737133**, Brier score **0.0145205**. Brier score is reported as a benchmark score, not evidence of real-world calibration.

Matrix in `[ham, spam]` order, rows actual and columns predicted: `[[897, 7], [7, 121]]`. There are seven false alarms and seven missed spam messages.

A fixed-seed (42), 500-resample bootstrap samples test template groups with replacement, retaining all messages in each sampled group. F1 percentile interval: **[0.9163484, 0.9727374]**. This reflects only sampling variability under this benchmark and does not cover domain shift, labelling error, or model-selection uncertainty.

The rules only alert at severity ≥55; none of this test corpus reaches that threshold. Thus rules-only F1 is 0 and hybrid results equal ML results. Precision is defined as 0 when there are no positive predictions. **No hybrid advantage is established by this benchmark.** Illustrative modern-scam demos are not an independent evaluation dataset.

## Limitations

- Labels distinguish unsolicited spam from ham, not criminal fraud from legitimate communication.
- Older English SMS differs from contemporary social engineering, recruitment, support chats, long messages, and conversations.
- Dataset collection sources and linguistic mix are not representative of all populations or communication styles; no demographic fairness claim is made.
- Template grouping misses paraphrases and other semantic duplicates.
- Linear features miss intent, sarcasm, obfuscation, identity, and cross-message dependencies.
- No OOD detector is provided beyond vocabulary absence. A familiar vocabulary does not imply in-distribution input.
- The app takes the maximum message score as a conversation summary. That increases the chance of flags as message count increases; no conversation-level calibration or benchmark exists here.
- Confidence intervals do not establish deployment safety.

## Reproduction and maintenance

Run `python -m scripts.train_model` from the repository root using the pinned dependencies. Source and outputs are committed. The script validates source integrity and writes environment versions into `evaluation.json`. Re-evaluate with independently collected, contemporary, licensed fraud conversations before making any deployment-performance claim. Do not silently relabel spam scores as fraud probabilities.
