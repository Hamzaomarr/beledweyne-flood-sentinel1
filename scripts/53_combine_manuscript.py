"""Combine Introduction, Methods, Results and Discussion into one manuscript and verify the result."""
import re, zipfile, docx
from docxcompose.composer import Composer
B = r'.'
order = ['MANUSCRIPT_frontmatter.docx', 'MANUSCRIPT_Introduction.docx', 'MANUSCRIPT_Methods.docx', 'MANUSCRIPT_Results.docx', 'MANUSCRIPT_Discussion.docx', 'MANUSCRIPT_Conclusion.docx']
master = docx.Document(B + '\\' + order[0]); comp = Composer(master)
for f in order[1:]: comp.append(docx.Document(B + '\\' + f))
out = B + r'\MANUSCRIPT_full.docx'; comp.save(out)
# ---- verification
d = docx.Document(out); paras = [p.text for p in d.paragraphs]
print('top-level section titles in order:', [p for p in paras if p in ('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion')])
print('tables:', len(d.tables), '| images:', len(d.inline_shapes), '| paragraphs:', len(paras))
z = zipfile.ZipFile(out); rels = z.read('word/_rels/document.xml.rels').decode()
links = re.findall(r'https://doi.org/([^"]+)"', rels); print('DOI hyperlinks:', len(links), '| unique:', len(set(l.lower() for l in links)))
print('media files:', len([n for n in z.namelist() if n.startswith('word/media/')]))
full = '\n'.join(paras)
print('figure and table captions in order:', [re.match(r'(Figure|Table) \d+', p).group(0) for p in paras if re.match(r'(Figure|Table) \d+\.', p)])
cites = [m.group(0) for m in re.finditer(r'\((Figure|Table) \d+\)', full)]; print('in-text exhibit citations in order:', cites)
chk = re.sub(r'\((Figure|Table) \d+\)', '', full); chk = re.sub(r'10\.\d{4}/\S+', 'DOI', chk)
print('banned punctuation in whole manuscript:', [c for c in [':', ';', '\u2014', '\u2013'] if c in chk], '| parentheses outside exhibit citations:', [chk[max(0, m.start() - 25):m.start() + 20] for m in re.finditer(r'[()]', chk)][:3])
print('Methods placeholders remaining:', full.count('[...]'))
w = len(re.sub(r'10\.\d{4}/\S+', '', full).split()); print('approximate words including captions and tables:', w)
