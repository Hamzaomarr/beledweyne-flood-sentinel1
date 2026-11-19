"""Figures are inserted at their native printed size (pixels at 300 DPI converted to 96 pixels per inch for the document), so that the text in them keeps the size it was drawn at."""
import re, os
S = r'.\scripts'
p = S + r'\82_restructure_exhibits.py'; t = open(p, encoding='utf-8').read()
a = "fh = lambda f: round(600 * Image.open(f).height / Image.open(f).width)"; assert t.count(a) == 1
t = t.replace(a, "fw = lambda f: round(Image.open(f).width / 300 * 96)\nfh = lambda f: round(Image.open(f).height / 300 * 96)")
t, n = re.subn(r"w=600, h=fh\((.*?)\), label", r"w=fw(\1), h=fh(\1), label", t); assert n == 4, n
a = "y['w'] = 600"; assert t.count(a) == 1; t = t.replace(a, "y['w'] = fw(y['file'])")
open(p, 'w', encoding='utf-8', newline='').write(t)
p = S + r'\14_make_methods_docx.js'; t = open(p, encoding='utf-8').read()
a = "const WFW = 600, WFH = Math.round(600 * WF.readUInt32BE(20) / WF.readUInt32BE(16));"; assert t.count(a) == 1
t = t.replace(a, "const WFW = Math.round(WF.readUInt32BE(16) / 300 * 96), WFH = Math.round(WF.readUInt32BE(20) / 300 * 96);")
open(p, 'w', encoding='utf-8', newline='').write(t); print('ok', n)

