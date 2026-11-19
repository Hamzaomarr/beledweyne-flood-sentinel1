import docx, os, sys, io, re, json
from docx.oxml.ns import qn
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'.'; REV = os.path.join(B, 'Revision')
M = docx.Document(os.path.join(REV, 'Manuscript_revised_colored.docx')); MR = docx.Document(os.path.join(REV, 'Manuscript_revised_red.docx'))
S = docx.Document(os.path.join(REV, 'Supplementary_revised_colored.docx')); SR = docx.Document(os.path.join(REV, 'Supplementary_revised_red.docx'))
L = docx.Document(os.path.join(REV, 'Response_to_reviewers.docx'))
def alltext(d): return '\n'.join(''.join(t.text or '' for t in p.iter(qn('w:t'))) for p in d.element.body.iter(qn('w:p')))
mt, mrt, st, srt, lt = map(alltext, (M, MR, S, SR, L))
print('1 text identical colored vs red: main', mt == mrt, 'supp', st == srt)
# hyperlinks identical
def links(d): return [(d.part.rels[h.get(qn('r:id'))].target_ref, ''.join(t.text or '' for t in h.iter(qn('w:t'))), (h.find('.//' + qn('w:color')).get(qn('w:val')) if h.find('.//' + qn('w:color')) is not None else None)) for h in d.element.body.iter(qn('w:hyperlink')) if h.get(qn('r:id'))]
lm, lr = links(M), links(MR)
print('2 hyperlinks count colored/red', len(lm), len(lr), 'targets+text same', [(a[0], a[1]) for a in lm] == [(a[0], a[1]) for a in lr], 'red link colours', sorted(set(x[2] for x in lr), key=str))
# all visible DOI text equals target
bad = [x for x in lm if x[0].startswith('https://doi.org/') and x[0][16:].lower() != x[1].lower()]; print('3 DOI visible text mismatches', len(bad))
# table and figure references
refs = set(re.findall(r'Table S\d+', mt)); titles = set(re.findall(r'^Table S\d+', st, re.M)); print('4 supp tables cited in main', sorted(refs, key=lambda x: int(x[7:])), 'missing in supplement', sorted(refs - titles), 'in supplement but not cited', sorted(titles - refs, key=lambda x: int(x[7:])))
frefs = set(re.findall(r'Figure S\d', mt)); ft = set(re.findall(r'^Figure S\d', st, re.M)); print('   fig refs', frefs, 'missing', frefs - ft)
# response letter checks
print('5 letter: red or colour runs', sum(1 for r in L.element.body.iter(qn('w:r')) if r.find(qn('w:rPr') + '/' + qn('w:color')) is not None), '| line-number words', re.findall(r'\bline[s]? \d+', lt), '| supplement items cited in letter', sorted(set(re.findall(r'Tables? S\d+(?: and S\d+)?|Figure S\d', lt))))
lt_refs = set(re.findall(r'S(\d+)', ' '.join(re.findall(r'Tables? S\d+(?: and S\d+)?', lt)))); print('   letter table numbers all exist', all(('Table S' + n) in titles for n in lt_refs))
# copied manuscript text in letter: any 8-word shingle shared with new text
log = json.load(open(os.path.join(B, 'outputs', 'change_log_raw.json'), encoding='utf-8')) + json.load(open(os.path.join(B, 'outputs', 'change_log_supp.json'), encoding='utf-8'))
def shingles(t, n=8): w = re.findall(r'\w+', t.lower()); return {' '.join(w[i:i + n]) for i in range(len(w) - n + 1)}
sl = shingles(lt.split('Reviewer 2, comment 1')[0] if False else ''.join(p.text + '\n' for p in L.paragraphs if p.text.startswith('Response') or p.paragraph_format.left_indent is not None and not p.text.startswith('Comment')))
newsh = set()
for x in log: newsh |= shingles(x['new'])
print('6 letter responses sharing 8-word runs with manuscript changes', len(sl & newsh), list(sl & newsh)[:3])
# every comment id in log
ids = set()
for x in log:
    for c in re.split(r',\s*', x['comment']): ids.add(c.strip())
print('7 comment ids in change log', sorted(ids))
# residual reference list / mendeley
print('8 sdt left', len(list(M.element.body.iter(qn('w:sdt')))), '| "References" heading present', bool(re.search(r'^References$', mt, re.M)), '| numbered citation like [12]', re.findall(r'\[\d+(?:[,\u2013-]\d+)*\]', mt)[:3])
print('9 placeholder', re.findall(r'\[Zenodo DOI to be inserted\]', mt))
print('10 paragraphs containing severity', [m for m in re.findall(r'[^.]*severity[^.]*\.', mt)])
