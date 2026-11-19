import docx, base64, json, re, sys, io, os, difflib, time, requests
from docx.oxml.ns import qn
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'.'
orig = docx.Document(os.path.join(B, 'MANUSCRIPT_full.docx'))
meta = {}
for s in orig.element.body.iter(qn('w:sdt')):
    t = s.find(qn('w:sdtPr') + '/' + qn('w:tag'))
    if t is None or not t.get(qn('w:val')).startswith('MENDELEY_CITATION'): continue
    b = t.get(qn('w:val')).split('_', 3)[3]; b += '=' * (-len(b) % 4)
    for it in json.loads(base64.b64decode(b))['citationItems']:
        dd = it['itemData']
        if dd.get('DOI'): meta[dd['DOI'].lower()] = dict(title=dd.get('title', ''), author=(dd.get('author') or [{}])[0].get('family', ''), year=(dd.get('issued', {}).get('date-parts') or [[None]])[0][0], journal=dd.get('container-title', ''))
def doc_links(path):
    d = docx.Document(path); out = []
    for h in d.element.body.iter(qn('w:hyperlink')):
        rid = h.get(qn('r:id'))
        if rid: out.append((d.part.related_parts[rid].target_ref if False else d.part.rels[rid].target_ref, ''.join(t.text or '' for t in h.iter(qn('w:t')))))
    return out
links = doc_links(os.path.join(B, 'Revision', 'Manuscript_revised_colored.docx'))
dois = []; urls = []
for tgt, vis in links:
    m = re.match(r'https?://(dx\.)?doi\.org/(.+)$', tgt)
    if m:
        x = m.group(2)
        if x.lower() not in [y.lower() for y in dois]: dois.append(x)
    elif tgt.startswith('mailto:'): pass
    elif tgt not in urls: urls.append(tgt)
print(len(dois), 'unique DOIs'); print(len(urls), 'non-DOI urls', urls)
rows = []
for x in dois:
    r = None
    for k in range(3):
        try:
            r = requests.get('https://api.crossref.org/works/' + x, timeout=30, headers={'User-Agent': 'revision-check/1.0'})
            break
        except Exception as e: time.sleep(2)
    if r is None or r.status_code != 200: rows.append(dict(doi=x, status=getattr(r, 'status_code', 'ERR'))); continue
    m = r.json()['message']; title = m['title'][0] if m.get('title') else ''; au = (m.get('author') or [{}])[0].get('family', ''); yr = (m.get('issued', {}).get('date-parts') or [[None]])[0][0]
    ref = meta.get(x.lower()); sim = difflib.SequenceMatcher(None, re.sub(r'\W+', ' ', title.lower()), re.sub(r'\W+', ' ', (ref or {}).get('title', '').lower())).ratio() if ref else None
    upd = [u.get('type') for u in m.get('update-to', [])] if m.get('update-to') else []
    rows.append(dict(doi=x, status=200, title=title, author=au, year=yr, journal=(m.get('container-title') or [''])[0], title_similarity=None if sim is None else round(sim, 2), ref_author=(ref or {}).get('author'), ref_year=(ref or {}).get('year'), updates=upd, new=ref is None))
json.dump(dict(dois=dois, urls=urls, rows=rows), open(os.path.join(B, 'outputs', 'doi_check_round2.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for r in rows: print(r['doi'], r['status'], r.get('title_similarity'), r.get('year'), r.get('ref_year'), r.get('author'), r.get('ref_author'), r.get('updates'), 'NEW' if r.get('new') else '')
