"""Style and punctuation scan for a Methods .docx. Usage python 26_check_methods_docx.py file.docx"""
import sys, re, zipfile, docx
f = sys.argv[1]; d = docx.Document(f)
txt = [p.text for p in d.paragraphs]
for t in d.tables:
    for r in t.rows:
        for c in r.cells: txt.append(c.text)
full = '\n'.join(txt)
chk = re.sub(r'\((Figure|Table) \d\)', '', full); chk = re.sub(r'10\.\d{4}/\S+', 'DOI', chk)
bad = False
for ch in ['(', ')', ':', ';', '—', '–']:
    if ch in chk:
        bad = True; print('FOUND', repr(ch), [chk[max(0, m.start() - 40):m.start() + 30] for m in re.finditer(re.escape(ch), chk)][:3])
for p in d.paragraphs:
    for s in re.split(r'(?<=[.!?])\s+', p.text):
        if s and s[0].isdigit(): bad = True; print('SENTENCE STARTS WITH NUMERAL:', s[:60])
print('punctuation scan clean' if not bad else 'ISSUES FOUND')
print('headings:', [p.text for p in d.paragraphs if p.style.name.startswith('Heading')])
x = zipfile.ZipFile(f).read('word/document.xml').decode()
print('DOI links', x.count('<w:hyperlink'), '| tables', len(d.tables), '| images', len(d.inline_shapes), '| words', len(full.split()), '| placeholders', full.count('[...]'))
print('figure and table citations in order:', [m.group(0) for m in re.finditer(r'\((Figure|Table) \d\)', full)])
