"""Formatting pass for MANUSCRIPT_full.docx and MANUSCRIPT_Supplementary_tables.docx. Run it last, after script 53 and the supplement render. Usage
    python 99_format_document.py [--measure]      --measure applies the paragraph merges and splits in memory and prints line counts without saving.
Only formatting is changed. Text is neither added, removed nor reworded. Paragraphs are merged or split at sentence boundaries under the paragraph length rule, and exhibits that sat between two merged paragraphs are moved after the merged paragraph.
Rules are applied through styles, and direct formatting is removed."""
import re, sys, copy, docx
from docx.shared import Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
sys.path.insert(0, r'.\scripts')
from importlib import import_module
lines_of = import_module('99a_paragraph_lines').lines
B = r'.'
MEASURE = '--measure' in sys.argv
W = lambda t: qn('w:' + t)
SECTIONS = ('Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion', 'Supplementary material')
# ------------------------------------------------------------------ paragraph merges and splits (main manuscript)
SPLITS = [   # (paragraph starts with, sentence that starts the new paragraph)
 ('Flooding affects more people', 'Observed flooding points the same way.'),
 ('The parameters were calibrated on 1 reference date only', 'After the later dates had been scored once'),
 ('The effect of the evaluation grid was checked', 'The Earth Engine run with inputs reprojected to 10 m'),
 ('The concentration of flagged area along the river', 'The ranking of classes differs from a wetland floodplain'),
 ('The limited recall, and its uneven spread', 'In built-up areas, floodwater against building walls'),
 ('The strong dependence of the flagged area on the pre-event reference', 'Rainfall estimates show no rain'),
 ('The same variability may explain', 'The improvement in agreement shows'),
 ('In VV, the 21 October scene was brighter', 'Rainfall averaged over the study rectangle'),
]
MERGES = [   # (first paragraph starts with, second paragraph starts with)
 ('Observed flooding points the same way.', 'In eastern Africa'), ('Exposure estimates are used to prioritise', 'This study aims to map'),
 ('Backscatter change was calculated', 'A pixel was flagged when'), ('The optical flood mapping used as reference', 'For calibration and accuracy assessment'),
 ('The classifier design was also evaluated', 'Agreement with consensus labels does not test'), ('The calibrated rule, without the minimum cluster size', 'To examine what the minimum cluster size removed'),
 ('Flagged pixels of 14 November 2023 were assigned', 'The class boundaries were set'), ('The calibrated rule was compared with a fixed-threshold', 'The area and land-cover composition of each scoring mask'),
 ('Area was the number of pixels multiplied', 'The analysis kept 4 areas apart'), ('The flagged area of 14 November 2023 was recomputed', 'The effect of the evaluation grid was checked'),
 ('The map covered 4780.81', 'Vegetation or rangeland occupied'), ('On 14 November and 26 November the flagged area formed', 'Within an analysed area of 3692.49'),
 ('Of 62829 building centroids', 'Within the analysed area, built-up pixels'), ('Of the 225.84 km² flagged on 14 November', 'Counting the dates on which a pixel was flagged'),
 ('Of the 225.84 km² flagged on 14 November', 'The strong class formed the core'), ('Against the Pléiades mapping of 12 November', 'In the town, the radar and UNOSAT flood extents'),
 ('The share of reference pixels that UNOSAT', 'The flooded share also rose'), ('On the calibration date, kappa rose', 'In the unfiltered flag'),
 ('Within the scoring masks, the filter removed', 'Over the full area, the filter removed'), ('The flagged areas obtained with the 3 references', 'In VV, the 21 October scene was brighter'),
 ('Rainfall averaged over the study rectangle', 'In the town, the main reference gave kappa'),
 ('The radar flood signal followed', 'The concentration of flagged area along the river'), ('The Earth Engine run with inputs reprojected to 10 m', 'To examine why the 2 October reference scenes'),
 ('Until such work is done', 'The main contribution of the study'),
]
def paras(doc): return [p for p in doc.element.body.iterchildren(W('p'))]
def text_of(p): return ''.join(t.text or '' for t in p.iter(W('t')))
def find(doc, key):
    hits = [p for p in doc.element.body.iterchildren(W('p')) if text_of(p).startswith(key)]
    assert len(hits) == 1, (key, len(hits)); return hits[0]
