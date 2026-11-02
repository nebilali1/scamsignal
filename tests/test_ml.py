import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from ml import TextClassifier
from scripts.train_model import load_records, make_splits

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def model():
    return TextClassifier()


def test_model_learned_and_bounded(model):
    ordinary = model.predict('See you in class tomorrow. Thanks for the notes!')
    spam = model.predict('Congratulations! You have won a FREE prize. Call now to claim your cash reward!')
    assert 0 <= ordinary['score'] < spam['score'] <= 1
    assert spam['flag'] is True
    assert len(model.features) > 1000


def test_unknown_or_empty_input_abstains(model):
    for text in ['', '   ', '🦊🦊🦊', 'qxzvvq qxzvvq']:
        result = model.predict(text)
        assert result['score'] is None and result['flag'] is None
    assert model.predict_many([]) == []


def test_batch_and_single_match(model):
    messages = ['Hello friend, see you tomorrow.', 'Free prize! Call now to claim.']
    assert model.predict_many(messages) == [model.predict(t) for t in messages]


def test_linear_explanation_matches_model(model):
    text = 'Claim your free prize now'
    row = dict(model.vectorize(text))
    assert model.predict(text)['score'] == pytest.approx(model.raw_score(text), abs=1e-12)
    for term in model.predict(text)['terms']:
        i = model.vocabulary[term['term']]
        assert term['contribution'] == pytest.approx(row[i] * model.coef[i])


def test_artifact_checksum_and_schema():
    report = json.loads((ROOT/'artifacts/evaluation.json').read_text())
    assert hashlib.sha256((ROOT/'artifacts/model.json.gz').read_bytes()).hexdigest() == report['model_sha256']
    with gzip.open(ROOT/'artifacts/model.json.gz','rt') as f:
        artifact = json.load(f)
    assert artifact['threshold'] == report['threshold']


def test_splits_have_no_duplicate_or_template_leakage():
    frame = pd.read_csv(ROOT/'artifacts/split_manifest.csv')
    assert frame.id.is_unique
    assert frame.groupby('template_group')['split'].nunique().max() == 1
    records, _ = load_records()
    splits = make_splits(records)
    for split, idx in splits.items():
        assert {records[i]['id'] for i in idx} == set(frame.loc[frame.split == split,'id'])


def test_report_matches_committed_predictions():
    frame = pd.read_csv(ROOT/'artifacts/test_predictions.csv')
    report = json.loads((ROOT/'artifacts/evaluation.json').read_text())
    pred = frame.model_score >= report['threshold']
    metrics = report['systems']['Machine learning']
    assert confusion_matrix(frame.label,pred).tolist() == metrics['confusion_matrix']
    p,r,f,_ = precision_recall_fscore_support(frame.label,pred,average='binary')
    assert [p,r,f] == pytest.approx([metrics[k] for k in ['precision','recall','f1']])


def test_all_held_out_predictions_reproduce(model):
    records,_ = load_records()
    by_id = {r['id']:r for r in records}
    frame = pd.read_csv(ROOT/'artifacts/test_predictions.csv')
    texts = [by_id[i]['text'] for i in frame.id]
    raw = np.array([model.raw_score(t) for t in texts])
    assert np.allclose(raw,frame.model_score,atol=1e-12, rtol=0)


def test_validation_threshold_matches_declared_selection():
    report = json.loads((ROOT/'artifacts/evaluation.json').read_text())
    eligible = [x for x in report['validation_thresholds'] if x['precision'] >= .95]
    chosen = max(eligible,key=lambda x:(x['f1'],x['precision'],x['threshold']))
    assert report['threshold'] == chosen['threshold']


def test_portable_vectorizer_matches_sklearn_on_unicode_and_repetitions(model):
    from sklearn.feature_extraction.text import TfidfVectorizer
    reference = TfidfVectorizer(vocabulary=model.vocabulary,ngram_range=(1,2),sublinear_tf=True,strip_accents='unicode')
    reference.idf_ = np.array(model.idf)
    for text in ['FREE free FREE prize!!', 'Café résumé verification code', 'Hi 👋, confirm your account.', '١٢٣ 123 CASH now', 'Never share your password, but send me your code.']:
        row = reference.transform([text]).getrow(0)
        expected = dict(zip(row.indices,row.data))
        actual = dict(model.vectorize(text))
        assert actual.keys() == expected.keys()
        for i in expected:
            assert actual[i] == pytest.approx(expected[i],abs=1e-12)


def test_corrupt_model_fails_clearly(tmp_path):
    bundle = {'schema_version':1,'model_version':'broken','threshold':.5,'features':['foo'],'idf':[1.0],'coefficients':[float('nan')],'intercept':0}
    path = tmp_path/'broken.json.gz'
    with gzip.open(path,'wt') as f:
        json.dump(bundle,f)
    with pytest.raises(ValueError,match='Invalid numeric'):
        TextClassifier(path)
