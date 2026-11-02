"""JSON-only TF-IDF + logistic model; no pickle, API, or network at inference."""
import gzip
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_PATH = Path(__file__).parent / "artifacts/model.json.gz"


class TextClassifier:
    def __init__(self, path: Path = MODEL_PATH):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            bundle = json.load(f)
        if bundle.get("schema_version") != 1:
            raise ValueError("Unsupported model artifact schema")
        self.version = bundle["model_version"]
        self.threshold = float(bundle["threshold"])
        self.features = np.array(bundle["features"])
        self.vectorizer = TfidfVectorizer(
            vocabulary={word: i for i, word in enumerate(bundle["features"])},
            ngram_range=(1, 2), lowercase=True, sublinear_tf=True,
            strip_accents="unicode", token_pattern=r"(?u)\b\w\w+\b")
        self.vectorizer.idf_ = np.asarray(bundle["idf"], dtype=float)
        self.coef = np.asarray(bundle["coefficients"], dtype=float)
        self.intercept = float(bundle["intercept"])
        if len(self.coef) != len(self.features) or not np.isfinite(self.coef).all():
            raise ValueError("Invalid model coefficients")

    def predict_many(self, texts: list[str]) -> list[dict]:
        if not texts:
            return []
        matrix = self.vectorizer.transform(texts)
        scores = expit(np.asarray(matrix @ self.coef).ravel() + self.intercept)
        results = []
        for i, score in enumerate(scores):
            row = matrix.getrow(i)
            contributions = row.data * self.coef[row.indices]
            order = np.argsort(np.abs(contributions))[::-1][:8]
            # Exact additive log-odds terms, not causal claims.
            terms = [{"term": str(self.features[row.indices[j]]),
                      "contribution": float(contributions[j]),
                      "direction": "spam" if contributions[j] > 0 else "ham"}
                     for j in order if abs(contributions[j]) > .015]
            available = bool(row.nnz) and bool(texts[i].strip())
            results.append({"score": float(score) if available else None,
                            "flag": bool(score >= self.threshold) if available else None,
                            "label": ("Spam-like" if score >= self.threshold else "Ham-like") if available else "Insufficient vocabulary",
                            "threshold": self.threshold, "terms": terms,
                            "known_features": int(row.nnz), "version": self.version})
        return results

    def predict(self, text: str) -> dict:
        return self.predict_many([text])[0]