def split_para(doc, key, sent):
    p = find(doc, key); full = text_of(p); idx = full.find(sent); assert idx > 0, (key, sent)
    pos = 0
    for child in list(p):
        if child.tag not in (W('r'), W('hyperlink')): continue
        n = len(text_of(child))
        if pos <= idx < pos + n or (pos + n > idx and pos <= idx):
            assert child.tag == W('r'), ('split inside a hyperlink', sent)
            tnode = child.find(W('t')); t = tnode.text; cut = idx - pos
            left, right = t[:cut].rstrip(), t[cut:].lstrip()
            tnode.text = left; tnode.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            new_p = OxmlElement('w:p'); r2 = copy.deepcopy(child); r2.find(W('t')).text = right; r2.find(W('t')).set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            new_p.append(r2)
            nxt = child.getnext()
            while nxt is not None:
                after = nxt.getnext(); new_p.append(nxt); nxt = after
            p.addnext(new_p); return
        pos += n
    raise AssertionError(('split point not found', sent))
def merge_paras(doc, k1, k2):
    a, b = find(doc, k1), find(doc, k2)
    between = []; e = a.getnext()
    while e is not None and e is not b: between.append(e); e = e.getnext()
    assert e is b, ('not following', k1, k2)
    sp = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = ' '; t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve'); sp.append(t); a.append(sp)
    for child in list(b):
        if child.tag in (W('r'), W('hyperlink')): a.append(child)
    b.getparent().remove(b)
    anchor = a
    for el in between: anchor.addnext(el); anchor = el      # exhibits that sat between the two paragraphs follow the merged paragraph, in their original order
# ------------------------------------------------------------------ classification
def classify(doc):
    """Returns list of (element, kind) for body paragraphs. Kinds are title, h1, h2, tabletitle, figtitle, note, figure, abstract, body, empty."""
    out = []; first_text = True; in_abstract = False
    for p in doc.element.body.iterchildren(W('p')):
        txt = text_of(p).strip(); runs = [r for r in p.iter(W('r')) if ''.join(t.text or '' for t in r.iter(W('t'))).strip()]
        isbold = bool(runs) and all(r.find(W('rPr')) is not None and r.find(W('rPr')).find(W('b')) is not None for r in runs)
        if p.find('.//' + W('drawing')) is not None: out.append((p, 'figure')); continue
        if not txt: out.append((p, 'empty')); continue
        if first_text and txt not in SECTIONS: out.append((p, 'title')); first_text = False; continue
        first_text = False
        if txt in SECTIONS: in_abstract = (txt == 'Abstract'); out.append((p, 'h1')); continue
        if re.match(r'Table S?\d+\.', txt): out.append((p, 'tabletitle')); continue
        if re.match(r'Figure S?\d+\.', txt): out.append((p, 'figtitle')); continue
        if txt.startswith('Note.'): out.append((p, 'note')); continue
        if isbold and len(txt) < 90: out.append((p, 'h2')); continue
        out.append((p, 'abstract' if in_abstract else 'body'))
    return out
def length_report(doc, label):
    kinds = classify(doc); sec = sub = None; rows = []
    for p, k in kinds:
        t = text_of(p).strip()
        if k == 'h1': sec, sub = t, None
        elif k == 'h2': sub = t
        elif k == 'body' and sec in ('Introduction', 'Methods', 'Results', 'Discussion'): rows.append((sec, sub, lines_of(t), t))
    bad = [r for r in rows if not 7 <= r[2] <= 15]
    print('%s | body paragraphs %d | outside 7 to 15 lines: %d' % (label, len(rows), len(bad)))
    cur = None
    for sec, sub, n, t in rows:
        if (sec, sub) != cur and any(r[0] == sec and r[1] == sub and not 7 <= r[2] <= 15 for r in rows): print('  [%s] %s' % (sec, sub or '')); cur = (sec, sub)
        if not 7 <= n <= 15: print('     %2d lines | %s' % (n, t[:80]))
    return bad
# ------------------------------------------------------------------ styles
def set_font(style_or_rpr_owner, bold=None):
    rpr = style_or_rpr_owner.element.get_or_add_rPr()
    for ch in list(rpr):
        if ch.tag in (W('rFonts'), W('sz'), W('szCs'), W('color'), W('b'), W('bCs'), W('i'), W('iCs'), W('u')): rpr.remove(ch)
    rf = OxmlElement('w:rFonts')
    for a in ('ascii', 'hAnsi', 'eastAsia', 'cs'): rf.set(qn('w:' + a), 'Cambria')
    rpr.insert(0, rf)
    for tag in ('sz', 'szCs'): e = OxmlElement('w:' + tag); e.set(qn('w:val'), '24'); rpr.append(e)
    if bold is not None:
        for tag in ('b', 'bCs'):
            e = OxmlElement('w:' + tag); e.set(qn('w:val'), '1' if bold else '0'); rpr.insert(1, e)
def get_style(doc, name, base='Normal'):
    try: st = doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    if name != 'Normal': st.base_style = doc.styles[base]
    return st
