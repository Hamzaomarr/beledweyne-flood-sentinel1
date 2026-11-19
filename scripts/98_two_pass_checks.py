"""Final mechanics checks for the two-pass edit on MANUSCRIPT_full.docx and the supplementary file."""
import re, zipfile, docx
from docx.shared import Pt
B = r'.'
NUM = r'\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fifteen|twenty|hundred|thirds?|percent|per cent)\b'
for f in ('MANUSCRIPT_full.docx', 'MANUSCRIPT_Supplementary_tables.docx'):
    d = docx.Document(B + '\\' + f); print('=====', f)
    items = [('p', p.text) for p in d.paragraphs] + [('cell', c.text) for t in d.tables for r in t.rows for c in r.cells]
    clean = lambda s: re.sub(r'\((?:Figure|Table)s? S?\d+[ab]?(?: and (?:Figure|Table) S?\d+[ab]?)?\)', '', re.sub(r'10\.\d{4,9}/\S+', ' DOI ', s))
    out = {'parens': [], 'colon': [], 'semicolon': [], 'dash': [], 'numword': [], 'numstart': [], 'percentword': []}
    for k, s in items:
        c = clean(s)
        if '(' in c or ')' in c: out['parens'].append(c[:90])
        if ':' in c and not re.match(r'(Background|Methods|Results|Conclusion|Keywords):', c): out['colon'].append(c[:90])
        if ';' in c: out['semicolon'].append(c[:90])
        if '\u2013' in c or '\u2014' in c: out['dash'].append(c[:90])
        for m in re.finditer(NUM, c, flags=re.I): out['numword'].append(c[max(0, m.start() - 35):m.end() + 25])
        for sen in re.split(r'(?<=[.!?])\s+', c):
            if re.match(r'\s*\d', sen): out['numstart'].append(sen[:70])
        if re.search(r'per ?cent', c, flags=re.I): out['percentword'].append(c[:60])
    for k, v in out.items(): print(k, len(v), v[:12])
    # italics anywhere, bold in tables
    it = sum(1 for p in d.paragraphs for r in p.runs if r.italic) + sum(1 for t in d.tables for r in t.rows for c in r.cells for p in c.paragraphs for run in p.runs if run.italic)
    tb = sum(1 for t in d.tables for r in t.rows for c in r.cells for p in c.paragraphs for run in p.runs if run.bold)
    print('italic runs', it, '| bold runs in tables', tb)
    # sentence case: captions, headings, table headers
    sc = []
    heads = [p.text for p in d.paragraphs if p.runs and all((r.bold or not r.text.strip()) for r in p.runs)] + [re.sub(r'^(Figure|Table) S?\d+\.\s*', '', p.text) for p in d.paragraphs if re.match(r'(Figure|Table) S?\d+\.', p.text)] + [c.text for r in (t.rows[0] for t in d.tables) for c in r.cells]
    PROPER = {'Sentinel-1', 'Deyr', 'Beledweyne', 'Somalia', 'UNOSAT', 'Pléiades', 'Gaofen-2', 'WorldView-2', 'WorldCover', 'HAND', 'VV', 'VH', 'ΔVV', 'ΔVH', 'Python', 'Earth', 'Engine', 'Open', 'Buildings', 'Dynamic', 'World', 'November', 'December', 'October', 'Kappa', 'Local', 'MERIT', 'Hydro', 'Copernicus', 'Global', 'Surface', 'Water', 'Climate', 'Hazards', 'Group', 'InfraRed', 'Precipitation', 'Station', 'European', 'Space', 'Agency', 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion', 'Table', 'Figure', 'Note', 'GLO-30', 'Fixed', 'Final'}
    for h in heads:
        words = h.split()
        for w in words[1:]:
            w2 = w.strip(',.')
            if w2[:1].isupper() and w2 not in PROPER and not re.match(r'^[A-Z]{1,3}\d*$', w2): sc.append((h[:60], w2))
    print('possible sentence-case issues', sc[:20])
z = zipfile.ZipFile(B + r'\MANUSCRIPT_full.docx'); x = z.read('word/document.xml').decode()
print('hyperlinks', len(re.findall(r'<w:hyperlink', x)), '| visible https text', len(re.findall(r'>https?://', x)))
d = docx.Document(B + r'\MANUSCRIPT_full.docx'); print('TITLE:', d.paragraphs[0].text)
fonts = {(r.font.name, r.font.size) for p in d.paragraphs for r in p.runs if r.text.strip()}; print('paragraph fonts', fonts)
print('body alignment', {str(p.alignment) for p in d.paragraphs if p.text.strip() and not re.match(r'(Figure|Table) \d', p.text) and not all((r.bold or not r.text.strip()) for r in p.runs) and not p.text.startswith('Note.')})
