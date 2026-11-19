"""Helpers for colour-coded in-place edits of a .docx body (python-docx plus lxml). Runs are split at exact text offsets, new text is inserted as coloured runs,
and DOI citations are inserted as working hyperlinks in the source colour."""
import copy, re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
COL = {'R1': '00803C', 'R2': 'E36C0A'}
LOG = []
def q(t): return qn('w:' + t)
def ptext(p):
    return ''.join(x.text or '' for x in p.iter(q('t')))
def items(p):
    out = []
    for ch in p:
        if ch.tag == q('r'):
            t = ''.join(x.text or '' for x in ch.findall(q('t')))
            plain = all(c.tag in (q('rPr'), q('t'), q('lastRenderedPageBreak')) for c in ch)
            out.append((ch, t, plain))
        elif ch.tag == q('hyperlink'):
            out.append((ch, ''.join(x.text or '' for x in ch.iter(q('t'))), False))
    return out
def flat(p): return ''.join(t for _, t, _ in items(p))
def set_t(r, text):
    ts = r.findall(q('t'))
    for t in ts[1:]: r.remove(t)
    if ts: t = ts[0]
    else:
        t = OxmlElement('w:t'); r.append(t)
    t.text = text; t.set(XML_SPACE, 'preserve')
def boundary(p, off):
    pos = 0
    for el, t, plain in items(p):
        end = pos + len(t)
        if pos < off < end:
            if not plain: raise ValueError('boundary inside hyperlink or complex run at %d' % off)
            r2 = copy.deepcopy(el); k = off - pos
            set_t(r2, t[k:]); set_t(el, t[:k]); el.addnext(r2); return
        pos = end
def find_unique(p, old):
    s = flat(p); i = s.find(old)
    if i < 0: raise ValueError('not found: %r in %r' % (old[:60], s[:80]))
    if s.find(old, i + 1) >= 0: raise ValueError('not unique: %r' % old[:60])
    return i
def mk_rpr(base, color, hyper=False):
    rpr = OxmlElement('w:rPr')
    if base is not None:
        for ch in base:
            if ch.tag in (q('color'), q('rStyle'), q('u'), q('b'), q('bCs'), q('i'), q('iCs'), q('highlight'), q('shd')): continue
            rpr.append(copy.deepcopy(ch))
    if hyper:
        rs = OxmlElement('w:rStyle'); rs.set(qn('w:val'), 'Hyperlink'); rpr.insert(0, rs)
    if color:
        c = OxmlElement('w:color'); c.set(qn('w:val'), color); rpr.append(c)
    if hyper:
        u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rpr.append(u)
    return rpr
def mk_run(text, base, color):
    r = OxmlElement('w:r'); rpr = mk_rpr(base, color)
    if len(rpr): r.append(rpr)
    t = OxmlElement('w:t'); t.text = text; t.set(XML_SPACE, 'preserve'); r.append(t); return r
def mk_link(part, doi, base, color):
    rid = part.relate_to('https://doi.org/' + doi, RT.HYPERLINK, is_external=True)
    h = OxmlElement('w:hyperlink'); h.set(qn('r:id'), rid); h.set(qn('w:history'), '1')
    r = OxmlElement('w:r'); r.append(mk_rpr(base, color, True)); t = OxmlElement('w:t'); t.text = doi; t.set(XML_SPACE, 'preserve'); r.append(t); h.append(r); return h
def build(part, segs, base, color):
    out = []
    for s in segs:
        if isinstance(s, tuple) and s[0] == 'doi': out.append(mk_link(part, s[1], base, color))
        else: out.append(mk_run(s, base, color))
    return out
def base_rpr(p, off):
    pos = 0; last = None
    for el, t, plain in items(p):
        if el.tag == q('r'):
            last = el
            if pos <= off <= pos + len(t) and t: break
        pos += len(t)
    return None if last is None else last.find(q('rPr'))