def define_styles(doc):
    root = doc.styles.element
    for st in list(root.findall(W('style'))):                       # start from clean paragraph styles so that ids and names never clash
        if st.get(qn('w:type')) == 'paragraph' and st.get(qn('w:styleId')) in ('Normal', 'Heading1', 'Heading2', 'Title', 'TableTitle', 'FigureTitle', 'TableNote', 'Figure', 'TableText', 'Caption'): root.remove(st)
    n = OxmlElement('w:style'); n.set(qn('w:type'), 'paragraph'); n.set(qn('w:default'), '1'); n.set(qn('w:styleId'), 'Normal')
    nm = OxmlElement('w:name'); nm.set(qn('w:val'), 'Normal'); n.append(nm); n.append(OxmlElement('w:qFormat')); root.append(n)
    ds = doc.styles.element.find(W('docDefaults'))
    if ds is not None:
        rpr = ds.find(W('rPrDefault'));
        if rpr is not None:
            r = rpr.find(W('rPr'))
            for ch in list(r):
                if ch.tag in (W('rFonts'), W('sz'), W('szCs')): r.remove(ch)
            rf = OxmlElement('w:rFonts')
            for a in ('ascii', 'hAnsi', 'eastAsia', 'cs'): rf.set(qn('w:' + a), 'Cambria')
            r.insert(0, rf)
            for tag in ('sz', 'szCs'): e = OxmlElement('w:' + tag); e.set(qn('w:val'), '24'); r.append(e)
        pp = ds.find(W('pPrDefault'))
        if pp is not None: ds.remove(pp)
        pp = OxmlElement('w:pPrDefault'); ppr_ = OxmlElement('w:pPr'); sp_ = OxmlElement('w:spacing')
        sp_.set(qn('w:before'), '0'); sp_.set(qn('w:after'), '0'); sp_.set(qn('w:line'), '240'); sp_.set(qn('w:lineRule'), 'auto'); ppr_.append(sp_); pp.append(ppr_); ds.append(pp)
    normal = doc.styles['Normal']; set_font(normal)
    pf = normal.paragraph_format; pf.space_before = Pt(12); pf.space_after = Pt(0); pf.line_spacing = 1.0; pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; pf.widow_control = True
    spec = {'Title': (True, WD_ALIGN_PARAGRAPH.LEFT, 0, True), 'Heading 1': (True, WD_ALIGN_PARAGRAPH.LEFT, 12, True), 'Heading 2': (True, WD_ALIGN_PARAGRAPH.LEFT, 12, True),
            'Table Title': (False, WD_ALIGN_PARAGRAPH.LEFT, 12, True), 'Figure Title': (False, WD_ALIGN_PARAGRAPH.LEFT, 12, False),
            'Table Note': (False, WD_ALIGN_PARAGRAPH.JUSTIFY, 0, False), 'Figure': (False, WD_ALIGN_PARAGRAPH.CENTER, 12, True), 'Table Text': (False, WD_ALIGN_PARAGRAPH.LEFT, 0, False)}
    for name, (bold, al, before, kwn) in spec.items():
        st = get_style(doc, name); set_font(st, bold=bold)
        pf = st.paragraph_format; pf.alignment = al; pf.space_before = Pt(before); pf.space_after = Pt(0); pf.line_spacing = 1.0; pf.keep_with_next = kwn; pf.keep_together = True
        if name.startswith('Heading') or name == 'Title':
            ppr = st.element.get_or_add_pPr()
            for ch in ppr.findall(W('outlineLvl')): ppr.remove(ch)
            ol = OxmlElement('w:outlineLvl'); ol.set(qn('w:val'), {'Title': '9', 'Heading 1': '0', 'Heading 2': '1'}[name]); ppr.append(ol)
        if name in ('Title', 'Heading 1', 'Heading 2'): st.element.attrib.pop(qn('w:customStyle'), None); st.element.append(OxmlElement('w:qFormat'))
        else: st.element.set(qn('w:customStyle'), '1')
    # hyperlink character style, no font override
    for st in doc.styles.element.findall(W('style')):
        if st.get(qn('w:styleId')) == 'Hyperlink':
            r = st.find(W('rPr'))
            if r is not None:
                for ch in list(r):
                    if ch.tag in (W('rFonts'), W('sz'), W('szCs')): r.remove(ch)
def style_id(doc, name): return doc.styles[name].style_id
# ------------------------------------------------------------------ apply
def clean_runs(p, bold_label=None):
    for r in p.iter(W('r')):
        rpr = r.find(W('rPr'))
        if rpr is None: continue
        for ch in list(rpr):
            if ch.tag in (W('rFonts'), W('sz'), W('szCs'), W('b'), W('bCs'), W('i'), W('iCs'), W('color')): rpr.remove(ch)
        if len(rpr) == 0: r.remove(rpr)
