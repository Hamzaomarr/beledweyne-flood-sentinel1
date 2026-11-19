import docx, re
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
B = r'.'
P = ["Radar mapping of the 2023 Deyr flood placed the flood signal mainly along the river corridor, where it fell chiefly on cropland and on surfaces mapped as built-up. The footprint appears credible where inundation was extensive and open, but many flooded pixels were missed, especially in built-up areas, on bare surfaces and beneath vegetation, where a rule based on falling backscatter is least suited. Flagged area also shifted substantially with the choice of pre-event scene and with cluster filtering, whereas terrain masks mattered little.",
"These results matter because radar flood totals depend on analytical choices that readers rarely see, and agreement obtained in a flooded town cannot be carried across the surrounding rangeland, where no reference mapping exists. Independent building footprints showed that the built-up class includes much area without buildings, so the exposure of settlements is better judged from building data than from that class. Locally calibrated rules can complement operational flood services where optical reference mapping exists.",
"Flagged area in built-up pixels near buildings is best treated as a lower bound, and the cropland footprint is the more reliable part of the map. Exposure estimates should be reported together with their sensitivity to the pre-event reference and to filtering, and intensity and persistence classes should be read as confidence layers rather than as depth.",
"Future work should add independent reference data outside the town, test a multi-date reference, add interferometric coherence for urban areas, and anchor the totals with gauge, rainfall and field observations."]
open(B + r'\conclusion_source.txt', 'w', encoding='utf-8').write('\n\n'.join(P))
d = docx.Document(B + r'\MANUSCRIPT_Discussion.docx'); body = d.element.body
for el in list(body):
    if not el.tag.endswith('sectPr'): body.remove(el)
def add(t, head=False):
    p = d.add_paragraph(); r = p.add_run(t); r.font.name = 'Cambria'; r.font.size = Pt(12); r.bold = head or None
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if head else WD_ALIGN_PARAGRAPH.JUSTIFY; p.paragraph_format.space_after = Pt(10); p.paragraph_format.line_spacing = 1.0
add('Conclusion', True)
for t in P: add(t)
d.save(B + r'\MANUSCRIPT_Conclusion.docx'); txt = ' '.join(P)
print(len(txt.split()), [c for c in ':;()\u2013\u2014' if c in txt], re.findall(r'\d', txt), re.findall(r'\b[A-Z]{2,}\b', txt))
