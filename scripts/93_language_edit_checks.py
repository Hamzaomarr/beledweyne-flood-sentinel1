"""Checks after the language edit. DOI markers are compared with the pre-edit sources, numbers with the pre-edit text, punctuation with the style rules, and a few pattern counts are printed."""
import re, collections, docx
B = r'.'; OLD = B + r'\backup_before_language_edit'
def dois(path): return collections.Counter(re.findall(r'10\.\d{4,9}/[^\s;>,)]+', open(path, encoding='utf-8').read()))
for f in ('introduction_source.txt', 'discussion_source.txt'):
    a, b = dois(OLD + '\\' + f), dois(B + '\\' + f); print(f, 'DOI markers before', sum(a.values()), 'after', sum(b.values()), '| same multiset:', a == b, '| differences:', dict((a - b) + (b - a)) if a != b else {})
# DOI sets per paragraph
for f in ('introduction_source.txt', 'discussion_source.txt'):
    pa = [set(re.findall(r'10\.\d{4,9}/[^\s;>,)]+', x)) for x in open(OLD + '\\' + f, encoding='utf-8').read().strip().split('\n\n')]
    pb = [set(re.findall(r'10\.\d{4,9}/[^\s;>,)]+', x)) for x in open(B + '\\' + f, encoding='utf-8').read().strip().split('\n\n')]
    print(f, 'paragraphs', len(pa), '->', len(pb))
# numbers: every number in the old manuscript prose still appears, and no new number appears
def prose(f):
    d = docx.Document(f); txt = '\n'.join(p.text for p in d.paragraphs); txt = re.sub(r'10\.\d{4,9}/\S+', ' ', txt); txt = re.sub(r'(Table|Figure) S?\d+[ab]?', ' ', txt); return txt
num = lambda s: collections.Counter(re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?', s))
ao, bo = num(prose(OLD + r'\MANUSCRIPT_full.docx')), num(prose(B + r'\MANUSCRIPT_full.docx'))
print('numbers only in the new text:', sorted(set(bo) - set(ao))[:30]); print('numbers no longer in the text:', sorted(set(ao) - set(bo))[:60])
# style
d = docx.Document(B + r'\MANUSCRIPT_full.docx'); bad = []
for p in d.paragraphs:
    c = re.sub(r'10\.\d{4,9}/\S+', 'DOI', p.text); c = re.sub(r'\((?:Figure|Table)s? S?\d+[ab]?(?: and (?:Figure|Table) S?\d+[ab]?)?\)', '', c)
    for ch in ';\u2014\u2013()':
        if ch in c: bad.append((ch, c[max(0, c.index(ch) - 30):c.index(ch) + 25]))
    if ':' in c and not re.match(r'(Background|Methods|Results|Conclusion|Keywords):', c) and 'Sentinel-1: Optical' not in c: bad.append((':', c[max(0, c.index(':') - 30):c.index(':') + 25]))
print('style hits:', bad)
txt = '\n'.join(p.text for p in d.paragraphs)
for pat in ('it is important', 'worth ', 'underscor', 'highlight', 'crucial', 'growing body', 'landscape', 'notably', 'moreover', 'furthermore', 'in addition', 'overall,', 'importantly', 'delve', 'robust', 'comprehensive', 'plays a'):
    n = len(re.findall(pat, txt, flags=re.I));
    if n: print('  pattern', repr(pat), n)
sents = [len(s.split()) for s in re.split(r'(?<=[.])\s+', re.sub(r'10\.\d{4,9}/\S+', 'DOI', txt)) if len(s.split()) > 3]
import statistics as st; print('sentences', len(sents), 'mean words', round(st.mean(sents), 1), 'sd', round(st.pstdev(sents), 1), 'max', max(sents), '>45 words:', sum(s > 45 for s in sents))
