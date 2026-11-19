"""Full abstracts by DOI from OpenAlex, plus Crossref bibliographic check (title, journal, year, type, update records)."""
import json, sys, urllib.request, urllib.parse
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:YOUR_EMAIL'}); return json.load(urllib.request.urlopen(req, timeout=40))
def abstract(inv):
    if not inv: return ''
    pos = {}
    for w, ps in inv.items():
        for p in ps: pos[p] = w
    return ' '.join(pos[i] for i in sorted(pos))
for d in sys.argv[1:]:
    try:
        oa = get('https://api.openalex.org/works/doi:' + urllib.parse.quote(d, safe='/') + '?select=title,publication_year,primary_location,type,abstract_inverted_index,authorships')
        cr = get('https://api.crossref.org/works/' + urllib.parse.quote(d))['message']
        au = (oa.get('authorships') or [{}])[0].get('author', {}).get('display_name', '')
        print('\n=== %s | %s (%s) | %s | crossref type %s, update-to %d, container %s' % (d, oa['title'], oa['publication_year'], au, cr.get('type'), len(cr.get('update-to') or []), (cr.get('container-title') or [''])[0]))
        print(abstract(oa.get('abstract_inverted_index')) or 'NO ABSTRACT IN OPENALEX')
    except Exception as e: print('\n=== %s | ERROR %s' % (d, str(e)[:100]))
