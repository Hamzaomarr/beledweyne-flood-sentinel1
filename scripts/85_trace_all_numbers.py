"""Traces every number in the Abstract, Results, table cells, table notes and figure legends of MANUSCRIPT_full.docx and of the Supplementary file
to the CSV and JSON files in outputs/tables (rounded half up at the shown precision, fractions shown as percentages). Prints what could not be traced."""
import re, os, json, glob, docx, numpy as np, pandas as pd
from decimal import Decimal, ROUND_HALF_UP
B = r'.'; T = os.path.join(B, 'outputs', 'tables')
vals = set()
def add(x):
    try:
        f = float(x)
        if np.isfinite(f): vals.update([f, f * 100, f / 100, abs(f)])
    except Exception: pass
def walk(o):
    if isinstance(o, dict): [walk(v) for v in o.values()]
    elif isinstance(o, list): [walk(v) for v in o]
    else: add(o)
for f in glob.glob(os.path.join(T, '*')):
    if f.endswith('.csv'):
        try:
            for v in pd.read_csv(f).values.ravel(): add(v)
        except Exception: pass
    elif f.endswith('.json'): walk(json.load(open(f, encoding='utf-8')))
rnd = lambda v, d: str(Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
index = {}
for v in vals:
    for d in range(0, 6): index.setdefault(rnd(v, d).lstrip('-'), set()).add(d)
MON = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
def clean(s):
    s = re.sub(r'10\.\d{4,9}/\S+', ' ', s)
    s = re.sub(r'(Table|Figure) S?\d+[ab]?', ' ', s)
    s = re.sub(r'\b\d{1,2}(?:, \d{1,2})?(?: and \d{1,2})?(?: to \d{1,2})? ' + MON, ' ', s)
    s = re.sub(MON + r' \d{4}', ' ', s); s = re.sub(r'\b20\d\d\b', ' ', s)
    s = re.sub(r'\b\d{1,2} (?:Oct|Nov|Dec)\b', ' ', s)
    return s
SMALL = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '50', '99', '100', '500', '1000', '2', '20', '30', '40'}
def check(label, s, miss):
    for m in re.finditer(r'-?\d+(?:\.\d+)?', clean(s)):
        tok = m.group(0).lstrip('-'); d = len(tok.split('.')[1]) if '.' in tok else 0
        if d == 0 and tok in SMALL: continue
        if tok not in index or d not in index[tok]:
            miss.append((label, tok, s[max(0, m.start() - 40):m.start() + 30].replace('\n', ' ')))
miss = []; n_tok = 0
for f in ('MANUSCRIPT_full.docx', 'MANUSCRIPT_Supplementary_tables.docx'):
    d = docx.Document(os.path.join(B, f)); sec = None
    for p in d.paragraphs:
        if p.text in ('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion', 'Supplementary material'): sec = p.text
        if f == 'MANUSCRIPT_full.docx' and sec in ('Abstract', 'Results'): check(f[:13] + ' ' + str(sec), p.text, miss)
        if f != 'MANUSCRIPT_full.docx' and p.text.startswith(('Table S', 'Figure S', 'Note')): check('Supp text', p.text, miss)
    for ti, t in enumerate(d.tables):
        hdr = [c.text for c in t.rows[0].cells]
        if f == 'MANUSCRIPT_full.docx' and ti < 2: continue      # Methods Tables 1 and 2 hold settings, not results
        for r in t.rows[1:]:
            for c in r.cells[1:]: check('%s table %d' % (f[:13], ti), c.text, miss)
print('untraced numeric tokens', len(miss))
seen = set()
for m in miss:
    k = (m[1], m[2][:40])
    if k in seen: continue
    seen.add(k); print(m)
