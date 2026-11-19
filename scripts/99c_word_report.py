import sys, collections, os
path = sys.argv[1]
rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8') if l.strip()]
rows = [r for r in rows if len(r) >= 12]
print('paragraphs', len(rows))
sty = collections.Counter(r[1] for r in rows); print('styles', dict(sty))
non = [r for r in rows if r[3] != '0' or r[2] == 'True']
print('font/size combos', collections.Counter((r[4], r[5]) for r in non))
print('line spacing rule (0=single)', collections.Counter(r[8] for r in non))
print('before/after by style:');
for s in sty:
    sub = [r for r in rows if r[1] == s]; print('  ', s, collections.Counter((r[6], r[7]) for r in sub).most_common(3), 'align', collections.Counter(r[9] for r in sub).most_common(2), 'bold', collections.Counter(r[10] for r in sub).most_common(2))
empty = [r for r in rows if r[3] == '0' and r[2] != 'True']; print('empty non-table paragraphs', len(empty), [r[1] for r in empty][:10])
# body paragraph line lengths by section
sec = sub = None; bad = []; allbody = []
for r in rows:
    s = r[1]
    if s == 'Heading 1': sec, sub = r[11], None
    elif s == 'Heading 2': sub = r[11]
    elif s == 'Normal' and r[2] != 'True' and sec in ('Introduction', 'Methods', 'Results', 'Discussion'):
        n = int(r[3]); allbody.append((sec, n));
        if not 7 <= n <= 15: bad.append((sec, sub, n, r[11]))
print('body paragraphs in Introduction/Methods/Results/Discussion', len(allbody), '| outside 7 to 15 lines', len(bad))
for b in bad: print('  ', b)
print('line distribution', sorted(collections.Counter(n for s, n in allbody).items()))
print([r for r in rows if r[0] == 'PAGES'])
