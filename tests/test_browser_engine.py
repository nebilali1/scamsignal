"""Cross-language parity: the browser serves the actual trained model."""
import gzip
import json
from dataclasses import asdict
from pathlib import Path
import re
import shutil
import subprocess
import numpy as np
import pandas as pd
import pytest
from detector import RULES
from examples import EXAMPLES, SCENARIOS
from ml import TextClassifier
from scripts.train_model import load_records
from timeline import analyze_timeline

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def browser_results():
    if not shutil.which('node'):
        pytest.skip('Node is required for browser-engine parity checks')
    records,_=load_records()
    by_id={r['id']:r['text'] for r in records}
    frame=pd.read_csv(ROOT/'artifacts/test_predictions.csv')
    texts=[by_id[i] for i in frame.id]
    run=subprocess.run(['node','scripts/check_web.mjs'],input=json.dumps({'texts':texts}),text=True,capture_output=True,cwd=ROOT,check=True)
    return json.loads(run.stdout),frame


def test_all_test_predictions_match_in_browser(browser_results):
    result,frame=browser_results
    assert np.allclose(result['scores'],frame.model_score,atol=1e-12,rtol=0)


def test_browser_and_python_scenarios_match(browser_results):
    result,_=browser_results
    for name,text in EXAMPLES.items():
        expected=analyze_timeline(text,TextClassifier())
        actual=result['scenarios'][name]
        assert actual['score']==expected['score']
        assert actual['first']==expected['first_warning']
        assert actual['modelPeak']==pytest.approx(expected['peak_model_score'],abs=1e-12)


def test_browser_replay_has_no_future_leakage(browser_results):
    assert browser_results[0]['prefixSafe']


def test_browser_privacy_and_escaping(browser_results):
    result,_=browser_results
    assert '<script>' not in result['escaped']
    assert '&lt;script&gt;' in result['escaped']
    assert 'PRIVATE' not in result['defaultReport'] and '123456' not in result['defaultReport']
    assert '123456' in result['fullReport']


def test_browser_guards_and_unknown_text(browser_results):
    result,_=browser_results
    assert all(result['invalid'])
    assert result['unknown']['score'] is None
    assert 'credentials' in result['safety']


def test_browser_bundle_uses_current_artifacts():
    html=(ROOT/'web/dist/index.html').read_text()
    data=json.loads(re.search(r'<script id="scamsignal-data" type="application/json">(.*?)</script>',html,re.S)[1])
    with gzip.open(ROOT/'artifacts/model.json.gz','rt') as f:
        assert data['model']==json.load(f)
    assert data['evaluation']==json.loads((ROOT/'artifacts/evaluation.json').read_text())
    assert data['rules']==[asdict(rule) for rule in RULES]
    assert data['scenarios']==SCENARIOS
