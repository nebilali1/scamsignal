"""Shared resource limits and explicit triage policy."""
MAX_CHARACTERS = 12000
MAX_MESSAGES = 80
RULE_HIGH_THRESHOLD = 55
MODEL_VERSION = "sms-lr-v1"


def triage(rule_score: int, model_flag: bool | None) -> dict:
    """Decision policy, deliberately not a blended fraud probability."""
    if rule_score >= RULE_HIGH_THRESHOLD or model_flag is True:
        return {"label": "Elevated concern", "tone": "danger", "reason": "Strong rule signals or a model spam flag warrant independent verification."}
    if rule_score > 0:
        return {"label": "Review suggested", "tone": "warning", "reason": "At least one rule matched. Context and the sender's identity still matter."}
    return {"label": "No strong signal", "tone": "neutral", "reason": "The available checks found no strong signal. This is not a safety guarantee."}
