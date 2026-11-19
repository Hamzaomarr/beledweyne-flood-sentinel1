import docx, re, copy
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
B=r'.'
P=["Radar mapping of the 2023 Deyr flood placed the flood signal mainly along the river corridor, where it fell chiefly on cropland and built-up land. The footprint appears credible where inundation was extensive and open, but many flooded pixels were missed, especially in built-up areas, on bare surfaces and beneath vegetation, where a rule based on falling backscatter is least suited. Flagged area also shifted substantially with the choice of pre-event scene and with cluster filtering, whereas terrain masks mattered little.",
"These results matter because radar flood totals depend on analytical choices that readers rarely see, and agreement obtained in a flooded town cannot be carried across the surrounding rangeland. Locally calibrated rules can complement operational flood services where optical reference mapping exists, as it did after these floods. Class-level exposure summaries give planners a way to relate flood footprints to cropland and settlements.",
"Flagged area in vegetated and built-up land is best treated as a lower bound, and the cropland footprint is the more reliable part of the map. Exposure estimates should be reported together with their sensitivity to the pre-event reference and to filtering, and intensity and persistence classes should be read as confidence layers rather than as depth.",
"Future work should test a multi-date reference, add interferometric coherence for urban areas, train models on optical flood polygons, and anchor the totals with gauge, rainfall and field observations."]
open(B+r'\conclusion_source.txt','w',encoding='utf-8').write('\n\n'.join(P))
d=docx.Document(B+r'\MANUSCRIPT_Discussion.docx')
body=d.element.body
for el in list(body):
    if el.tag.endswith('sectPr'): continue
    body.remove(el)
ps=[]
def add(t,head=False):
    p=d.add_paragraph(); r=p.add_run(t); r.font.name='Cambria'; r.font.size=Pt(12); r.bold=head or None
    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if head else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after=Pt(10); p.paragraph_format.line_spacing=1.0
    sp=body.find(docx.oxml.ns.qn('w:sectPr'))
add('Conclusion',True)
for t in P: add(t)
d.save(B+r'\MANUSCRIPT_Conclusion.docx')
txt=' '.join(P); print(len(txt.split()), [c for c in ':;()\u2013\u2014' if c in txt], re.findall(r'\d',txt), re.findall(r'\b[A-Z]{2,}\b',txt), [w for w in ['this study','our','present'] if w in txt.lower()])
s=open(B+r'\scripts\53_combine_manuscript.py',encoding='utf-8').read()
s=s.replace("'MANUSCRIPT_Discussion.docx']","'MANUSCRIPT_Discussion.docx', 'MANUSCRIPT_Conclusion.docx']").replace("('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion')","('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion')")
open(B+r'\scripts\53_combine_manuscript.py','w',encoding='utf-8').write(s)
