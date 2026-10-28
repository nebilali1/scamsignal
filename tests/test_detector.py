from detector import analyze

def test_job_fee():
    output = analyze('Pay an equipment fee upfront via Zelle immediately')
    assert output['score'] >= 55
    assert any(x['label'] == 'Upfront fee' for x in output['findings'])

def test_empty():
    assert analyze('  ')['findings'] == []

def test_benign():
    assert analyze('See you in class tomorrow, thanks!')['score'] == 0

def test_credentials():
    assert any(x['label'] == 'Credential request' for x in analyze('Send me your verification code')['findings'])

def test_cap():
    assert 0 <= analyze('urgent Zelle verification code guaranteed returns equipment fee upfront')['score'] <= 100
