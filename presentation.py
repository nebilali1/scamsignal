"""Safe display helpers. All conversation text is HTML-escaped before markup."""
from html import escape
import json


def highlight(text: str, findings: list[dict]) -> str:
    spans = sorted((s['start'], s['end']) for f in findings for s in f.get('spans', []))
    merged = []
    for start, end in spans:
        if not 0 <= start < end <= len(text):
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    result, cursor = [], 0
    for start, end in merged:
        result += [escape(text[cursor:start]), '<mark>' + escape(text[start:end]) + '</mark>']
        cursor = end
    result.append(escape(text[cursor:]))
    return ''.join(result)


def build_report(result: dict, include_text: bool = False) -> str:
    """Default export excludes original text, evidence phrases, and learned terms."""
    report = {
        'product': 'ScamSignal AI', 'scope': 'Educational screening, not a fraud verdict',
        'triage': result['triage']['label'], 'rule_severity': result['score'],
        'peak_message_model_score': result['peak_model_score'],
        'model_score_meaning': 'Maximum SMS spam score; not a conversation fraud probability',
        'first_rule_warning': result['first_warning'], 'first_model_flag': result['first_model_flag'],
        'message_count': len(result['events']),
        'findings': [{k: f[k] for k in ('id','label','category','weight','first_message','explanation','next_step')} for f in result['findings']],
        'includes_original_text': include_text,
    }
    if include_text:
        report['messages'] = [{'sender': e['sender'], 'text': e['message']} for e in result['events']]
    return json.dumps(report, indent=2, ensure_ascii=False)
