"""ScamSignal AI: a session-scoped, explainable investigation workspace."""
from html import escape
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from detector import RULES
from examples import SCENARIOS, EXAMPLES
from ml import TextClassifier
from presentation import build_report, highlight
from settings import MAX_CHARACTERS
from timeline import analyze_timeline, split_messages, validate_input

ROOT = Path(__file__).parent
CUSTOM = 'Paste your own conversation'
DEFAULT = 'Fake job offer'
LIVE_URL = 'https://scamsignal-cudqj7eqefjdkp8j2hvkyn.streamlit.app/'
REPO_URL = 'https://github.com/nebilali1/scamsignal'

st.set_page_config(page_title='ScamSignal AI · Conversation intelligence', page_icon='assets/shield.svg', layout='wide', initial_sidebar_state='expanded')
st.markdown('<style>' + (ROOT / 'assets/style.css').read_text() + '</style>', unsafe_allow_html=True)

# Detach these widget values from Streamlit's cleanup when another workspace
# does not render them. Drafts and submitted results must survive navigation.
for state_key in ('scenario', 'editor', 'step'):
    if state_key in st.session_state:
        st.session_state[state_key] = st.session_state[state_key]


@st.cache_resource(show_spinner=False)
def load_model():
    return TextClassifier()


@st.cache_data(show_spinner=False)
def load_evaluation():
    return json.loads((ROOT / 'artifacts/evaluation.json').read_text())


try:
    classifier = load_model()
    model_error = None
except (OSError, ValueError, KeyError, TypeError):
    classifier = None
    model_error = 'The model artifact is unavailable. Rule screening still works; no ML prediction is being shown.'
try:
    evaluation = load_evaluation()
except (OSError, ValueError):
    evaluation = None


def html(value):
    st.markdown(value, unsafe_allow_html=True)


def hero(eyebrow, title, subtitle):
    status = 'Model ready · offline inference' if classifier else 'Rules-only mode'
    html(f'<div class="hero"><div><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div><div class="status"><span class="dot"></span>{status}</div></div>')


def reset_demo():
    name = st.session_state.scenario
    text = EXAMPLES.get(name, '')
    st.session_state.editor = text
    st.session_state.submitted = text
    st.session_state.result = analyze_timeline(text, classifier) if text else None
    st.session_state.step = max(1, len(split_messages(text)))


def clear_session():
    st.session_state.scenario = CUSTOM
    reset_demo()


def set_step(value):
    st.session_state.step = value


def stats(cards):
    html('<div class="stat-grid">' + ''.join(
        f'<div class="stat"><div class="stat-label">{label}</div><div class="stat-value {tone}">{value}</div><div class="stat-foot">{foot}</div></div>'
        for label, value, foot, tone in cards) + '</div>')


def chart_style(chart):
    return chart.configure_view(stroke=None).configure_axis(gridColor='#233140', domain=False, labelColor='#96a8ba', titleColor='#aab8c6', labelFontSize=11).configure_legend(labelColor='#b7c6d7', title=None)


with st.sidebar:
    shield = (ROOT / 'assets/shield.svg').read_text()
    html(f'<div class="brand">{shield}<span>ScamSignal<sup>AI</sup></span></div><div class="eyebrow">Investigation workspace</div>')
    page = st.radio('Navigation', ['Investigate', 'Model lab', 'How it works'], label_visibility='collapsed', key='page')
    html('<div class="side-caption">A closer look at the language<br>behind suspicious conversations.</div>')
    if evaluation:
        f1 = evaluation['systems']['Machine learning']['f1']
        html(f'<div class="side-box"><div class="side-label">Held-out SMS benchmark</div><div class="value">{f1:.1%} F1</div><div class="side-caption">{evaluation["splits"]["test"]["total"]:,} messages · spam vs. ham<br>Not a real-world fraud accuracy claim.</div></div>')
    st.link_button('View source on GitHub ↗', REPO_URL, width='stretch')
    st.divider()
    html('<div class="side-label">Privacy by design</div><div class="side-caption">No external AI API.<br>No message database.<br>Clear your session when finished.</div>')
    st.caption('Hosted inference runs on the app server. Remove sensitive details before pasting.')
    st.button('Clear conversation', on_click=clear_session, width='stretch')
    html('<div class="side-caption" style="margin-top:25px">Built by Nebil Ali<br>Computer Science · Connecticut College</div>')


