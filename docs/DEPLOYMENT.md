# Deployment and smoke checks

Existing deployment: https://scamsignal-cudqj7eqefjdkp8j2hvkyn.streamlit.app/

The existing repository, `main` branch, and `app.py` entrypoint are retained. Runtime dependencies are pinned in `requirements.txt`; tests and lint tools are in `requirements-dev.txt`. Model serving uses only the Python standard library; scikit-learn and SciPy are training/test dependencies. The model artifact and evaluation are checked in, so launch requires no training or secrets.

## Streamlit Community Cloud

1. Push the tested commit to `main`; Cloud normally notices and installs changed dependencies.
2. Wait for the app to rebuild, then refresh. The title should read **ScamSignal AI · Conversation intelligence** and the sidebar should include **Model lab**.
3. If the old build remains, use the app management menu to reboot. Inspect build logs for dependency errors.
4. Use Python 3.11 or 3.12. If the deployment uses an older interpreter and Cloud requires recreating the deployment to change it, keep the repository, branch, and entrypoint and select Python 3.12 in advanced settings.

## Smoke checklist

- App opens without an error panel; model status is ready.
- Fake job offer shows rule severity 83, first signal at message 3, and four rule patterns.
- Start and First signal reveal the correct prefix; Next message works without blanking the page.
- Ordinary conversation and Legitimate security advice show no rule signals.
- Custom edits are not silently treated as analysed. Analyse, navigate to Model lab, then return: submitted input persists.
- Model Lab shows 1,032 test records and matrix `[[897,7],[7,121]]`.
- Moving the validation threshold does not change the deployed threshold of 0.49.
- Default report excludes source text; Clear conversation removes the active content.

## Local fallback

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the localhost URL Streamlit prints. This is useful if conference Wi-Fi is unreliable. Community Cloud may sleep after inactivity; open and check it before demonstrating. No claim of guaranteed uptime is made.

## Rollback

Use GitHub's revert workflow to revert the upgrade commit(s), or `git revert <commit>` followed by a normal push. Do not reset/force-push the shared branch. The original implementation is preserved in repository history.
