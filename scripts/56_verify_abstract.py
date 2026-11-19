"""Line-by-line check of every number and date in abstract_source.txt against the manuscript (tables included), plus the formatting rules."""
import re, docx
B = r'.'
L = open(B + r'\abstract_source.txt', encoding='utf-8').read().strip().split('\n')
body = [l.split('|', 1)[1] for l in L if '|' in l]; txt = ' '.join(body)
d = docx.Document(B + r'\MANUSCRIPT_full.docx'); full = '\n'.join(p.text for p in d.paragraphs) + '\n' + '\n'.join(c.text for t in d.tables for r in t.rows for c in r.cells)
txt2 = re.sub(r'\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December)\b', ' ', txt)
nums = re.findall(r'\d+(?:\.\d+)?', txt2.replace('Sentinel-1', 'Sentinel').replace('Gaofen-2', 'Gaofen'))
print('numbers in abstract:', nums)
miss = [n for n in nums if n not in full]; print('numbers not found anywhere in the manuscript:', miss)
for x in re.findall(r'\b\d{1,2} (?:October|November|December)\b', txt): print('date', x, 'present in manuscript:', x in full)
print('2023 present:', '2023' in full)
# where each key number lives
chk = {'4780.81 study area': ('Table 4 all classes', '4780.81'), '225.84 flagged 14 Nov': ('Table 5', '225.84'), '275.09 flagged 26 Nov': ('Table 5', '275.09'), '92.15 cropland': ('Table 5', '92.15'),
       '40.37 built-up share': ('Table 6', '40.37'), '1.07 rangeland share': ('Table 6', '1.07'), '185.1 and 573.8 pre-event scenes': ('Table 13', '185.1'), '396.4 without cluster filter': ('Table 13', '396.4'), '225.8 with it': ('Table 13', '225.8')}
for k, (src, v) in chk.items(): print(k, '->', src, v in full)
T = [[c.text for c in r.cells] for r in d.tables[ [i for i, t in enumerate(d.tables) if t.rows[0].cells[0].text == 'Rule'][0] ].rows]
g = [r for r in T if 'Gaofen-2 23 November, outside' in r[1]]; print('Table 8 Gaofen-2 outside rows (rule, precision, recall, balanced accuracy, kappa):', [(r[0], r[2], r[3], r[4], r[5]) for r in g])
print('parentheses:', '(' in txt, '| en/em dashes:', any(c in txt for c in ['\u2013', '\u2014']), '| semicolons:', ';' in txt, '| colons in body:', ':' in txt, '| abbreviations:', sorted(set(re.findall(r'\b[A-Z]{2,}\b', txt))), '| words:', len(txt.split()), 'plus 4 labels')
