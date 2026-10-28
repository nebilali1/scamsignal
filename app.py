import streamlit as st
from detector import analyze
from examples import EXAMPLES
from timeline import analyze_timeline

st.set_page_config(page_title='ScamSignal | Conversation Risk Review', page_icon='🛡️', layout='wide')
st.markdown('''<style>
.stApp {background: #0b1220; color: #e5eef9;}
.block-container {max-width: 1130px; padding-top: 2rem;}
h1,h2,h3 {color: #f5f8ff !important;}
[data-testid="stMetricValue"] {color: #6ee7b7;}
div[data-testid="stAlert"] {border-radius: 12px;}
</style>''', unsafe_allow_html=True)

st.caption('SCAMSIGNAL / CONVERSATION SAFETY')
st.title('Catch the warning signs before you respond.')
st.write('Review suspicious conversations with transparent, explainable screening rules. No account or API key required.')
st.info('Prototype only: these are heuristic warning signals, **not an AI prediction or proof of fraud**. A low score does not mean a conversation is safe.')

left, right = st.columns([1.15, 0.85], gap='large')
with left:
    selected = st.selectbox('Try a sample', ['Write or paste your own'] + list(EXAMPLES))
    initial = EXAMPLES.get(selected, '')
    message = st.text_area('Conversation or message', value=initial, height=255, placeholder='Paste a suspicious message here…', key=f'message_{selected}')
    st.caption('For privacy, remove names, phone numbers, passwords, and other sensitive details before pasting.')
    run = st.button('Analyze conversation', type='primary', use_container_width=True)

with right:
    st.subheader('How the review works')
    st.markdown('**1.** Look for payment, pressure, account, and identity-related patterns.\n\n**2.** Show the exact language that triggered each finding.\n\n**3.** Suggest practical independent verification steps.')
    st.divider()
    st.markdown('**Important design choice**')
    st.write('Scores are a severity index based on matched rules—not a calibrated probability that someone is a scammer.')

if run:
    if not message.strip():
        st.warning('Add a message to analyze.')
    elif len(message) > 30000:
        st.warning('Please enter 30,000 characters or fewer.')
    else:
        result = analyze(message)
        st.divider()
        st.subheader('Analysis results')
        a,b,c = st.columns(3)
        a.metric('Signal severity', f"{result['score']} / 100")
        b.metric('Assessment', result['level'])
        c.metric('Warning signs', len(result['findings']))
        st.write(result['summary'])
        if result['findings']:
            for f in result['findings']:
                with st.expander(f"{f['label']} · {f['category']}", expanded=True):
                    st.write('**Matched excerpt:**', f['evidence'])
                    st.write('**Why it matters:**', f['explanation'])
                    st.write('**What to do:**', f['next_step'])
        else:
            st.info('No configured patterns matched. Scams can still evade these checks. Independently verify unusual requests.')
        st.divider()
        st.subheader('Conversation timeline')
        st.caption('For multiple messages, put each message on a separate line. Each line is screened independently.')
        timeline = analyze_timeline(message)
        if len(timeline['events']) > 1:
            if timeline['first_warning'] is not None:
                st.warning(f"First detected warning: message {timeline['first_warning']}")
            else:
                st.info('No configured warning patterns found in individual messages.')
            for event in timeline['events']:
                status = ', '.join(finding['label'] for finding in event['findings']) or 'No rule matched'
                with st.expander(f"Message {event['number']} · {status}"):
                    st.write(event['message'])
                    if event['findings']:
                        st.write('Matched warning signs:', status)
        else:
            st.caption('Tip: paste multiple messages on separate lines to see the timeline.')
        st.caption('Note: suspicious patterns may depend on context across different messages.')
        st.caption('No conversations are written to a database by this app. Hosting providers may still process application traffic.')

st.divider()
st.caption('Built as an explainable scam-screening prototype • GitHub / portfolio demonstration')
