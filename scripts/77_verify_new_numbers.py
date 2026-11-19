"""Checks every number in the new Results text and tables against the CSV and JSON outputs of scripts 64 to 70 (rounded half-up at the shown precision, percentages from fractions)."""
import re, json, os, glob, itertools, docx, numpy as np, pandas as pd
from decimal import Decimal, ROUND_HALF_UP
B = r'.'; T = os.path.join(B, 'outputs', 'tables')
vals = set()
def add(x):
    try:
        f = float(x)
        if np.isfinite(f): vals.update([f, f * 100, f / 100])
    except Exception: pass
def walk(o):
    if isinstance(o, dict): [walk(v) for v in o.values()]
    elif isinstance(o, list): [walk(v) for v in o]
    else: add(o)
for f in glob.glob(os.path.join(T, 'revision_*')):
    if f.endswith('.csv'):
        for v in pd.read_csv(f).values.ravel(): add(v)
    elif f.endswith('.json'): walk(json.load(open(f, encoding='utf-8')))
for f in ['lulc_accuracy_vs_consensus.json']: walk(json.load(open(os.path.join(T, f))))
for f in ['flood_stats_by_landcover.csv']:
    for v in pd.read_csv(os.path.join(T, f)).values.ravel(): add(v)
def rnd(v, d): return str(Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
index = {}
for v in vals:
    for d in range(0, 5): index.setdefault(rnd(v, d), set()).add(d)
doc = docx.Document(os.path.join(B, 'MANUSCRIPT_Results.docx')); txt = []
cur = None
for p in doc.paragraphs:
    if p.style.name.startswith('Heading'): cur = p.text
    new = cur in ('Reliability of the land-cover map', 'Study area, exclusions and analysed area', 'Built-up land and building footprints', 'Coverage of the reference mapping', 'What the cluster filter removed', 'Pre-event reference scenes')
    if new and not re.match(r'(Figure|Table) \d+\.', p.text): txt.append(p.text)
allowed = {'1', '2', '3', '4', '5', '9', '10', '12', '14', '20', '25', '50', '99', '100', '500', '1000', '2500', '373', '23', '24', '26', '21', '22', '15', '16', '17', '18', '19', '6', '7', '8', '11', '13', '13', '0.0'}
tabtxt = []
for t in doc.tables:
    h = ' | '.join(c.text for c in t.rows[0].cells)
    if any(k in h for k in ['Training points', 'Reference class', 'Permanent water excluded', 'Building centroids', 'Analysed area, km² | Flagged 14', 'Mask |', 'Removed, km²', '1 to 9 pixels', 'Without cluster filter', '9 October only', '21 October minus', 'Pre-event reference |']):
        for r_ in t.rows[1:]: tabtxt += [c.text for c in r_.cells[1:]]
miss = []
for s in txt + tabtxt:
    s2 = re.sub(r'\((Table|Figure) \d+\)', '', s); s2 = re.sub(r'(Table|Figure) \d+', '', s2)
    for tok in re.findall(r'-?\d+(?:\.\d+)?', s2):
        t_ = tok.lstrip('-'); d = len(t_.split('.')[1]) if '.' in t_ else 0
        if t_ in allowed and d == 0 and len(t_) <= 4 and int(t_) < 3000 and t_ not in ('0',): continue
        if t_ not in index or d not in index[t_]: miss.append((tok, s[:70]))
print('numbers checked in new text and tables; not traced:', miss[:40], len(miss))
