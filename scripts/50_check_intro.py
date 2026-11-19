"""Mechanical checks for MANUSCRIPT_Introduction.docx and verification of every DOI in Crossref."""
import docx, re, zipfile, json, urllib.request, urllib.parse
B = r'.'
d = docx.Document(B + r'\MANUSCRIPT_Introduction.docx'); paras = [p.text for p in d.paragraphs]; body = paras[1:]; full = '\n'.join(body)
chk = re.sub(r'\((Figure|Table) \d+\)', '', full); chk = re.sub(r'10\.\d{4}/\S+', 'DOI', chk)
print('banned punctuation:', [c for c in [chr(40), chr(41), ':', ';', '\u2014', '\u2013', '[', ']'] if c in chk])
print('numeral-initial sentences:', [s[:30] for p in body for s in re.split(r'(?<=[.!?])\s+', p) if s and s[0].isdigit()])
plain = re.sub(r'10\.\d{4}/\S+', '', full); print('words (DOIs excluded):', len(plain.split()), '| paragraphs:', len(body))
last = re.split(r'(?<=[.!?])\s+', plain.strip())[-1]; print('final sentence starts with This study aims to:', last.startswith('This study aims to'), '| nothing follows:', plain.strip().endswith('.'))
rels = zipfile.ZipFile(B + r'\MANUSCRIPT_Introduction.docx').read('word/_rels/document.xml.rels').decode(); links = re.findall(r'https://doi.org/([^"]+)"', rels)
print('DOI links:', len(links), '| unique:', len(set(l.lower() for l in links)), '| URLs in text other than DOI links:', bool(re.search(r'http', full)))
print('word percent:', 'percent' in full.lower(), '| SAR uses:', len(re.findall(r'\bSAR\b', full)))
disc = open(B + r'\discussion_source.txt', encoding='utf-8').read().lower()
meth = (open(B + r'\scripts\14_make_methods_docx.js', encoding='utf-8-sig').read() + open(B + r'\scripts\25_make_methods_paperstyle_docx.js', encoding='utf-8-sig').read()).lower()
print('overlap with Discussion:', [l for l in set(x.lower() for x in links) if l in disc], '| overlap with Methods:', [l for l in set(x.lower() for x in links) if l in meth])
bad = []
for l in sorted(set(links)):
    try:
        w = json.load(urllib.request.urlopen('https://api.crossref.org/works/' + urllib.parse.quote(l), timeout=30))['message']
        ok = w['type'] == 'journal-article' and not w.get('update-to')
        print(('OK   ' if ok else 'FAIL ') + l + ' | ' + w['title'][0][:60] + ' | ' + w['container-title'][0] + ' ' + str(w['issued']['date-parts'][0][0]))
        if not ok: bad.append(l)
    except Exception as e: print('FAIL', l, str(e)[:50]); bad.append(l)
print('DOI problems:', bad)
sup = [len(g.split(';')) for g in re.findall(r'<<([^>]+)>>', open(B + r'\introduction_source.txt', encoding='utf-8').read())]
print('DOIs per cited statement:', sup, '| single-DOI statements:', sup.count(1))
