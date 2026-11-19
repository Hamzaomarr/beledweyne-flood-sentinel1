"""Adds the window-size test (10 m inputs, filter windows of 9 and 11 pixels) to Table S13, the Results numbers, the Methods and the Discussion."""
import os
os.chdir(r'.\scripts')
def edit(path, pairs):
    t = open(path, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (path, a[:70], t.count(a)); t = t.replace(a, b)
    open(path, 'w', encoding='utf-8', newline='').write(t)
edit('82_restructure_exhibits.py', [
 ("rows.insert(j + 2, ['Local Python, inputs sampled at 20 m, 5 by 5 filter spanning 100 m, four sampling offsets', '45.672 to 45.789'])",
  "rows.insert(j + 2, ['Local Python, inputs sampled at 20 m, 5 by 5 filter spanning 100 m, four sampling offsets', '45.672 to 45.789'])\nrows.insert(j + 3, ['Local Python, 10 m inputs, 9 by 9 filter spanning 90 m', '45.579'])\nrows.insert(j + 4, ['Local Python, 10 m inputs, 11 by 11 filter spanning 110 m', '44.839'])"),
 ("across the four sampling offsets (Table S13).'", "across the four sampling offsets, and the 10 m rule gave 45.579 km² with a 9 by 9 pixel window and 44.839 km² with an 11 by 11 pixel window (Table S13).'"),
])
edit('14_make_methods_docx.js', [("with 4 sampling offsets, before the 5 by 5 pixel filter was applied.", "with 4 sampling offsets, before the 5 by 5 pixel filter was applied, and the local 10 m rule was also run with windows of 9 by 9 and 11 by 11 pixels.")])
OLD = "followed the 5 by 5 pixel median window, which spans 100 m and not 50 m on the coarser grid."
NEW = "followed the 5 by 5 pixel median window, which spans 100 m and not 50 m on the coarser grid, since the 10 m rule gave 45.6 km² with a 9 by 9 pixel window."
edit('..\\discussion_source.txt', [(OLD, NEW)]); edit('74_discussion_revision.py', [(OLD, NEW)])
print('ok')