if 'scenario' not in st.session_state:
    st.session_state.scenario = DEFAULT
    reset_demo()
if model_error:
    st.warning(model_error)


def investigation():
    hero('01 / Conversation intelligence', 'See where the conversation turns.', 'Inspect the warning signs, follow the evidence, and compare a trained model with transparent rules.')
    controls, run_col = st.columns([3.4, 1], vertical_alignment='bottom')
    with controls:
        st.selectbox('Conversation', list(EXAMPLES) + [CUSTOM], key='scenario', on_change=reset_demo)
    with run_col:
        run = st.button('Analyze conversation', type='primary', width='stretch')
    scenario = SCENARIOS.get(st.session_state.scenario)
    if scenario:
        st.caption(f'{scenario["kind"]}  /  {scenario["channel"]}  /  Fictional demo')
    with st.expander('Edit conversation / paste your own', expanded=st.session_state.scenario == CUSTOM):
        st.text_area('One message per line; optional Sender: prefix', key='editor', height=190, max_chars=MAX_CHARACTERS,
                     placeholder='Sender: Paste a message here…\nYou: Add the next reply…')
        st.caption('Remove names, account numbers, and secrets. Up to 80 messages / 12,000 characters. Links are never opened.')
    if run:
        try:
            validate_input(st.session_state.editor)
        except ValueError as exc:
            st.warning(str(exc))
        else:
            st.session_state.submitted = st.session_state.editor
            st.session_state.result = analyze_timeline(st.session_state.submitted, classifier)
            st.session_state.step = len(st.session_state.result['events'])
    if st.session_state.editor != st.session_state.submitted:
        st.info('You have unanalysed edits. Results below still show the last analysed conversation. Click Analyze conversation to update.')
    result = st.session_state.result
    if not result or not result['events']:
        st.info('Paste a conversation, then click Analyze conversation. Or select a fictional demo above.')
        return
    step = min(st.session_state.get('step', len(result['events'])), len(result['events']))
    current = result['events'][step - 1]
    first = result['first_signal']
    active_first = first if first is not None and first <= step else None
    model_score = current['peak_model_score']
    rules_seen = {}
    for event in result['events'][:step]:
        for finding in event['findings']:
            rules_seen.setdefault(finding['id'], finding)
    stats([
        ('Rule severity', f'{current["cumulative_score"]}<small> / 100</small>', 'Weighted signals · not a probability', 'amber' if current['cumulative_score'] else 'mint'),
        ('ML spam score', f'{model_score:.1%}' if model_score is not None else 'Unavailable', f'Peak message · alert at {classifier.threshold:.0%}' if classifier else 'Model unavailable', 'mint'),
        ('First signal', f'Message {active_first:02}' if active_first else 'None yet', 'Earliest rule match or model flag', ''),
        ('Evidence found', f'{len(rules_seen):02}<small> patterns</small>', f'Viewing {step} of {len(result["events"])} messages', ''),
    ])
    left, right = st.columns([1.4, 1], gap='large')
    with left:
        html('<div class="section-title">Conversation timeline</div><div class="section-sub">Reveal the conversation in order. Amber highlights are exact rule matches.</div>')
        if len(result['events']) > 1:
            a, b, c = st.columns(3)
            a.button('↤ Start', on_click=set_step, args=(1,), width='stretch')
            b.button('First signal', on_click=set_step, args=(first or 1,), disabled=first is None, width='stretch')
            c.button('Next message →', on_click=set_step, args=(min(step + 1, len(result['events'])),), disabled=step == len(result['events']), width='stretch')
            st.slider('Reveal through message', min_value=1, max_value=len(result['events']), key='step')
        for event in result['events'][:step]:
            number = event['number']
            badges = ''
            if number == result['first_warning']:
                badges += '<span class="badge warn">FIRST RULE SIGNAL</span>'
            if event['model'] and event['model']['flag']:
                badges += '<span class="badge ml">ML SPAM FLAG</span>'
            rule_badges = ''.join(f'<span class="badge warn">{escape(f["label"])}</span>' for f in event['findings'])
            css_class = 'warning' if event['findings'] else 'you' if event['sender'].casefold() in ('you','seller') else ''
            html(f'<div class="chat-row"><div class="chat-num">{number:02}</div><div class="bubble {css_class}"><div class="chat-meta"><strong>{escape(event["sender"])}</strong><span>MESSAGE {number:02}</span></div><div class="chat-body">{highlight(event["message"], event["findings"])}</div>{("<div style=\"margin-top:9px\">" + badges + rule_badges + "</div>") if badges or rule_badges else ""}</div></div>')
        if step < len(result['events']):
            st.caption(f'{len(result["events"]) - step} messages hidden. Move the slider or select Next message to reveal more.')
        if scenario and st.session_state.submitted == scenario['text']:
            html(f'<div class="notice"><b>Demo insight</b><br>{escape(scenario["note"])}</div>')
        st.subheader('Signal progression')
        rows = []
        for event in result['events'][:step]:
            rows.append({'Message': event['number'], 'Value': event['cumulative_score'], 'Signal': 'Cumulative rule severity'})
            if event['model'] and event['model']['score'] is not None:
                rows.append({'Message': event['number'], 'Value': event['model']['score'] * 100, 'Signal': 'Per-message ML spam score'})
        chart = alt.Chart(pd.DataFrame(rows)).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X('Message:Q', axis=alt.Axis(tickMinStep=1), scale=alt.Scale(domain=[1, max(2, len(result['events']))])),
            y=alt.Y('Value:Q', scale=alt.Scale(domain=[0,100]), title='Score (different meanings)'),
            color=alt.Color('Signal:N', scale=alt.Scale(domain=['Cumulative rule severity','Per-message ML spam score'], range=['#ffbe76','#67e8be']), legend=alt.Legend(orient='bottom')),
            tooltip=['Message:Q','Signal:N',alt.Tooltip('Value:Q',format='.1f')]).properties(height=190)
        st.altair_chart(chart_style(chart), width='stretch')
        st.caption('Rule severity and ML spam score use different scales of meaning. Neither is a probability that this conversation is fraudulent.')
    with right:
        verdict = current['triage']
        html(f'<div class="section-title">Evidence & assessment</div><div class="section-sub">Assessment through message {step:02}</div><div class="verdict {verdict["tone"]}"><div class="eyebrow">Hybrid triage · decision policy</div><div class="verdict-title">{verdict["label"]}</div><p>{verdict["reason"]}</p></div>')
        if model_score is not None:
            ml_flag = model_score >= classifier.threshold
            rule_flag = current['cumulative_score'] >= 55
            explanation = ('Both engines raise concern.' if ml_flag and rule_flag else
                           'The rules raise concern; the SMS model does not flag this conversation.' if rule_flag else
                           'The model flags spam-like language without a high rule-severity score.' if ml_flag else
                           'Neither engine reaches its high-concern threshold. Review any individual warnings below.')
            st.caption(explanation)
        rules_tab, model_tab = st.tabs(['Rule evidence', 'Model evidence'])
        with rules_tab:
            if not rules_seen:
                st.info('No configured rule has matched the revealed messages. Subtle impersonation can still evade these checks.')
            for finding in rules_seen.values():
                evidence_number = next(e['number'] for e in result['events'][:step] if finding['id'] in [f['id'] for f in e['findings']])
                html(f'<div class="finding"><div class="finding-top"><span>{escape(finding["label"])}</span><span class="amber">+{finding["weight"]}</span></div><div class="stat-foot">{escape(finding["category"])} · first seen in message {evidence_number:02}</div><div class="evidence">{escape(finding["evidence"])}</div><p>{escape(finding["explanation"])}</p><p class="action">{escape(finding["next_step"])}</p></div>')
            st.caption('Each rule contributes once per conversation; repeated matches do not inflate severity. Scores are capped at 100.')
        with model_tab:
            available = [e for e in result['events'][:step] if e['model'] and e['model']['score'] is not None]
            if not available:
                st.info('No model score is available for the revealed messages.')
            else:
                selected = st.selectbox('Inspect model evidence for', [e['number'] for e in available], format_func=lambda n:f'Message {n:02}', key=f'model_message_{step}')
                prediction = result['events'][selected - 1]['model']
                st.metric('Message spam score', f'{prediction["score"]:.1%}')
                st.caption(f'{prediction["label"]} at the fixed {prediction["threshold"]:.0%} threshold. Model: TF-IDF + logistic regression.')
                terms = prediction['terms']
                if terms:
                    df = pd.DataFrame(terms)
                    term_chart = alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
                        x=alt.X('contribution:Q', title='Contribution to spam log-odds'),
                        y=alt.Y('term:N', sort='-x', title=None),
                        color=alt.Color('direction:N', scale=alt.Scale(domain=['spam','ham'], range=['#ffbe76','#67e8be']), legend=None),
                        tooltip=['term:N',alt.Tooltip('contribution:Q',format='.3f'),'direction:N']).properties(height=220)
                    st.altair_chart(chart_style(term_chart), width='stretch')
                st.caption('Amber terms push toward spam; mint terms push toward ham. These are learned weighted associations, not proof or causal explanations. Other terms and the intercept also contribute.')
                st.info('Trained on older English SMS spam/ham labels. Modern scams, unusual phrasing, long messages, and other languages can be missed.')
        with st.expander('Export analysis'):
            st.caption('Default export contains scores and rule categories, without conversation text or matched phrases.')
            include_text = st.checkbox('Include original conversation text', value=False)
            st.download_button('Download JSON report', build_report(result, include_text), file_name='scamsignal-analysis.json', mime='application/json', width='stretch')
            st.caption('The export covers the full analysed conversation, including any messages hidden by the replay slider.')


