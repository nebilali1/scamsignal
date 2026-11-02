"""Build a self-contained browser demo from the same trained artifacts/rules."""
from dataclasses import asdict
import gzip
import json
from pathlib import Path
from detector import RULES
from examples import SCENARIOS

ROOT=Path(__file__).resolve().parents[1]


def build():
    with gzip.open(ROOT/'artifacts/model.json.gz','rt') as f:
        model=json.load(f)
    payload={'model':model,'rules':[asdict(r) for r in RULES],'scenarios':SCENARIOS,
             'evaluation':json.loads((ROOT/'artifacts/evaluation.json').read_text())}
    template=(ROOT/'web/template.html').read_text()
    content=template.replace('/*STYLE*/',(ROOT/'web/style.css').read_text()).replace('/*SHIELD*/',(ROOT/'assets/shield.svg').read_text())
    content=content.replace('/*DATA*/',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
    content=content.replace('/*ENGINE*/',(ROOT/'web/engine.mjs').read_text().replace('export ',''))
    content=content.replace('/*APP*/',(ROOT/'web/app.js').read_text())
    (ROOT/'web/dist').mkdir(exist_ok=True)
    (ROOT/'web/dist/index.html').write_text(content)
    print(f'Built browser demo: {len(content.encode()):,} bytes; no external runtime assets.')

if __name__=='__main__':
    build()
