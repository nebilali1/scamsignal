"""Reproducible offline experiment: python -m scripts.train_model.

Fit vocabulary/IDF/classifier on train only. Select threshold on validation only.
Evaluate test once. Publish split hashes and per-test predictions for auditing.
"""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
import platform
import re
from pathlib import Path
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold
from detector import analyze
from settings import MODEL_VERSION, RULE_HIGH_THRESHOLD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/raw/SMSSpamCollection'
EXPECTED_SHA256 = '7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d'


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def canonical(text: str) -> str:
    return ' '.join(text.casefold().split())


def template_key(text: str) -> str:
    text = canonical(text)
    text = re.sub(r'https?://\S+|www\.\S+', ' urltoken ', text)
    text = re.sub(r'\b\S+@\S+\b', ' emailtoken ', text)
    text = re.sub(r'\d+(?:[.,:/-]\d+)*', ' numbertoken ', text)
    return ' '.join(re.sub(r'[^\w\s]', ' ', text).split())


def load_records():
    raw = DATA.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Dataset checksum differs from the documented UCI source.')
    records, seen, raw_count = [], {}, 0
    for line in raw.decode('utf-8').splitlines():
        if not line.strip():
            continue
        label, text = line.split('\t', 1)
        if label not in ('ham', 'spam'):
            raise ValueError(f'Unknown label: {label}')
        raw_count += 1
        key = canonical(text)
        if key in seen:
            if seen[key] != label:
                raise ValueError('Conflicting labels in duplicate messages')
            continue
        seen[key] = label
        records.append({'id': digest(key), 'group': digest(template_key(text)), 'text': text, 'label': int(label == 'spam')})
    return records, raw_count


def make_splits(records):
    y = np.array([r['label'] for r in records])
    groups = np.array([r['group'] for r in records])
    pool, test = next(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42).split(y, y, groups))
    train_sub, val_sub = next(StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=43).split(y[pool], y[pool], groups[pool]))
    return {'train': pool[train_sub], 'validation': pool[val_sub], 'test': test}


def metrics(y, pred, score=None):
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average='binary', zero_division=0)
    result = {'precision': float(precision), 'recall': float(recall), 'f1': float(f1),
              'accuracy': float(accuracy_score(y, pred)),
              'confusion_matrix': confusion_matrix(y, pred, labels=[0, 1]).tolist(),
              'support': int(len(y)), 'positive_count': int(sum(y))}
    if score is not None:
        result.update(roc_auc=float(roc_auc_score(y, score)), average_precision=float(average_precision_score(y, score)),
                      brier_score=float(brier_score_loss(y, score)))
    return result


def choose_threshold(y, scores):
    candidates = []
    for threshold in np.round(np.arange(.20, .851, .01), 2):
        row = metrics(y, scores >= threshold)
        candidates.append({'threshold': float(threshold), **row})
    # A declared selection rule: maximize validation F1 among >=95% precision.
    eligible = [c for c in candidates if c['precision'] >= .95]
    best = max(eligible or candidates, key=lambda c: (c['f1'], c['precision'], c['threshold']))
    return best['threshold'], candidates, bool(eligible)