def bold_run(r):
    rpr = r.find(W('rPr'))
    if rpr is None: rpr = OxmlElement('w:rPr'); r.insert(0, rpr)
    for tag in ('b', 'bCs'): rpr.append(OxmlElement('w:' + tag))
def set_pstyle(doc, p, name):
    ppr = p.find(W('pPr'))
    if ppr is not None: p.remove(ppr)
    ppr = OxmlElement('w:pPr'); ps = OxmlElement('w:pStyle'); ps.set(qn('w:val'), style_id(doc, name)); ppr.append(ps); p.insert(0, ppr)
def apply_styles(doc):
    define_styles(doc); kinds = classify(doc)
    for p, k in kinds:
        if k == 'empty': p.getparent().remove(p); continue
        label_run = None
        if k in ('tabletitle', 'figtitle'):
            rs = [r for r in p.iter(W('r'))];
            for r in rs:
                m = re.match(r'(Figure|Table) S?\d+\.', ''.join(t.text or '' for t in r.iter(W('t'))))
                if m: label_run = r; break
        abstract_runs = []
        if k == 'abstract':
            for r in p.iter(W('r')):
                if re.match(r'(Background|Methods|Results|Conclusion):', ''.join(t.text or '' for t in r.iter(W('t')))): abstract_runs.append(r)
        clean_runs(p)
        name = {'title': 'Title', 'h1': 'Heading 1', 'h2': 'Heading 2', 'tabletitle': 'Table Title', 'figtitle': 'Figure Title', 'note': 'Table Note', 'figure': 'Figure', 'abstract': 'Normal', 'body': 'Normal'}[k]
        set_pstyle(doc, p, name)
        if label_run is not None:
            bold_run(label_run)
            last = [t for t in p.iter(W('t'))][-1]
            if last.text and last.text.rstrip().endswith('.'): last.text = last.text.rstrip()[:-1]        # titles do not end with a full stop
        for r in abstract_runs: bold_run(r)
    # tables
    for tbl in doc.element.body.iterchildren(W('tbl')):
        tp = tbl.find(W('tblPr'))
        for tag in ('tblBorders', 'tblStyle', 'jc', 'tblInd', 'shd'):
            for e in tp.findall(W(tag)): tp.remove(e)
        jc = OxmlElement('w:jc'); jc.set(qn('w:val'), 'left'); ind = OxmlElement('w:tblInd'); ind.set(qn('w:w'), '0'); ind.set(qn('w:type'), 'dxa')
        bd = OxmlElement('w:tblBorders')
        for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'): e = OxmlElement('w:' + side); e.set(qn('w:val'), 'nil'); bd.append(e)
        for e in (jc, ind, bd):
            lay = tp.find(W('tblLayout')); (lay.addprevious(e) if lay is not None else tp.append(e))
        rows = tbl.findall(W('tr'))
        for ri, tr in enumerate(rows):
            trpr = tr.find(W('trPr'))
            if trpr is None: trpr = OxmlElement('w:trPr'); tr.insert(0, trpr)
            for e in trpr.findall(W('tblHeader')): trpr.remove(e)
            if trpr.find(W('cantSplit')) is None: trpr.append(OxmlElement('w:cantSplit'))
            for tc in tr.findall(W('tc')):
                tcpr = tc.find(W('tcPr'))
                for e in tcpr.findall(W('tcBorders')) + tcpr.findall(W('shd')): tcpr.remove(e)
                b = OxmlElement('w:tcBorders')
                def edge(side, sz): e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(sz)); e.set(qn('w:space'), '0'); e.set(qn('w:color'), '000000'); b.append(e)
                if ri == 0: edge('top', 8); edge('bottom', 4 if len(rows) > 1 else 8)
                if ri == len(rows) - 1 and ri != 0: edge('bottom', 8)
                if len(b): tcpr.append(b)
                for p in tc.findall(W('p')): clean_runs(p); set_pstyle(doc, p, 'Table Text')
    # drop empty spacer paragraphs that remained inside cells is not needed. Section properties stay untouched
def run(path, out):
    doc = docx.Document(path)
    main = 'MANUSCRIPT_full' in path
    if main:
        for key, sent in SPLITS: split_para(doc, key, sent)
        for a, b in MERGES: merge_paras(doc, a, b)
    if MEASURE:
        # temporary classification works on bold runs, so report before styles are applied
        return length_report(doc, path.split('\\')[-1]) if main else None
    apply_styles(doc); doc.save(out)
    return length_report(docx.Document(out), 'formatted ' + out.split('\\')[-1]) if main else None
if __name__ == '__main__':
    run(B + r'\MANUSCRIPT_full.docx', B + r'\MANUSCRIPT_full.docx')
    if not MEASURE: run(B + r'\MANUSCRIPT_Supplementary_tables.docx', B + r'\MANUSCRIPT_Supplementary_tables.docx')
