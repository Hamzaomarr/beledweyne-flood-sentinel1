import docx, os, sys, io, re, collections, json
from docx.oxml.ns import qn
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'.'; REV = os.path.join(B, 'Revision')
SRC = ('00803C', 'E36C0A')
def colors(d):
    c = collections.Counter()
    for r in d.element.body.iter(qn('w:r')):
        x = r.find(qn('w:rPr') + '/' + qn('w:color'))
        if x is not None: c[x.get(qn('w:val')).upper()] += 1
    return c
def shading(d):
    n = 0
    for r in d.element.body.iter(qn('w:r')):
        rp = r.find(qn('w:rPr'))
        if rp is not None and (rp.find(qn('w:highlight')) is not None or rp.find(qn('w:shd')) is not None): n += 1
    return n
for nm in ('MANUSCRIPT_full.docx', 'MANUSCRIPT_Supplementary_materials.docx'):
    d = docx.Document(os.path.join(REV, nm)); print('ORIGINAL', nm, dict(colors(d)), 'highlight/shading runs', shading(d), 'tracked ins/del', len(list(d.element.body.iter(qn('w:ins')))) + len(list(d.element.body.iter(qn('w:del')))))
def to_red(src, dst):
    d = docx.Document(src); n_runs = 0
    for r in d.element.body.iter(qn('w:r')):
        x = r.find(qn('w:rPr') + '/' + qn('w:color'))
        if x is not None and x.get(qn('w:val')).upper() in SRC: x.set(qn('w:val'), 'FF0000'); n_runs += 1
    d.save(dst)
    # count red passages = maximal sequences of consecutive red runs within a paragraph (hyperlink runs included)
    d2 = docx.Document(dst); passages = 0
    for p in d2.element.body.iter(qn('w:p')):
        prev = False
        for r in p.iter(qn('w:r')):
            t = ''.join(x.text or '' for x in r.findall(qn('w:t')))
            x = r.find(qn('w:rPr') + '/' + qn('w:color')); red = x is not None and x.get(qn('w:val')).upper() == 'FF0000'
            if not t.strip() and not red: continue
            if red and not prev: passages += 1
            prev = red
    return n_runs, passages
for a, b in (('Manuscript_revised_colored.docx', 'Manuscript_revised_red.docx'), ('Supplementary_revised_colored.docx', 'Supplementary_revised_red.docx')):
    n, p = to_red(os.path.join(REV, a), os.path.join(REV, b))
    d = docx.Document(os.path.join(REV, b)); print(b, 'red runs', n, 'red passages', p, dict(colors(d)), 'highlight/shading', shading(d))
