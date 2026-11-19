import re, zipfile, docx, json, urllib.request, urllib.parse, time
B=r'.'
z=zipfile.ZipFile(B+r'\MANUSCRIPT_full.docx')
rels=z.read('word/_rels/document.xml.rels').decode()
rid={m.group(1):m.group(2) for m in re.finditer(r'Id="(rId\d+)"[^>]*Target="(https://doi.org/[^"]+)"',rels)}
rid.update({m.group(2):m.group(1) for m in re.finditer(r'Target="(https://doi.org/[^"]+)"[^>]*Id="(rId\d+)"',rels) if False})
x=z.read('word/document.xml').decode()
hl=re.findall(r'<w:hyperlink[^>]*r:id="(rId\d+)"[^>]*>(.*?)</w:hyperlink>',x,flags=re.S)
rows=[]
for r,body in hl:
    t=''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',body))
    rows.append((t,rid.get(r)))
bad=[(t,u) for t,u in rows if not u or u!='https://doi.org/'+t]
print('hyperlinks',len(rows),'mismatch visible vs target',bad[:5])
d=docx.Document(B+r'\MANUSCRIPT_full.docx')
full='\n'.join(p.text for p in d.paragraphs)+'\n'.join(c.text for t in d.tables for r in t.rows for c in r.cells)
raw=set(re.findall(r'10\.\d{4,9}/[^\s,;)]+',full)); vis=set(t for t,u in rows)
print('visible DOI strings not hyperlinked:',[r for r in raw if r.rstrip('.') not in vis][:5])
print('doi.org text or author-year left:',re.findall(r'https?://\S+',full)[:3])
out={}
for doi in sorted(vis):
    try:
        j=json.load(urllib.request.urlopen(urllib.request.Request('https://api.crossref.org/works/'+urllib.parse.quote(doi),headers={'User-Agent':'mailto:YOUR_EMAIL'}),timeout=30))['message']
        out[doi]=dict(title=j.get('title',[''])[0],year=(j.get('issued',{}).get('date-parts') or [[None]])[0][0],journal=(j.get('container-title') or [''])[0],au=(j.get('author') or [{}])[0].get('family'),retracted=bool(j.get('update-to')) or any(u.get('type')=='retraction' for u in j.get('relation',{}).get('is-retracted-by',[]) ) if False else None,upd=[u.get('type') for u in j.get('updated-by',[])] if 'updated-by' in j else [])
    except Exception as e: out[doi]=dict(err=str(e)[:80])
    time.sleep(.2)
json.dump(out,open(B+r'\outputs\doi_crossref_check.json','w'),indent=1)
for k,v in out.items(): print(k,'|',v.get('year'),v.get('au'),'|',v.get('journal'),'|',(v.get('title') or v.get('err'))[:80],'|',v.get('upd'))
