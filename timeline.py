"""Message evidence and a clearly separated hybrid triage policy."""
import re
from detector import analyze
from settings import MAX_CHARACTERS, MAX_MESSAGES, triage


def split_messages(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_message(line: str) -> tuple[str, str]:
    match = re.match(r"^([\w .'-]{1,32}):\s+(.+)$", line)
    return (match[1], match[2]) if match else ("Message", line)


def validate_input(text: str) -> None:
    if not text.strip():
        raise ValueError("Add a message or select a demo to begin.")
    if len(text) > MAX_CHARACTERS:
        raise ValueError(f"Use {MAX_CHARACTERS:,} characters or fewer.")
    if len(split_messages(text)) > MAX_MESSAGES:
        raise ValueError(f"Use {MAX_MESSAGES} messages or fewer (one per nonempty line).")


def analyze_timeline(text: str, classifier=None) -> dict:
    """Cumulative rules count each rule once; ML aggregation is a maximum.

    The maximum message score is not a calibrated conversation probability.
    Earlier evidence never depends on future messages.
    """
    lines = split_messages(text)
    parsed = [parse_message(line) for line in lines]
    predictions = classifier.predict_many([body for _, body in parsed]) if classifier else [None] * len(lines)
    events, seen = [], {}
    first_warning = first_model_flag = None
    peak_model = None
    for index, ((sender, body), prediction) in enumerate(zip(parsed, predictions), 1):
        result = analyze(body)
        new_ids = [f["id"] for f in result["findings"] if f["id"] not in seen]
        for finding in result["findings"]:
            seen.setdefault(finding["id"], {**finding, "first_message": index})
        if first_warning is None and result["findings"]:
            first_warning = index
        if prediction and prediction["score"] is not None:
            peak_model = max(peak_model or 0, prediction["score"])
            if prediction["flag"] and first_model_flag is None:
                first_model_flag = index
        cumulative = min(100, sum(f["weight"] for f in seen.values()))
        events.append({"number": index, "sender": sender, "message": body, **result,
                       "new_rule_ids": new_ids, "cumulative_score": cumulative,
                       "model": prediction, "peak_model_score": peak_model,
                       "triage": triage(cumulative, first_model_flag is not None if classifier else None)})
    flags = [n for n in (first_warning, first_model_flag) if n is not None]
    return {"events": events, "first_warning": first_warning, "first_model_flag": first_model_flag,
            "first_signal": min(flags) if flags else None, "findings": list(seen.values()),
            "score": events[-1]["cumulative_score"] if events else 0, "peak_model_score": peak_model,
            "triage": events[-1]["triage"] if events else triage(0, None)}
