"""Verifies the formatting pass: text and order unchanged, tables in three-rule style, titles, bold and italics, DOIs."""
import re, zipfile, docx
B = r'.'
from docx.oxml.ns import qn
W = lambda t: qn('w:' + t)
def body_text(path):
    d = docx.Document(path); out = []
    for p in d.paragraphs:
        t = re.sub(r'\s+', ' ', p.text).strip()
        if t and not re.match(r'(Figure|Table) S?\d+\.', t) and not t.startswith('Note.'): out.append(t)
    return ' '.join(out)
def captions(path):
    d = docx.Document(path); return [re.sub(r'\s+', ' ', p.text).strip().rstrip('.') for p in d.paragraphs if re.match(r'(Figure|Table) S?\d+\.', p.text) or p.text.startswith('Note.')]
def cells(path):
    d = docx.Document(path); return [[re.sub(r'\s+', ' ', c.text).strip() for r in t.rows for c in r.cells] for t in d.tables]
for f, old in (('MANUSCRIPT_full.docx', 'backup_before_two_pass'), ('MANUSCRIPT_Supplementary_tables.docx', 'backup_before_two_pass')):
    a, b = B + '\\' + old + '\\' + f, B + '\\' + f
    print('==', f)
    print('body text identical after whitespace normalisation:', body_text(a) == body_text(b), len(body_text(a).split()), len(body_text(b).split()))
    print('captions and notes identical:', captions(a) == captions(b)); print('table cell text identical:', cells(a) == cells(b))
    d = docx.Document(b); body = d.element.body
    # tables
    for ti, tbl in enumerate(body.iterchildren(W('tbl'))):
        rows = tbl.findall(W('tr')); info = []
        for ri, tr in enumerate(rows):
            for tc in tr.findall(W('tc')):
                bd = tc.find(W('tcPr')).find(W('tcBorders')); sides = [] if bd is None else [(e.tag.split('}')[1]) for e in bd]
                if sides: info.append((ri, tuple(sides)))
        hdr = [tr for tr in rows if tr.find(W('trPr')) is not None and tr.find(W('trPr')).find(W('tblHeader')) is not None]
        shd = tbl.findall('.//' + W('shd')); vert = [s for _, ss in info for s in ss if s in ('left', 'right')]
        tp = tbl.find(W('tblPr')); jc = tp.find(W('jc')).get(W('val'))
        okrows = sorted({r for r, _ in info}); ok = (okrows == sorted({0, len(rows) - 1}) or okrows == [0]) and not hdr and not shd and not vert
        if not ok: print('  table', ti, 'rows with rules', okrows, 'of', len(rows), 'repeat-header', len(hdr), 'shading', len(shd), 'vertical', len(vert))
    print('tables checked', len(list(body.iterchildren(W('tbl')))), '| all three-rule, no repeat header, no shading, left aligned:', all(tbl.find(W('tblPr')).find(W('jc')).get(W('val')) == 'left' for tbl in body.iterchildren(W('tbl'))))
    # order: table title above table, figure title below figure, note below table, no full stop
    seq = []
    for el in body:
        tag = el.tag.split('}')[1]
        if tag == 'tbl': seq.append('TABLE')
        elif tag == 'p':
            t = ''.join(x.text or '' for x in el.iter(W('t'))).strip()
            if el.find('.//' + W('drawing')) is not None: seq.append('IMAGE')
            elif re.match(r'Table S?\d+\.', t): seq.append('TT');
            elif re.match(r'Figure S?\d+\.', t): seq.append('FT')
            elif t.startswith('Note.'): seq.append('NOTE')
            if (re.match(r'(Table|Figure) S?\d+\.', t)) and t.endswith('.'): print('  title ends with a full stop:', t[:50])
    s = ' '.join(seq); print('every table title directly above a table:', len(re.findall('TT TABLE', s)) == s.count('TT'), '| every figure title directly after an image:', len(re.findall('IMAGE FT', s)) == s.count('FT'), '| notes follow tables:', s.count('TABLE NOTE') == s.count('NOTE'))
    # bold and italics
    bolds = []; ital = 0
    for p in body.iter(W('p')):
        sid = p.find(W('pPr')).find(W('pStyle')).get(W('val')) if p.find(W('pPr')) is not None and p.find(W('pPr')).find(W('pStyle')) is not None else None
        for r in p.iter(W('r')):
            rp = r.find(W('rPr'))
            if rp is not None and rp.find(W('i')) is not None: ital += 1
            if rp is not None and rp.find(W('b')) is not None: bolds.append((sid, ''.join(t.text or '' for t in r.iter(W('t')))[:25]))
    import collections
    print('italic runs', ital, '| direct bold runs by style', dict(collections.Counter(s for s, _ in bolds)), '| examples', [t for _, t in bolds][:8])
    z = zipfile.ZipFile(b); x = z.read('word/document.xml').decode(); rels = z.read('word/_rels/document.xml.rels').decode()
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(https://doi.org/[^"]+)"', rels)); hl = re.findall(r'<w:hyperlink[^>]*r:id="(rId\d+)"[^>]*>(.*?)</w:hyperlink>', x, flags=re.S)
    vis = lambda s: ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', s)); bad = [(vis(s), rid.get(r)) for r, s in hl if rid.get(r) != 'https://doi.org/' + vis(s)]
    print('hyperlinks', len(hl), 'unique', len({vis(s) for r, s in hl}), 'mismatched', bad, '| empty paragraphs', sum(1 for p in body.iterchildren(W('p')) if not ''.join(t.text or '' for t in p.iter(W('t'))).strip() and p.find('.//' + W('drawing')) is None), '| direct paragraph formatting beyond style', sum(1 for p in body.iter(W('p')) if p.find(W('pPr')) is not None and len(p.find(W('pPr'))) > 1))
