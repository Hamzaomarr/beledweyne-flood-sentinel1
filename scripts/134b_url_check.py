import requests, re, sys, io, html
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36'}
for u in ['https://unosat.org/products/', 'https://esa-worldcover.org/en', 'https://dynamicworld.app/', 'https://dataspace.copernicus.eu/']:
    t = requests.get(u, headers=H, timeout=40).text
    print(u, '| <title>:', re.findall(r'<title[^>]*>(.*?)</title>', t, re.I | re.S)[:1], '| h1:', [re.sub(r'<[^>]+>', '', x).strip()[:80] for x in re.findall(r'<h1[^>]*>(.*?)</h1>', t, re.I | re.S)][:2], '| years:', sorted(set(re.findall(r'\b(20[12]\d)\b', re.sub(r'<script.*?</script>', '', t, flags=re.S))))[-6:])
    try:
        c = requests.get('http://web.archive.org/cdx/search/cdx', params=dict(url=u.replace('https://', ''), output='json', limit=1, fl='timestamp,statuscode'), timeout=60).json(); print('   first archive capture:', c[1:] )
    except Exception as e: print('   cdx err', e)
a = requests.get('https://arxiv.org/abs/2107.12283', headers=H, timeout=40).text
print(re.findall(r'<meta name="citation_title" content="([^"]+)"', a), re.findall(r'<meta name="citation_(?:date|online_date)" content="([^"]+)"', a))
