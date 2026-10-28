"""Transparent, rule-based scam conversation screening.

This is an educational triage tool, not a trained classifier or conclusive verdict.
"""
from dataclasses import dataclass, asdict
import re

@dataclass(frozen=True)
class Rule:
    label: str
    category: str
    weight: int
    pattern: str
    explanation: str
    next_step: str

RULES = [
    Rule('Upfront fee', 'Financial request', 28, r'\b(?:pay|send|deposit|transfer|fee|purchase)\b.{0,85}\b(?:equipment|training|application|processing|activation|registration|onboarding|upfront|before you start)\b|\b(?:equipment|training|application|processing|activation|registration|onboarding|upfront)\b.{0,85}\b(?:fee|payment|deposit)\b', 'A demand for money before a promised opportunity is a common scam pattern.', 'Do not send money. Confirm the opportunity using an independently located company contact.'),
    Rule('Urgent deadline', 'Pressure', 17, r'\b(?:within (?:the next )?\d+ (?:minutes?|hours?)|act now|right now|immediately|today only|last chance|final notice|urgent|before midnight|expires? today)\b', 'Urgency can discourage verification and careful decisions.', 'Slow down and independently confirm any deadline.'),
    Rule('Unusual payment', 'Financial request', 22, r'\b(?:zelle|cash app|cashapp|venmo|gift cards?|crypto(?:currency)?|bitcoin|wire transfer|western union)\b', 'Some payment methods can be hard to reverse or are frequently abused by scammers.', 'Use official payment channels and confirm the recipient before transferring funds.'),
    Rule('Credential request', 'Account takeover', 30, r'\b(?:password|passcode|one.time code|verification code|otp|2fa code|security code|login credentials|seed phrase|recovery phrase)\b', 'Requests for login secrets or one-time codes can indicate account takeover attempts.', 'Never share passwords or authentication codes through an unsolicited message.'),
    Rule('Secrecy request', 'Manipulation', 16, r'\b(?:keep this (?:between us|secret|confidential)|don.t tell|do not tell|tell no one|no one else should know)\b', 'A request for secrecy can isolate the recipient from trusted advice.', 'Ask a trusted person to review the message.'),
    Rule('Threat of consequences', 'Pressure', 19, r'\b(?:arrested|lawsuit|legal action|account (?:will be )?suspended|account (?:will be )?closed|police will|avoid (?:a )?penalty|face charges)\b', 'Threats and penalties can be used to force immediate compliance.', 'Verify the claim through an official website or published phone number.'),
    Rule('Off-platform contact', 'Identity verification', 12, r'\b(?:message me on telegram|contact me on whatsapp|move (?:this|our) chat to|continue on telegram|continue on whatsapp)\b', 'Moving conversations to another platform can reduce platform protections.', 'Keep communication on the original verified channel while checking identity.'),
    Rule('Guaranteed returns', 'Investment claim', 25, r'\b(?:guaranteed (?:profits?|returns?|income)|risk.free investment|double your money|100% return|zero risk)\b', 'Claims of guaranteed investment returns are a serious warning sign.', 'Do not invest based on unsolicited guarantees; verify registration and disclosures.'),
    Rule('Link verification prompt', 'Identity verification', 14, r'\b(?:click (?:this|the) link|verify (?:your )?account|confirm (?:your )?identity|update (?:your )?payment details)\b', 'Unsolicited links requesting verification may lead to phishing sites.', 'Open the official site directly rather than using a message link.'),
]

def analyze(text: str) -> dict:
    """Return scored patterns, evidence and guidance; no personal data is stored."""
    if not text or not text.strip():
        return {'score': 0, 'level': 'No text', 'findings': [], 'summary': 'Paste a conversation to begin.'}
    matches = []
    for rule in RULES:
        m = re.search(rule.pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            matches.append({
                'label': rule.label, 'category': rule.category, 'weight': rule.weight,
                'evidence': text[max(0, m.start()-35):min(len(text), m.end()+35)].strip(),
                'explanation': rule.explanation, 'next_step': rule.next_step,
            })
    # Severity indicator reflects matched heuristics, not likelihood/probability.
    score = min(100, sum(m['weight'] for m in matches))
    level = 'High concern' if score >= 55 else 'Review carefully' if score >= 25 else 'Low signals detected'
    summary = ('Multiple concerning patterns were detected.' if score >= 55 else
               'Some suspicious patterns were detected.' if score >= 25 else
               'Few of the configured warning signs were found. This does not prove the message is safe.')
    return {'score': score, 'level': level, 'findings': matches, 'summary': summary}
