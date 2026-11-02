"""Portable TF-IDF + logistic inference from numeric JSON.

Training uses scikit-learn. Serving reproduces its word/bigram TF-IDF and linear
model with the standard library; there is no pickle, external API, or runtime
scientific-library dependency. Tests check every held-out score for parity.
"""
from collections import Counter
import gzip
import json
import math
from pathlib import Path
import re
import unicodedata

MODEL_PATH = Path(__file__).parent / 'artifacts/model.json.gz'
TOKENS = re.compile(r'(?u)\b\w\w+\b')


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


class TextClassifier:
    def __init__(self, path: Path = MODEL_PATH):
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            bundle = json.load(f)
        if bundle.get('schema_version') != 1:
            raise ValueError('Unsupported model artifact schema')
        self.version = bundle['model_version']
        self.threshold = float(bundle['threshold'])
        self.features = bundle['features']
        self.vocabulary = {word:i for i,word in enumerate(self.features)}
        self.idf = [float(v) for v in bundle['idf']]
        self.coef = [float(v) for v in bundle['coefficients']]
        self.intercept = float(bundle['intercept'])
        if (not self.features or len(self.coef) != len(self.features) or len(self.idf) != len(self.features)
                or len(self.vocabulary) != len(self.features) or not 0 < self.threshold < 1
                or not all(math.isfinite(v) for v in self.coef + self.idf + [self.intercept])
                or not all(v > 0 for v in self.idf)):
            raise ValueError('Invalid numeric model artifact')

    def vectorize(self, text: str) -> list[tuple[int, float]]:
        """Equivalent to the fitted sklearn vectorizer's L2-normalised output."""
        normal = unicodedata.normalize('NFKD', text.lower())
        normal = ''.join(c for c in normal if not unicodedata.combining(c))
        words = TOKENS.findall(normal)
        terms = words + [' '.join(pair) for pair in zip(words, words[1:])]
        counts = Counter(self.vocabulary[t] for t in terms if t in self.vocabulary)
        weighted = [(i, (1.0 + math.log(count)) * self.idf[i]) for i,count in sorted(counts.items())]
        norm = math.sqrt(sum(value * value for _,value in weighted))
        return [(i, value / norm) for i,value in weighted] if norm else []

    def raw_score(self, text: str) -> float:
        """Unconditional numerical score for reproducibility, including the prior."""
        return sigmoid(sum(value * self.coef[i] for i,value in self.vectorize(text)) + self.intercept)

    def predict_many(self, texts: list[str]) -> list[dict]:
        results = []
        for text in texts:
            vector = self.vectorize(text)
            contributions = [(i, value * self.coef[i]) for i,value in vector]
            score = sigmoid(sum(value for _,value in contributions) + self.intercept)
            strongest = sorted(contributions, key=lambda p:abs(p[1]), reverse=True)[:8]
            terms = [{'term': self.features[i], 'contribution': value,
                      'direction': 'spam' if value > 0 else 'ham'}
                     for i,value in strongest if abs(value) > .015]
            available = bool(vector) and bool(text.strip())
            results.append({'score': score if available else None,
                            'flag': score >= self.threshold if available else None,
                            'label': ('Spam-like' if score >= self.threshold else 'Ham-like') if available else 'Insufficient vocabulary',
                            'threshold': self.threshold, 'terms': terms,
                            'known_features': len(vector), 'version': self.version})
        return results

    def predict(self, text: str) -> dict:
        return self.predict_many([text])[0]
