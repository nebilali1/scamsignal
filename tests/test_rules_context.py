import pytest
from detector import analyze


def labels(text):
    return {f['id'] for f in analyze(text)['findings']}


@pytest.mark.parametrize('text', [
    'Never share your password.', 'Do not send me your verification code.',
    "Don't ever share your one-time code.", 'Your verification code is 123456.',
    'We will never ask you to share your password.',
    'I use Venmo for dinner with friends.',
    'There is no equipment fee.', 'The equipment fee is not required.',
])
def test_benign_context(text):
    assert not labels(text)


@pytest.mark.parametrize('text', [
    'Please send me your verification code.', 'Tell us your password.',
    "What's your recovery phrase?", 'Enter the one-time code at this link.',
    'Never share your password, but send me your verification code.',
    'Never share your password. Please give me your passcode.',
])
def test_secret_requests(text):
    assert 'credentials' in labels(text)


@pytest.mark.parametrize('text,rule_id', [
    ('Download AnyDesk so we can help.', 'remote_access'),
    ('Please return the difference to the courier.', 'refund'),
    ('Send $200 via Zelle.', 'payment'),
    ('Pay an equipment fee before you start.', 'upfront_fee'),
    ('Keep this between us.', 'secrecy'),
])
def test_behavior_coverage(text, rule_id):
    assert rule_id in labels(text)


def test_repetitions_count_once_but_preserve_all_spans():
    result = analyze('Act now! Act now!')
    assert result['score'] == 17
    assert len(result['findings'][0]['spans']) == 2


def test_offsets_are_exact_even_with_unicode():
    text = 'Hi 👋. SEND me your verification code immediately.'
    for finding in analyze(text)['findings']:
        for span in finding['spans']:
            assert text[span['start']:span['end']] == span['text']


def test_no_cross_message_request_invention():
    assert 'credentials' not in labels('Please send the notes.\nWe discussed password protection in class.')


def test_negation_does_not_suppress_secrecy():
    assert 'secrecy' in labels('Do not tell anyone about this transfer.')
