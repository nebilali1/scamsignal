from timeline import analyze_timeline, split_messages


def test_line_split_removes_blank_lines():
    assert split_messages('Hello\n\nPay now\n') == ['Hello', 'Pay now']


def test_first_warning_is_second_message():
    result = analyze_timeline('Hi! How are you?\nPay an equipment fee upfront via Zelle.')
    assert result['first_warning'] == 2
    assert result['events'][0]['findings'] == []
    assert result['events'][1]['findings']


def test_no_warning():
    assert analyze_timeline('Hi!\nSee you tomorrow.')['first_warning'] is None


def test_empty_timeline():
    assert analyze_timeline('  \n\n')['events'] == []
