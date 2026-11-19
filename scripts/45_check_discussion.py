"""Checks MANUSCRIPT_Discussion.docx against the Discussion brief that can be tested mechanically."""
import docx, re, zipfile, json, urllib.request, urllib.parse
B = r'.'
d = docx.Document(B + r'\MANUSCRIPT_Discussion.docx')
paras = [p.text for p in d.paragraphs]; body = paras[1:]; full = '\n'.join(body)
chk = re.sub(r'\((Figure|Table) \d+\)', '', full); chk = re.sub(r'10\.\d{4}/\S+', 'DOI', chk)
print('banned punctuation:', [c for c in [chr(40), chr(41), ':', ';', '\u2014', '\u2013', '[', ']'] if c in chk])
print('numeral-initial sentences:', [s[:30] for p in body for s in re.split(r'(?<=[.!?])\s+', p) if s and s[0].isdigit()])
plain = re.sub(r'10\.\d{4}/\S+', '', full)
print('words (DOIs excluded):', len(plain.split()), '| paragraphs:', len(body))
x = zipfile.ZipFile(B + r'\MANUSCRIPT_Discussion.docx').read('word/document.xml').decode()
rels = zipfile.ZipFile(B + r'\MANUSCRIPT_Discussion.docx').read('word/_rels/document.xml.rels').decode(); links = re.findall(r'https://doi.org/([^"]+)"', rels); print('DOI links:', len(links), '| unique:', len(set(l.lower() for l in links)))
print('word percent present:', 'percent' in full.lower(), '| SAR defined', full.count('SAR,'), 'time(s), used', len(re.findall(r'\bSAR\b', full)), 'times')
src = open(B + r'\scripts\14_make_methods_docx.js', encoding='utf-8-sig').read() + open(B + r'\scripts\25_make_methods_paperstyle_docx.js', encoding='utf-8-sig').read()
meth = set(m.lower().rstrip("'") for m in re.findall(r"10\.\d{4}/[^\s,;)'\"<]+", src))
print('overlap with DOIs used in either Methods version:', sorted(set(l.lower() for l in links) & meth))
bad = []
for l in sorted(set(links)):
    try:
        w = json.load(urllib.request.urlopen('https://api.crossref.org/works/' + urllib.parse.quote(l), timeout=30))['message']
        ok = w['type'] == 'journal-article' and not w.get('update-to')
        print(('OK   ' if ok else 'FAIL ') + l + ' | ' + w['title'][0][:62] + ' | ' + w['container-title'][0] + ' ' + str(w['issued']['date-parts'][0][0]))
        if not ok: bad.append(l)
    except Exception as e:
        print('FAIL', l, str(e)[:50]); bad.append(l)
print('DOI problems:', bad)
sup = [len(g.split(';')) for g in re.findall(r'<<([^>]+)>>', open(B + r'\discussion_source.txt', encoding='utf-8').read())]
print('DOIs per cited statement:', sup, '| single-DOI statements:', sup.count(1))
