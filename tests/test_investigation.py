import json
import pytest
from examples import EXAMPLES
from ml import TextClassifier
from presentation import build_report, highlight
from timeline import analyze_timeline, validate_input, parse_message
from detector import analyze
from settings import triage


@pytest.mark.parametrize('text', ['', 'x'*12001, '\n'.join(['Hi']*81)])
def test_input_bounds(text):
    with pytest.raises(ValueError):
        validate_input(text)


def test_valid_boundary():
    validate_input('x'*12000)
    validate_input('\n'.join(['Hi']*80))


def test_sender_prefix_and_url():
    assert parse_message('Recruiter: Hi there') == ('Recruiter','Hi there')
    assert parse_message('https://example.com') == ('Message','https://example.com')


def test_replay_no_future_leakage():
    text = EXAMPLES['Fake job offer']
    model = TextClassifier()
    whole = analyze_timeline(text,model)
    for n in range(1,len(whole['events'])+1):
        prefix = analyze_timeline('\n'.join(text.splitlines()[:n]),model)
        assert whole['events'][:n] == prefix['events']
    assert whole['first_warning'] == 3


def test_duplicate_rules_dont_inflate_cumulative_score():
    result = analyze_timeline('A: Act now\nA: Act now\nA: Act now')
    assert [e['cumulative_score'] for e in result['events']] == [17,17,17]


def test_model_failure_degrades_to_rules():
    result = analyze_timeline(EXAMPLES['Fake job offer'],None)
    assert result['triage']['label'] == 'Elevated concern'
    assert all(e['model'] is None for e in result['events'])
    assert result['peak_model_score'] is None


def test_html_injection_is_escaped_and_never_linked():
    text = '<script>alert(1)</script> Send your password to https://bad.example'
    output = highlight(text,analyze(text)['findings'])
    assert '<script>' not in output and '&lt;script&gt;' in output
    assert '<a ' not in output
    assert '<mark>' in output


def test_overlapping_spans_are_merged():
    assert highlight('abcdefgh', [{'spans':[{'start':1,'end':4},{'start':3,'end':6}]}]) == 'a<mark>bcdef</mark>gh'


def test_default_report_excludes_sensitive_text():
    result = analyze_timeline('PRIVATE SENDER: Send me your verification code 123456 immediately')
    report = build_report(result)
    assert 'PRIVATE SENDER' not in report and '123456' not in report
    assert 'spans' not in report and 'evidence' not in report
    full = json.loads(build_report(result,True))
    assert '123456' in full['messages'][0]['text']


@pytest.mark.parametrize('score,flag,expected', [(55,False,'Elevated concern'),(0,True,'Elevated concern'),(22,False,'Review suggested'),(0,None,'No strong signal')])
def test_explicit_hybrid_policy(score,flag,expected):
    assert triage(score,flag)['label'] == expected
