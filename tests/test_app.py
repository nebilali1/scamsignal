from streamlit.testing.v1 import AppTest
from examples import EXAMPLES
from pathlib import Path


def app():
    at = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py', default_timeout=30).run()
    assert not at.exception
    return at


def button(at,label):
    return next(b for b in at.button if b.label == label)


def test_default_and_replay():
    at=app()
    assert at.session_state.result['score'] == 83
    button(at,'↤ Start').click().run()
    assert not at.exception and at.slider(key='step').value == 1
    button(at,'First signal').click().run()
    assert at.slider(key='step').value == 3
    button(at,'Next message →').click().run()
    assert not at.exception and at.slider(key='step').value == 4


def test_all_demo_scenarios_and_navigation():
    at=app()
    for name in EXAMPLES:
        at.selectbox(key='scenario').select(name).run()
        assert not at.exception, name
        assert at.session_state.submitted == EXAMPLES[name]
    for name in ['Model lab','How it works','Investigate']:
        at.radio(key='page').set_value(name).run()
        assert not at.exception, name


def test_custom_input_persists_and_clear_removes_it():
    at=app()
    at.text_area(key='editor').set_value('PRIVATE: Send me your password immediately').run()
    assert at.session_state.submitted == EXAMPLES['Fake job offer']
    button(at,'Analyze conversation').click().run()
    assert not at.exception
    assert at.session_state.result['events'][0]['message'] == 'Send me your password immediately'
    at.radio(key='page').set_value('Model lab').run()
    at.radio(key='page').set_value('Investigate').run()
    assert at.session_state.submitted.startswith('PRIVATE:')
    button(at,'Clear conversation').click().run()
    assert not at.exception
    assert at.session_state.editor == ''
    assert at.session_state.submitted == ''
    assert at.session_state.result is None


def test_empty_input_does_not_crash():
    at=app()
    button(at,'Clear conversation').click().run()
    button(at,'Analyze conversation').click().run()
    assert not at.exception
    assert any('Add a message' in w.value for w in at.warning)


def test_validation_explorer_does_not_change_classifier():
    at=app()
    at.radio(key='page').set_value('Model lab').run()
    at.slider(key='explore_threshold').set_value(.8).run()
    assert not at.exception
    at.radio(key='page').set_value('Investigate').run()
    assert at.session_state.result['events'][0]['model']['threshold'] == .49


def test_missing_model_still_renders_rules(monkeypatch):
    import ml
    import streamlit as st
    st.cache_resource.clear()
    def unavailable():
        raise OSError('Test model unavailable')
    monkeypatch.setattr(ml,'TextClassifier',unavailable)
    try:
        at=app()
        assert any('artifact is unavailable' in w.value for w in at.warning)
        assert at.session_state.result['score'] == 83
        assert at.session_state.result['peak_model_score'] is None
        assert at.session_state.engine_signature == 'rules-only'
        at.radio(key='page').set_value('Model lab').run()
        assert not at.exception
    finally:
        st.cache_resource.clear()