def model_lab():
    hero('02 / Measurement & transparency', 'Evidence behind the engine.', 'A reproducible benchmark, a fixed test set, and an honest view of what the model can—and cannot—detect.')
    if not evaluation:
        st.warning('Evaluation artifact unavailable. No performance numbers are shown.')
        return
    report = evaluation
    ml = report['systems']['Machine learning']
    stats([('Precision', f'{ml["precision"]:.1%}', 'Of spam flags, how many were correct?', 'mint'),
           ('Recall', f'{ml["recall"]:.1%}', 'Of labelled spam, how much was caught?', 'mint'),
           ('F1 score', f'{ml["f1"]:.1%}', 'Harmonic mean of precision and recall', 'mint'),
           ('Test messages', f'{ml["support"]:,}', f'{ml["positive_count"]} spam · {ml["support"]-ml["positive_count"]} ham', '')])
    st.info('These metrics measure spam vs. ham on the UCI SMS Spam Collection. They do not measure real-world fraud accuracy or multi-message conversation detection.')
    left, right = st.columns([1,1.1], gap='large')
    with left:
        st.subheader('Held-out confusion matrix')
        st.caption('Rows: actual label · Columns: predicted label. Positive class = spam.')
        tn, fp = ml['confusion_matrix'][0]
        fn, tp = ml['confusion_matrix'][1]
        html(f'<div class="matrix"><div class="matrix-cell"><span>HAM → HAM · TRUE NEGATIVE</span><strong>{tn}</strong><span>Ordinary messages left unflagged</span></div><div class="matrix-cell error"><span>HAM → SPAM · FALSE POSITIVE</span><strong>{fp}</strong><span>False alarms</span></div><div class="matrix-cell error"><span>SPAM → HAM · FALSE NEGATIVE</span><strong>{fn}</strong><span>Missed spam</span></div><div class="matrix-cell"><span>SPAM → SPAM · TRUE POSITIVE</span><strong>{tp}</strong><span>Spam correctly flagged</span></div></div>')
        interval = report['f1_group_bootstrap_95']
        st.caption(f'F1 95% group-bootstrap interval: {interval[0]:.1%}–{interval[1]:.1%} (500 resamples of test template groups). This measures sampling uncertainty, not deployment generalisation.')
    with right:
        st.subheader('The data boundary')
        for label, value in [('Dataset', 'UCI SMS Spam Collection'), ('License', 'CC BY 4.0 · Almeida & Hidalgo'),
                             ('Raw → deduplicated', f'{report["dataset"]["raw_rows"]:,} → {report["dataset"]["unique_rows"]:,} messages'),
                             ('Training / validation / test', ' / '.join(f'{report["splits"][k]["total"]:,}' for k in ('train','validation','test'))),
                             ('Learned vocabulary', f'{report["features"]:,} word & bigram features'),
                             ('Fixed alert threshold', f'{report["threshold"]:.0%} · selected on validation only'),
                             ('Zero-vocabulary test inputs', str(report['zero_vocabulary_test_inputs']))]:
            html(f'<div class="mini-row"><span>{label}</span><b>{value}</b></div>')
        st.caption('Exact duplicates are removed before splitting. Normalised templates stay within one split. Vocabulary and IDF weights are fitted only on training data. Zero-vocabulary inputs produce no model alert and are labelled unavailable in the app.')
        st.link_button('View dataset & license ↗', report['dataset']['url'])
    st.divider()
    st.subheader('Compare the systems')
    frame = pd.DataFrame([{'System': name, 'Precision': m['precision'], 'Recall': m['recall'], 'F1': m['f1'], 'Accuracy': m['accuracy']} for name,m in report['systems'].items()])
    st.dataframe(frame, hide_index=True, width='stretch', column_config={c:st.column_config.NumberColumn(format='percent') for c in ['Precision','Recall','F1','Accuracy']})
    st.caption('Rules-only alert: severity ≥55. Hybrid alert: ML flag OR severity ≥55. Zero precision here means no positive predictions (defined as 0), not a measured ability to reject scams.')
    st.warning('None of these held-out SMS messages reaches the high rule threshold. The rules add coverage in authored modern-scam scenarios, but this benchmark does not demonstrate a hybrid improvement. The always-ham baseline also shows why accuracy alone is misleading.')
    st.subheader('Explore the precision–recall tradeoff')
    st.caption('Validation data only. This explorer does not change the deployed threshold or the held-out test metrics.')
    threshold = st.slider('Exploratory validation threshold', min_value=.20, max_value=.85, value=float(report['threshold']), step=.01, format='%.2f', key='explore_threshold')
    point = min(report['validation_thresholds'], key=lambda x:abs(x['threshold']-threshold))
    a,b,c = st.columns(3)
    a.metric('Validation precision', f'{point["precision"]:.1%}')
    b.metric('Validation recall', f'{point["recall"]:.1%}')
    c.metric('Validation F1', f'{point["f1"]:.1%}')
    frame = pd.DataFrame(report['validation_thresholds']).melt(id_vars='threshold', var_name='Metric', value_name='Score')
    chart = alt.Chart(frame).mark_line(strokeWidth=2.5).encode(
        x=alt.X('threshold:Q', title='Model score threshold'), y=alt.Y('Score:Q', scale=alt.Scale(domain=[0,1]), axis=alt.Axis(format='%')),
        color=alt.Color('Metric:N', scale=alt.Scale(range=['#67e8be','#88b5ef','#ffbe76']), legend=alt.Legend(orient='bottom')),
        tooltip=[alt.Tooltip('threshold:Q',format='.2f'),'Metric:N',alt.Tooltip('Score:Q',format='.1%')]).properties(height=230)
    marker = alt.Chart(pd.DataFrame({'threshold':[threshold]})).mark_rule(color='#b8c8d7',strokeDash=[4,4]).encode(x='threshold:Q')
    st.altair_chart(chart_style(chart + marker), width='stretch')
    with st.expander('Methodology & limitations', expanded=True):
        st.write('A TF-IDF vectorizer turns words and two-word phrases into weighted features. Logistic regression learns which features separate the labelled classes. The threshold maximises validation F1 among candidates with at least 95% validation precision; test precision can be lower.')
        for limitation in report['limitations']:
            st.markdown(f'- {limitation}')
        st.write('The rules have limited context and negation handling. Quotes, sarcasm, indirect requests, obfuscation, and identity impersonation remain difficult. URLs are displayed as text and are never resolved or scanned.')
        st.code('python -m scripts.train_model\npython -m pytest -q', language='bash')
    st.download_button('Download full evaluation JSON', json.dumps(report,indent=2), file_name='scamsignal-evaluation.json', mime='application/json')


