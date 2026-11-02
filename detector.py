"""Explainable rules with exact evidence offsets and local negation handling.

Weights are a severity index, never a probability. Rules cannot establish
intent, identity, or whether a link is safe.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    category: str
    weight: int
    pattern: str
    explanation: str
    next_step: str


SECRET = r"(?:password|passcode|one[ -]time (?:code|password)|verification code|otp|2fa code|security code|login credentials|seed phrase|recovery phrase)"
PAYMENT = r"(?:zelle|cash ?app|venmo|gift cards?|crypto(?:currency)?|bitcoin|wire transfer|western union)"
RULES = [
    Rule("upfront_fee", "Upfront fee", "Financial request", 28,
         r"\b(?:pay|send|deposit|transfer|purchase)\b[^\n.!?;]{0,85}\b(?:equipment|training|application|processing|activation|registration|onboarding|upfront|before you start)\b|\b(?:equipment|training|application|processing|activation|registration|onboarding|upfront)\b[^\n.!?;]{0,55}\b(?:fee|payment|deposit)\b",
         "Payment tied to unlocking a job, prize, or opportunity is a common advance-fee pattern.",
         "Pause payment and confirm the opportunity through an independently found company contact."),
    Rule("urgency", "Urgent deadline", "Pressure", 17,
         r"\b(?:within (?:the next )?\d+ (?:minutes?|hours?)|act now|right now|immediately|today only|last chance|final notice|urgent|before midnight|expires? today)\b",
         "A short deadline can pressure someone to act before checking a claim. Ordinary reminders can also be urgent.",
         "Take time to verify the request through a separate, trusted channel."),
    Rule("payment", "Unusual payment", "Financial request", 22,
         rf"\b(?:pay|send|transfer|buy|purchase|deposit)\b[^\n.!?;]{{0,65}}\b{PAYMENT}\b|\b{PAYMENT}\b[^\n.!?;]{{0,25}}\b(?:only|required|payment|deposit)\b",
         "A requested transfer or gift-card purchase can be difficult to reverse. The payment method alone is not evidence of fraud.",
         "Verify the recipient and purpose independently before sending money or gift-card codes."),
    Rule("credentials", "Credential request", "Account takeover", 35,
         rf"\b(?:send|share|tell|reply|provide|give|enter|forward|need|confirm)\b[^\n.!?;]{{0,65}}?\b{SECRET}\b|\bwhat(?:'s| is) your {SECRET}\b",
         "This language asks for an authentication secret. An unsolicited request to reveal a code can enable account takeover.",
         "Do not reveal codes or passwords to the sender. Open the service's official app directly."),
    Rule("secrecy", "Secrecy request", "Manipulation", 16,
         r"\b(?:keep this (?:between us|secret|confidential)|don.t tell|do not tell|tell no one|no one else should know)\b",
         "Secrecy can isolate a recipient from advice, although legitimate confidential conversations also exist.",
         "Ask a trusted person to review the request before acting."),
    Rule("threat", "Threat of consequences", "Pressure", 19,
         r"\b(?:arrested|lawsuit|legal action|account (?:will be )?suspended|account (?:will be )?closed|police will|avoid (?:a )?penalty|face charges)\b",
         "Threats of losing access or facing penalties can be used to force compliance.",
         "Check the claim through the organization's official app or published number."),
    Rule("off_platform", "Off-platform contact", "Identity verification", 12,
         r"\b(?:message me on telegram|contact me on whatsapp|move (?:this|our) chat to|continue on telegram|continue on whatsapp)\b",
         "Moving a conversation can remove marketplace or platform protections; it is not inherently malicious.",
         "Keep communication on the original verified platform while checking identity."),
    Rule("returns", "Guaranteed returns", "Investment claim", 25,
         r"\b(?:guaranteed (?:profits?|returns?|income)|risk.free investment|double your money|100% return|zero risk)\b",
         "Promises of risk-free investment profits are a common persuasion tactic.",
         "Independently check the firm and investment claim before transferring funds."),
    Rule("verification_link", "Link verification prompt", "Identity verification", 14,
         r"\b(?:click (?:this|the) link|verify (?:your )?account|confirm (?:your )?identity|update (?:your )?payment details)\b",
         "A verification prompt can steer someone to a phishing page. This check does not visit or establish the reputation of any URL.",
         "Open the official app or type a known address instead of following the message link."),
    Rule("remote_access", "Remote access request", "Device access", 30,
         r"\b(?:install|download|open)\b[^\n.!?;]{0,40}\b(?:anydesk|teamviewer|remote access)\b|\b(?:give|grant|allow)\b[^\n.!?;]{0,30}\bremote (?:access|control)\b",
         "Unsolicited remote-access requests may give a stranger control of a device.",
         "Do not grant access. Contact support using a number you locate independently."),
    Rule("refund", "Refund or overpayment", "Financial request", 28,
         r"\b(?:refund|return|send|wire)\b[^\n.!?;]{0,55}\b(?:difference|overpayment|excess|extra money)\b",
         "Sending back a supposed overpayment before the original payment settles is a common refund-scam pattern.",
         "Ask your bank or payment provider to verify settlement through its official support channel."),
]
_COMPILED = [(rule, re.compile(rule.pattern, re.IGNORECASE)) for rule in RULES]
_NEGATED = re.compile(r"\b(?:never|do not|don't|dont|must not|should not|shouldn't|won't|will not|no need to|not required to|avoid)\s+(?:(?:ever|again|ask you to|need to)\s+)*$", re.I)


def _is_safety_advice(text: str, start: int, end: int, rule_id: str) -> bool:
    # Suppress only the current match, not an entire message. A malicious clause
    # after "but" must still be detected. Never erase a true secrecy request.
    if rule_id == "secrecy":
        return False
    prefix = re.split(r"[.!?;\n]|\b(?:but|however)\b", text[:start], flags=re.I)[-1][-90:]
    if _NEGATED.search(prefix):
        return True
    if rule_id == "upfront_fee":
        if re.match(r"\s+(?:is |are )?(?:not required|not needed|waived|never required)\b", text[end:end + 28], re.I):
            return True
        if re.search(r"\b(?:no|without|waive(?:d)?)\s+(?:an?\s+)?$", prefix, re.I):
            return True
    return False


def analyze(text: str) -> dict:
    """Preserve the original API; add stable IDs and exact evidence spans."""
    if not text or not text.strip():
        return {"score": 0, "level": "No text", "findings": [], "summary": "Paste a conversation to begin."}
    findings = []
    for rule, pattern in _COMPILED:
        spans = [{"start": m.start(), "end": m.end(), "text": m.group()}
                 for m in pattern.finditer(text)
                 if not _is_safety_advice(text, m.start(), m.end(), rule.id)]
        if spans:
            findings.append({"id": rule.id, "label": rule.label, "category": rule.category,
                             "weight": rule.weight, "evidence": spans[0]["text"], "spans": spans,
                             "explanation": rule.explanation, "next_step": rule.next_step})
    score = min(100, sum(f["weight"] for f in findings))
    level = "High concern" if score >= 55 else "Review carefully" if score >= 25 else "Low signals detected"
    summary = ("Multiple concerning patterns were detected." if score >= 55 else
               "Some configured warning signs were found; verify the context." if findings else
               "No configured rules matched. This does not prove the message is safe.")
    return {"score": score, "level": level, "findings": findings, "summary": summary}
