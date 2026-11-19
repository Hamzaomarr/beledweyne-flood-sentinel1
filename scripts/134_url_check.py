import requests, re, json, sys, io, html
from urllib.parse import urlparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
urls = ['https://arxiv.org/pdf/2107.12283', 'https://dataspace.copernicus.eu/', 'https://unosat.org/products/', 'https://esa-worldcover.org/', 'https://dynamicworld.app/']
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36', 'Accept-Language': 'en'}
def meta(t, names):
    for n in names:
        m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)["\']' % re.escape(n), t, re.I) or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % re.escape(n), t, re.I)
        if m: return html.unescape(m.group(1))
for u in urls:
    try:
        r = requests.get(u, headers=H, timeout=40, allow_redirects=True)
        t = r.text if 'html' in r.headers.get('content-type', '') else ''
        ti = meta(t, ['og:title', 'twitter:title']) or (re.search(r'<title[^>]*>(.*?)</title>', t, re.I | re.S).group(1).strip() if re.search(r'<title', t, re.I) else None)
        pub = meta(t, ['og:site_name', 'publisher', 'author', 'application-name'])
        yr = meta(t, ['article:published_time', 'article:modified_time', 'citation_publication_date', 'datePublished', 'dateModified', 'og:updated_time'])
        jl = re.findall(r'"(?:datePublished|dateModified)"\s*:\s*"([^"]+)"', t)
        print(u, r.status_code, '->', r.url, r.headers.get('content-type'), '\n   title:', html.unescape(ti or '')[:150], '| site:', pub, '| date meta:', yr, '| jsonld:', jl[:2], '| copyright:', re.findall(r'©[^<]{0,80}', t)[:2])
    except Exception as e: print(u, 'ERR', e)
r = requests.get('http://export.arxiv.org/api/query?id_list=2107.12283', timeout=40); print(re.findall(r'<(?:title|published|updated)>([^<]+)', r.text)[:4])
