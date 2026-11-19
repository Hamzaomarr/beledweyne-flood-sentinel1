"""Language edit of the Methods generator (script 14) and rendering of the Conclusion from conclusion_source.txt."""
import os, docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
B = r'.'
p = B + r'\scripts\14_make_methods_docx.js'; t = open(p, encoding='utf-8').read()
a = t.index("K.push(body('The effect of the evaluation grid was checked"); b = t.index('\n', a)
new = ("K.push(body('The effect of the evaluation grid was checked over the extent of the 10 m town rasters. The flagged area of 14 November 2023 without the terrain mask was computed in Earth Engine on 10 m, 20 m and 30 m grids and with the local Python implementation, using the rule without the minimum cluster size. The exported 10 m flag layer was also compared with the local implementation over the same extent. "
       "To separate the effect of counting on a coarser grid from the effect of the median window, which spans 50 m on a 10 m grid and 100 m on a 20 m grid, the local 10 m flag layer was averaged to 20 m, the inputs were sampled at 20 m with 4 sampling offsets before the 5 by 5 pixel filter was applied, and the local 10 m rule was run with windows of 9 by 9 and 11 by 11 pixels. "
       "The Earth Engine run with inputs reprojected to 10 m still computed the filter at the 20 m output scale.'));")
t = t[:a] + new + t[b:]
# the sentence on configurations without the cluster filter belongs with the configurations
old = "each configuration is defined together with its result (Table 7).'));"
assert t.count(old) == 1
t = t.replace(old, "each configuration is defined together with its result (Table 7). The flagged area of each configuration was also computed without the minimum cluster size.'));")
open(p, 'w', encoding='utf-8', newline='').write(t)
# Conclusion
P = [x.strip() for x in open(B + r'\conclusion_source.txt', encoding='utf-8').read().strip().split('\n\n')]
d = docx.Document(B + r'\MANUSCRIPT_Conclusion.docx'); body = d.element.body
for el in list(body):
    if not el.tag.endswith('sectPr'): body.remove(el)
def add(txt, head=False):
    q = d.add_paragraph(); r = q.add_run(txt); r.font.name = 'Cambria'; r.font.size = Pt(12); r.bold = head or None
    q.alignment = WD_ALIGN_PARAGRAPH.LEFT if head else WD_ALIGN_PARAGRAPH.JUSTIFY; q.paragraph_format.space_after = Pt(10); q.paragraph_format.line_spacing = 1.0
add('Conclusion', True)
for x in P: add(x)
d.save(B + r'\MANUSCRIPT_Conclusion.docx'); print('methods edited, conclusion paragraphs', len(P))