def how_it_works():
    hero('03 / System design', 'Two engines. Every signal explained.', 'A small, inspectable system built to make uncertainty visible—not hide it behind an AI label.')
    cols = st.columns(3)
    for col,number,title,body in zip(cols,['01','02','03'],['Inspect each message','Run independent checks','Review the evidence'],[
        'Each nonempty line is a message. Sender labels are separated from content. Input size is bounded; links are never opened.',
        'A trained TF-IDF + logistic model scores SMS-like language. Eleven explicit rules look for payment, pressure, credential, and access requests.',
        'An explicit OR policy raises concern if the model flags spam or cumulative rule severity reaches 55. Exact spans and learned term weights stay separate.']):
        with col:
            html(f'<div class="method-card"><div class="eyebrow">{number}</div><h3>{title}</h3><p>{body}</p></div>')
    st.subheader('The 30-second story')
    st.write('“ScamSignal helps people spot where a conversation becomes suspicious. I combined a trained text classifier with an explainable rule engine, then built a timeline that shows the exact message and phrase behind each warning. The model achieved 94.5% F1 on a held-out SMS spam benchmark. I also show false positives, missed cases, and where rules and machine learning disagree—because a useful security tool needs to explain its limits.”')
    st.subheader('Try a one-minute walkthrough')
    st.markdown('1. Open **Investigate → Fake job offer** and click **Start**.\n2. Click **First signal** to reveal the equipment-fee request.\n3. Click **Next message** to watch the evidence accumulate.\n4. Compare **Rule evidence** with **Model evidence**.\n5. Try **Legitimate security advice** and **Subtle impersonation**.\n6. Open **Model lab** to inspect the actual test errors and methodology.')
    st.subheader('What is—and is not—stored')
    st.write('The app keeps your current input and analysis in your Streamlit session. It does not write conversations to a database, analytics service, log file, or external model API. Model and evaluation artifacts are shared read-only caches; submitted text is not cached across users. Clear conversation removes the current app session content. The hosting provider still processes traffic; this is not end-to-end encryption or browser-only inference.')
    with st.expander('Inspect all screening rules'):
        for rule in RULES:
            st.markdown(f'**{rule.label} · +{rule.weight}** — {rule.explanation}')
    st.subheader('Built for an honest demonstration')
    st.write('ScamSignal is a portfolio screening tool, not a fraud adjudication service. It does not authenticate senders, inspect attachments, verify domains, support images, or use a large language model. It must not be the sole basis for blocking, accusing, or reporting someone. The current model needs broader, contemporary, labelled fraud data before any production detection claim.')
    st.link_button('Architecture, model card & reproducible results ↗', REPO_URL)


if page == 'Investigate':
    investigation()
elif page == 'Model lab':
    model_lab()
else:
    how_it_works()
html('<div class="footer"><span>ScamSignal AI · Explainable conversation screening</span><span>Evidence, not a verdict. Verify unusual requests independently.</span></div>')
