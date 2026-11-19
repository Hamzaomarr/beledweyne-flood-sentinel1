"""Counts the lines each body paragraph occupies in Cambria 12 pt on A4 with 1 inch margins (text width 451.3 pt), using the real font metrics and greedy wrapping with breaks at spaces and after hyphens.
Usage: python 99a_paragraph_lines.py [docx] [--all]"""
import sys, re, docx
from PIL import ImageFont
FONT = ImageFont.truetype(r'C:\Windows\Fonts\cambria.ttc', 120, index=0)   # 10 px per pt
WIDTH = 4513.0
SPACE = FONT.getlength(' ')
def lines(text):
    text = re.sub(r'\s+', ' ', text.strip())
    toks = []
    for w in text.split(' '):
        parts = re.findall(r'[^-]*-|[^-]+', w) or [w]
        toks.append(parts)
    n, cur = 1, 0.0
    for parts in toks:
        first = True
        for part in parts:
            wlen = FONT.getlength(part); sp = 0 if cur == 0 else (SPACE if first else 0)
            if cur + sp + wlen > WIDTH and cur > 0: n += 1; cur = wlen
            else: cur += sp + wlen
            first = False
    return n
SECTIONS = ('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion', 'Supplementary material')
def analyse(path):
    d = docx.Document(path); out = []; sec = sub = None
    for p in d.paragraphs:
        t = p.text.strip()
        if not t: continue
        runs = [r for r in p.runs if r.text.strip()]
        allbold = bool(runs) and all(r.bold for r in runs)
        if t in SECTIONS: sec, sub = t, None; continue
        if allbold and not re.match(r'(Figure|Table) S?\d', t) and len(t) < 90: sub = t; continue
        if re.match(r'(Figure|Table) S?\d+\.', t) or t.startswith('Note.'): continue
        out.append((sec, sub, lines(t), t))
    return out
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else r'.\MANUSCRIPT_full.docx'
    rows = analyse(path); cur = None
    for sec, sub, n, t in rows:
        if (sec, sub) != cur: print('\n[%s] %s' % (sec, sub or '')); cur = (sec, sub)
        flag = '' if 7 <= n <= 15 else ('  <-- SHORT' if n < 7 else '  <-- LONG')
        print('  %2d lines%s | %s' % (n, flag, t[:70]))
