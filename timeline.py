"""Per-message screening for line-separated conversations."""
from detector import analyze


def split_messages(text: str) -> list[str]:
    """Treat each nonempty line as one message, preserving order."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def analyze_timeline(text: str) -> dict:
    """Find first observed warning in individual messages, not fraud probability."""
    events = []
    first_warning = None
    for index, message in enumerate(split_messages(text), start=1):
        result = analyze(message)
        events.append({
            'number': index,
            'message': message,
            'score': result['score'],
            'level': result['level'],
            'findings': result['findings'],
        })
        if first_warning is None and result['findings']:
            first_warning = index
    return {'events': events, 'first_warning': first_warning}