def seg_text(segs): return ''.join(s if isinstance(s, str) else s[1] for s in segs)
def replace(part, p, old, segs, src, cid, loc, kind='replace'):
    i = find_unique(p, old); boundary(p, i); boundary(p, i + len(old))
    base = copy.deepcopy(base_rpr(p, i)) if base_rpr(p, i) is not None else None
    pos = 0; first = None; rm = []
    for el, t, plain in items(p):
        end = pos + len(t)
        if t and pos >= i and end <= i + len(old): rm.append(el)
        pos = end
    if not rm: raise ValueError('nothing to remove for %r' % old[:40])
    new = build(part, segs, base, COL[src]); anchor = rm[0]
    for e in new: anchor.addprevious(e)
    for el in rm: p.remove(el)
    for pe in p.findall(q('proofErr')): p.remove(pe)
    LOG.append(dict(src=src, comment=cid, location=loc, kind=kind, old=old, new=seg_text(segs)))
def insert_after(part, p, anchor_text, segs, src, cid, loc, anchor_end=True):
    i = find_unique(p, anchor_text) + (len(anchor_text) if anchor_end else 0); boundary(p, i)
    pos = 0; target = None
    for el, t, plain in items(p):
        end = pos + len(t)
        if end <= i and (end > 0 or True): target = el
        if end >= i and (t or end > i): 
            if end == i: target = el
            break
        pos = end
    base = copy.deepcopy(base_rpr(p, i)) if base_rpr(p, i) is not None else None
    new = build(part, segs, base, COL[src]); 
    if i == 0:
        first = items(p)[0][0]
        for e in new: first.addprevious(e)
    else:
        # locate the element ending exactly at i
        pos = 0; tgt = None
        for el, t, plain in items(p):
            pos += len(t)
            if pos == i and t: tgt = el; break
        for e in reversed(new): tgt.addnext(e)
    LOG.append(dict(src=src, comment=cid, location=loc, kind='insert', old='', new=seg_text(segs)))
def append(part, p, segs, src, cid, loc):
    its = items(p); last = [e for e, t, pl in its if t][-1]
    base = copy.deepcopy(last.find(q('rPr'))) if last.tag == q('r') and last.find(q('rPr')) is not None else None
    new = build(part, segs, base, COL[src]); anchor = last
    for e in reversed(new): anchor.addnext(e)
    LOG.append(dict(src=src, comment=cid, location=loc, kind='append', old='', new=seg_text(segs)))
def new_par_after(part, ref, template, segs, src, cid, loc):
    p = copy.deepcopy(template)
    for ch in list(p):
        if ch.tag != q('pPr'): p.remove(ch)
    for k in list(p.attrib): del p.attrib[k]
    for e in build(part, segs, None, COL[src]): p.append(e)
    ref.addnext(p)
    LOG.append(dict(src=src, comment=cid, location=loc, kind='new paragraph', old='', new=seg_text(segs)))
    return p
def set_cell(part, cell_el, paras, src, cid, loc):
    """cell_el is a w:tc. paras is a list of seg lists, one per paragraph. Existing paragraph properties are kept."""
    ps = cell_el.findall(q('p')); tmpl = ps[0]
    base = None
    r0 = tmpl.find(q('r'))
    if r0 is not None and r0.find(q('rPr')) is not None: base = copy.deepcopy(r0.find(q('rPr')))
    old = ' / '.join(ptext(p) for p in ps)
    for p in ps[1:]: cell_el.remove(p)
    for ch in list(tmpl):
        if ch.tag != q('pPr'): tmpl.remove(ch)
    prev = tmpl
    for k, segs in enumerate(paras):
        if k == 0: p = tmpl
        else:
            p = copy.deepcopy(tmpl)
            for ch in list(p):
                if ch.tag != q('pPr'): p.remove(ch)
            for a in list(p.attrib): del p.attrib[a]
            prev.addnext(p)
        for e in build(part, segs, base, COL[src]): p.append(e)
        prev = p
    LOG.append(dict(src=src, comment=cid, location=loc, kind='table cell', old=old, new=' / '.join(seg_text(s) for s in paras)))
