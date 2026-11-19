"""Final format checks on MANUSCRIPT_full.docx and the Supplementary file: DOI format, title, forbidden punctuation."""
import re, zipfile, docx
B = r'.'
d = docx.Document(B + r'\MANUSCRIPT_full.docx'); print('TITLE:', d.paragraphs[0].text)
z = zipfile.ZipFile(B + r'\MANUSCRIPT_full.docx'); rels = z.read('word/_rels/document.xml.rels').decode(); x = z.read('word/document.xml').decode()
rid = {m.group(1): m.group(2) for m in re.finditer(r'Id="(rId\d+)"[^>]*Target="(https://doi.org/[^"]+)"', rels)}
hl = re.findall(r'<w:hyperlink[^>]*r:id="(rId\d+)"[^>]*>(.*?)</w:hyperlink>', x, flags=re.S)
vis = lambda b: ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', b))
bad = [(vis(b), rid.get(r)) for r, b in hl if rid.get(r) != 'https://doi.org/' + vis(b)]
print('hyperlinks', len(hl), '| unique DOIs', len(set(vis(b) for r, b in hl)), '| visible text differs from target:', bad)
txt = '\n'.join(p.text for p in d.paragraphs); print('https text left:', re.findall(r'https?://\S+', txt))
DOI = re.compile(r'10\.\d{4,9}/\S+'); hits = []
for f in ('MANUSCRIPT_full.docx', 'MANUSCRIPT_Supplementary_tables.docx'):
    dd = docx.Document(B + '\\' + f); items = [p.text for p in dd.paragraphs] + [c.text for t in dd.tables for r in t.rows for c in r.cells]
    for s in items:
        c = DOI.sub('DOI', s); c = re.sub(r'\((?:Figure|Table)s? S?\d+[ab]?(?: and (?:Figure|Table) S?\d+[ab]?)?\)', '', c)
        for ch in ':;\u2014\u2013()':
            if ch in c: hits.append((f[:14], ch, c[max(0, c.index(ch) - 30):c.index(ch) + 25].replace('\n', ' ')))
seen = set(); print('forbidden punctuation hits:')
for h in hits:
    if (h[1], h[2]) not in seen: seen.add((h[1], h[2])); print('  ', h)
