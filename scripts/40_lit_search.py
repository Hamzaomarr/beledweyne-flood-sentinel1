"""Literature search through the OpenAlex API. Prints DOI, year, venue, title and the reconstructed abstract for the top hits of each query, so claims can be matched to what an abstract states."""
import json, sys, urllib.request, urllib.parse
def abstract(inv):
    if not inv: return ''
    pos = {}
    for w, ps in inv.items():
        for p in ps: pos[p] = w
    return ' '.join(pos[i] for i in sorted(pos))
def search(q, n=6, flt='type:article'):
    url = 'https://api.openalex.org/works?search=' + urllib.parse.quote(q) + '&filter=' + flt + '&per-page=%d&select=doi,title,publication_year,primary_location,abstract_inverted_index,cited_by_count,type' % n
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:YOUR_EMAIL'})
    return json.load(urllib.request.urlopen(req, timeout=40))['results']
queries = sys.argv[1:]
for q in queries:
    print('\n#### ' + q)
    try:
        for r in search(q):
            loc = (r.get('primary_location') or {}).get('source') or {}
            ab = abstract(r.get('abstract_inverted_index'))
            print('\n- %s | %s | %s | cited %s\n  %s\n  ABSTRACT: %s' % ((r.get('doi') or '').replace('https://doi.org/', ''), r.get('publication_year'), loc.get('display_name'), r.get('cited_by_count'), r.get('title'), ab[:700]))
    except Exception as e: print('ERROR', e)
