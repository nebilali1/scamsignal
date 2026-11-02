"""Authored, fictional demo fixtures. Never included in training/benchmarking."""
SCENARIOS = {
    'Fake job offer': {
        'kind': 'Scam scenario', 'channel': 'Recruiting · 6 messages',
        'note': 'A friendly opening turns into an equipment payment, deadline, and secrecy request. Watch where the first evidence appears.',
        'text': """Recruiter: Hi! We reviewed your profile for our remote assistant role. Are you available to chat?
You: Yes, could you tell me about the interview process?
Recruiter: You're already approved. Pay an equipment fee of $150 before you start.
You: Can I speak with someone from the company first?
Recruiter: Send the payment via Zelle within 30 minutes to secure your position.
Recruiter: Keep this between us while we finish the paperwork."""},
    'Account security phishing': {
        'kind': 'Scam scenario', 'channel': 'SMS · 4 messages',
        'note': 'Account threats escalate to a request for an authentication code. The link is fictional and is never opened.',
        'text': """Support: We noticed a login to your account from a new device.
You: I haven't logged in today. What should I do?
Support: URGENT: your account will be suspended. Click this link to verify your account: https://account-check.example/verify
Support: Reply with the one-time code we texted you so we can restore access."""},
    'Investment pitch': {
        'kind': 'Scam scenario', 'channel': 'Direct message · 4 messages',
        'note': 'Guarantees, payment, and isolation cues can accumulate even if the SMS model is unconvinced.',
        'text': """Contact: It was nice meeting you in the group yesterday.
Contact: Our private fund offers guaranteed returns with zero risk. You can double your money this month.
You: Where can I read about the fund?
Contact: Move our chat to Telegram. Send $500 in bitcoin and keep this between us."""},
    'Marketplace overpayment': {
        'kind': 'Scam scenario', 'channel': 'Marketplace · 4 messages',
        'note': 'A supposed overpayment turns into a demand for money back before settlement.',
        'text': """Buyer: Is your desk still available for $80?
Seller: Yes, you can collect it tomorrow.
Buyer: My assistant accidentally paid $800. Please send the difference to the courier.
Buyer: Send the refund via Cash App immediately. The driver is already on the way."""},
    'Tech support impersonation': {
        'kind': 'Scam scenario', 'channel': 'Support chat · 3 messages',
        'note': 'The rules catch device-access requests that older SMS spam training data may not represent.',
        'text': """Agent: This is the support team. We've detected a problem with your laptop.
You: I didn't open a support ticket.
Agent: Install AnyDesk and give us remote access right now so we can fix it."""},
    'Ordinary conversation': {
        'kind': 'Benign scenario', 'channel': 'Class project · 4 messages',
        'note': 'An ordinary collaboration with no configured rule triggers. A quiet result still is not proof of safety.',
        'text': """Alex: Hi, thanks for meeting today. I added our notes to the project folder.
You: Great. I'll work on the introduction tonight.
Alex: Can we review the slides after class tomorrow?
You: Sure, see you at the library at three."""},
    'Legitimate security advice': {
        'kind': 'Benign scenario', 'channel': 'Security notice · 3 messages',
        'note': 'Mentioning a password is different from requesting it. Local negation suppresses the explicit safety advice.',
        'text': """IT team: A reminder to keep your account secure.
IT team: Never share your password or verification code with anyone.
IT team: If you need assistance, open the campus support portal from your bookmarks."""},
    'Friends splitting dinner': {
        'kind': 'Ambiguous / false-positive check', 'channel': 'Friends · 3 messages',
        'note': 'A normal payment request can match a rule. The system cannot know whether this sender is really your friend.',
        'text': """Sam: Thanks for dinner! Your share was $18.
You: Can I send you the money tomorrow?
Sam: Sure, send it via Venmo when you get a chance. No rush."""},
    'Urgent but legitimate': {
        'kind': 'Ambiguous / false-positive check', 'channel': 'Class reminder · 2 messages',
        'note': 'A legitimate deadline can trigger the urgency rule. This example deliberately exposes a false-positive risk.',
        'text': """Classmate: The project submission closes before midnight. Please upload your section.
You: Thanks for the reminder. I'll submit it through the course portal."""},
    'Safety advice followed by a scam': {
        'kind': 'Challenging scam scenario', 'channel': 'Direct message · 3 messages',
        'note': 'A safety-sounding opening must not suppress a later request to reveal a code.',
        'text': """Contact: Never share your password with strangers.
Contact: I'm on the account recovery team, so this is different.
Contact: Please send me your verification code right now to complete the check."""},
    'Subtle impersonation': {
        'kind': 'Challenging / possible miss', 'channel': 'Direct message · 3 messages',
        'note': 'An intentionally subtle scenario may escape both engines. Text alone cannot authenticate a sender; this is a known coverage limit.',
        'text': """Unknown: Hey, it's me. I had to change my number.
You: Who is this?
Unknown: Your cousin. I'm at the shop and my card isn't working. Could you cover it for me? I'll pay you back tomorrow."""},
}
EXAMPLES = {name: scenario['text'] for name, scenario in SCENARIOS.items()}
