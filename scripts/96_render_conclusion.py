"""Renders conclusion_source.txt to MANUSCRIPT_Conclusion.docx, Cambria 12, justified, single spacing, left aligned bold heading."""
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
B = r'.'
P = [x.strip() for x in open(B + r'\conclusion_source.txt', encoding='utf-8').read().strip().split('\n\n')]
d = docx.Document(B + r'\MANUSCRIPT_Conclusion.docx'); body = d.element.body
for el in list(body):
    if not el.tag.endswith('sectPr'): body.remove(el)
def add(txt, head=False):
    q = d.add_paragraph(); r = q.add_run(txt); r.font.name = 'Cambria'; r.font.size = Pt(12); r.bold = head or None
    q.alignment = WD_ALIGN_PARAGRAPH.LEFT if head else WD_ALIGN_PARAGRAPH.JUSTIFY; q.paragraph_format.space_after = Pt(10); q.paragraph_format.line_spacing = 1.0
add('Conclusion', True)
for x in P: add(x)
d.save(B + r'\MANUSCRIPT_Conclusion.docx'); print('conclusion paragraphs', len(P))
