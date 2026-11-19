import requests, re, json, os, sys, io, time, csv, html
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'.'; OUT = os.path.join(B, 'Revision', 'Full Text'); os.makedirs(OUT, exist_ok=True)
info = json.load(open(os.path.join(B, 'outputs', 'doi_check_round2.json'), encoding='utf-8'))
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36', 'Accept': 'application/pdf,text/html,*/*'}
def getpdf(u):
    try:
        r = requests.get(u, headers=H, timeout=60, allow_redirects=True)
        if r.status_code == 200 and r.content[:5] == b'%PDF-' and len(r.content) > 40000: return r.content
    except Exception: pass
def words(s): return [w for w in re.findall(r'[a-z0-9]+', s.lower()) if len(w) > 3]
def matches(pdf, title, author):
    try:
        d = fitz.open(stream=pdf, filetype='pdf'); t = ' '.join(d[i].get_text() for i in range(min(2, len(d)))).lower(); n = len(d)
    except Exception: return False, 0
    tw = words(title); hit = sum(w in t for w in tw) / max(1, len(tw))
    return hit >= 0.7, n
def candidates(doi):
    c = []
    try:
        m = requests.get('https://api.crossref.org/works/' + doi, timeout=30).json()['message']
        for l in m.get('link', []):
            if 'pdf' in l.get('content-type', ''): c.append(('crossref link', l['URL']))
    except Exception: pass
    try:
        o = requests.get('https://api.openalex.org/works/doi:' + doi, timeout=30).json()
        for loc in [o.get('best_oa_location')] + (o.get('locations') or []):
            if loc and loc.get('pdf_url'): c.append(('openalex ' + str(loc.get('version')), loc['pdf_url']))
    except Exception: pass
    try:
        e = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=dict(query='DOI:"%s"' % doi, format='json', resultType='lite'), timeout=30).json()
        for r in e.get('resultList', {}).get('result', []):
            if r.get('pmcid'): c.append(('europepmc', 'https://europepmc.org/backend/ptpmcrender.fcgi?accid=%s&blobtype=pdf' % r['pmcid']))
    except Exception: pass
    try:
        t = requests.get('https://doi.org/' + doi, headers=H, timeout=40).text
        for mm in re.findall(r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)', t, re.I): c.append(('landing meta', html.unescape(mm)))
    except Exception: pass
    return c
rows = []
todo = [(r['doi'], r.get('title', ''), r.get('author', ''), r.get('year')) for r in info['rows']] + [('arXiv:2107.12283', 'Continental-Scale Building Detection from High Resolution Satellite Imagery', 'Sirko', 2021)]
for doi, title, author, year in todo:
    short = '_'.join(words(title)[:4]); fn = '%s_%s_%s.pdf' % (re.sub(r'\W', '', author), year, short)
    status = 'not saved'; src = ''; ver = ''; pages = ''
    if doi.startswith('arXiv'):
        cands = [('arxiv', 'https://arxiv.org/pdf/2107.12283')]
    else: cands = candidates(doi)
    seen = set()
    for how, u in cands:
        if u in seen: continue
        seen.add(u); pdf = getpdf(u)
        if pdf:
            ok, n = matches(pdf, title, author)
            if ok:
                open(os.path.join(OUT, fn), 'wb').write(pdf); status = 'saved'; src = u; ver = how; pages = n; break
    print(doi, status, ver, src[:80], flush=True)
    rows.append(dict(citation='%s (%s). %s' % (author, year, title), doi_or_url=doi if not doi.startswith('arXiv') else 'https://arxiv.org/pdf/2107.12283', saved_filename=fn if status == 'saved' else '', source_url=src, version=('preprint' if 'arxiv' in ver else 'published or accepted, route: ' + ver) if status == 'saved' else '', retrieval_status=status, pages=pages))
with open(os.path.join(OUT, 'download_log.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('saved', sum(r['retrieval_status'] == 'saved' for r in rows), 'of', len(rows))