def main():
    records, raw_count = load_records()
    splits = make_splits(records)
    texts = np.array([r['text'] for r in records])
    y = np.array([r['label'] for r in records])
    train, val, test = (splits[k] for k in ('train', 'validation', 'test'))
    for left, right in [('train', 'validation'), ('train', 'test'), ('validation', 'test')]:
        assert not {records[i]['group'] for i in splits[left]} & {records[i]['group'] for i in splits[right]}
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=16000,
                               lowercase=True, sublinear_tf=True, strip_accents='unicode', token_pattern=r'(?u)\b\w\w+\b')
    x_train = vectorizer.fit_transform(texts[train])
    model = LogisticRegression(C=6.0, class_weight='balanced', solver='liblinear', max_iter=1000, random_state=42)
    model.fit(x_train, y[train])
    validation_scores = model.predict_proba(vectorizer.transform(texts[val]))[:, 1]
    threshold, candidates, precision_met = choose_threshold(y[val], validation_scores)
    test_scores = model.predict_proba(vectorizer.transform(texts[test]))[:, 1]
    rule_scores = np.array([analyze(t)['score'] for t in texts[test]])
    model_pred = test_scores >= threshold
    rule_pred = rule_scores >= RULE_HIGH_THRESHOLD
    systems = {'Machine learning': metrics(y[test], model_pred, test_scores),
               'Rules only': metrics(y[test], rule_pred),
               'Hybrid policy': metrics(y[test], model_pred | rule_pred),
               'Always ham baseline': metrics(y[test], np.zeros(len(test), dtype=int))}
    bundle = {'schema_version': 1, 'model_version': MODEL_VERSION, 'threshold': threshold,
              'features': vectorizer.get_feature_names_out().tolist(), 'idf': vectorizer.idf_.tolist(),
              'coefficients': model.coef_[0].tolist(), 'intercept': float(model.intercept_[0])}
    out = ROOT / 'artifacts'
    out.mkdir(exist_ok=True)
    artifact_bytes = gzip.compress(json.dumps(bundle, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0)
    (out / 'model.json.gz').write_bytes(artifact_bytes)
    # Check exported inference against the fitted estimator on every test record.
    from ml import TextClassifier
    exported = TextClassifier(out / 'model.json.gz')
    from scipy.special import expit
    export_matrix = exported.vectorizer.transform(texts[test])
    export_scores = expit(np.asarray(export_matrix @ exported.coef).ravel() + exported.intercept)
    assert np.allclose(export_scores, test_scores, atol=1e-12)
    abstentions = int(sum(export_matrix.getnnz(axis=1) == 0))
    # Zero-vocabulary inputs are shown as unavailable by the app. They generate
    # no ML alert, equivalent to the below-threshold prior in this artifact.
    assert float(expit(exported.intercept)) < threshold
    with (out / 'test_predictions.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'label', 'model_score', 'rule_score'])
        writer.writerows((records[i]['id'], int(y[i]), float(p), int(s)) for i, p, s in zip(test, test_scores, rule_scores))
    with (out / 'split_manifest.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'template_group', 'label', 'split'])
        for split, indices in splits.items():
            writer.writerows((records[i]['id'], records[i]['group'], records[i]['label'], split) for i in indices)
    # Group-bootstrap interval, resampling template groups instead of individual messages.
    rng = np.random.default_rng(42)
    test_groups = np.array([records[i]['group'] for i in test])
    groups = np.unique(test_groups)
    group_indices = {g: np.flatnonzero(test_groups == g) for g in groups}
    bootstrap = []
    for _ in range(500):
        selected = np.concatenate([group_indices[g] for g in rng.choice(groups, len(groups), replace=True)])
        bootstrap.append(metrics(y[test][selected], model_pred[selected])['f1'])
    report = {'schema_version': 1, 'model_version': MODEL_VERSION,
              'dataset': {'name': 'UCI SMS Spam Collection', 'url': 'https://archive.ics.uci.edu/dataset/228/sms+spam+collection',
                          'doi': '10.24432/C5CC84', 'license': 'CC BY 4.0', 'sha256': EXPECTED_SHA256,
                          'raw_rows': raw_count, 'unique_rows': len(records), 'duplicates_removed': raw_count - len(records),
                          'template_groups': len({r['group'] for r in records})},
              'splits': {name: {'total': len(idx), 'spam': int(sum(y[idx])), 'ham': int(sum(1-y[idx])),
                                'groups': len({records[i]['group'] for i in idx})} for name, idx in splits.items()},
              'split_method': 'StratifiedGroupKFold: outer 5 folds (seed 42), first test fold; inner 4 folds (seed 43), first validation fold.',
              'threshold': threshold, 'threshold_policy': 'Maximum validation F1 among thresholds 0.20–0.85 with precision >= 0.95; fall back to maximum F1 if none qualify.',
              'validation_precision_target_met': precision_met,
              'validation': metrics(y[val], validation_scores >= threshold, validation_scores),
              'validation_thresholds': [{k:c[k] for k in ('threshold','precision','recall','f1')} for c in candidates],
              'systems': systems, 'f1_group_bootstrap_95': [float(x) for x in np.quantile(bootstrap, [.025, .975])],
              'features': len(bundle['features']), 'zero_vocabulary_test_inputs': abstentions,
              'model_sha256': hashlib.sha256(artifact_bytes).hexdigest(),
              'training': {'vectorizer': 'TF-IDF word unigrams + bigrams; min_df=2; max_features=16000; sublinear_tf=True; unicode accent stripping',
                           'classifier': 'LogisticRegression(C=6, class_weight=balanced, solver=liblinear, random_state=42)',
                           'python': platform.python_version(), 'sklearn': sklearn.__version__, 'numpy': np.__version__},
              'limitations': ['Spam labels are a proxy, not verified fraud labels.',
                             'Older English SMS data does not establish performance on modern phishing, long conversations, or other languages.',
                             'Template normalization reduces leakage but cannot eliminate semantic near-duplicates.',
                             'Scores are not calibrated fraud probabilities; class weighting changes their interpretation.',
                             'Hybrid policy is a heuristic OR of model spam flag and rule severity >=55; conversation aggregation is not evaluated by this SMS benchmark.',
                             'Demo scenarios are authored examples, separate from all training and reported benchmark data.']}
    (out / 'evaluation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'splits': report['splits'], 'threshold': threshold, 'systems': systems,
                      'f1_group_bootstrap_95': report['f1_group_bootstrap_95'], 'features': report['features']}, indent=2))


if __name__ == '__main__':
    main()
