"""Two-pass edit, part 2. Results and supplementary blocks. Run after scripts 82 and 91. Replacements are applied to every text field (paragraphs, headings, captions, notes, table headers and cells)
and each one must match at least once."""
import json, os
B = r'.'; O = os.path.join(B, 'outputs')
R = [
 ('Land-cover map and agreement with reference labels', 'Land-cover map and agreement with consensus labels'),
 ('Land-cover map area and agreement with reference labels', 'Land-cover map area and agreement with consensus labels'),
 ('Overall agreement with the 373 hold-out reference points', 'Overall agreement with the 373 hold-out points'),
 ('One of these was mapped as built-up and 3 as vegetation or rangeland', 'Of these, 1 was mapped as built-up and 3 as vegetation or rangeland'),
 (' All of these values measure agreement with labels on which WorldCover and Dynamic World agreed and not accuracy against field observation.', ''),
 ('The analysis extents of the United Nations Satellite Centre, UNOSAT, covered a small part of the western half.', 'The UNOSAT analysis extents covered a small part of the western half.'),
 ('Flagged flood extent on four dates', 'Flagged flood extent on 4 dates'),
 ('in the weak class of change in vertical transmit and vertical receive backscatter, ΔVV, 36.59', 'in the weak class of ΔVV, 36.59'),
 ('was flagged on one date, 101.48 km² on two dates and 134.60 km² on all three (Table S4)', 'was flagged on 1 date, 101.48 km² on 2 dates and 134.60 km² on all 3 dates (Table S4)'),
 ('was flagged on all three dates, whereas', 'was flagged on all 3 dates, whereas'),
 ('Pixels flagged on all three dates were concentrated', 'Pixels flagged on all 3 dates were concentrated'), ('pixels flagged on one or two dates predominated', 'pixels flagged on 1 or 2 dates predominated'),
 ('for the first two rules', 'for the first 2 rules'),
 ('Precision and recall of the final rule by ESA WorldCover class', 'Precision and recall of the final rule by WorldCover class'), ('Agreement varied by ESA WorldCover class', 'Agreement varied by WorldCover class'),
 ('Together the three products covered', 'Together the 3 products covered'),
 ('for pixels flagged on one, two and three dates', 'for pixels flagged on 1, 2 and 3 dates'), ('for zero, one, two and three dates', 'for 0, 1, 2 and 3 dates'),
 ('obtained with the three references were nested', 'obtained with the 3 references were nested'), ('the mean of all three scenes gave', 'the mean of all 3 scenes gave'),
 ('across the four sampling offsets', 'across the 4 sampling offsets'), ('on the two independent dates outside', 'on the 2 independent dates outside'),
 ('One date, km²', '1 date, km²'), ('Two dates, km²', '2 dates, km²'), ('Three dates, km²', '3 dates, km²'),
 ('Union of all three products', 'Union of all 3 products'), ('four sampling offsets', '4 sampling offsets'),
 ('Flagged pixels in two rangeland boxes without the cluster filter', 'Flagged pixels in 2 rangeland boxes without the cluster filter'), ('Three by three filter', '3 by 3 filter'),
 ('Note. Values are flagged area on 14 November 2023. HAND, height above nearest drainage. VV, vertical transmit and vertical receive polarisation. VH, vertical transmit and horizontal receive polarisation. ΔVV, post-event minus pre-event VV backscatter in dB.', 'Note. Values are flagged area on 14 November 2023.'),
 (' that was not permanent water. HAND, height above nearest drainage.', ' that was not permanent water.'),
 ('a decrease of 2.0 dB in vertical transmit and vertical receive backscatter or 1.5 dB in vertical transmit and horizontal receive backscatter', 'a decrease of 2.0 dB in VV backscatter or 1.5 dB in VH backscatter'),
 ('where two existing land-cover products gave the same class', 'where 2 existing land-cover products gave the same class'),
 ('Rows are reference labels and columns are mapped classes', 'Rows are consensus labels and columns are mapped classes'),
 ('Hold-out refers to spatial block 0', 'Hold-out refers to spatial block 0'),
]
def walk(o, f):
    if isinstance(o, str): return f(o)
    if isinstance(o, list): return [walk(v, f) for v in o]
    if isinstance(o, dict): return {k: (walk(v, f) if k in ('x', 'title', 'note', 'header', 'rows', 'label') else v) for k, v in o.items()}
    return o
hits = {a: 0 for a, _ in R}
def sub(s):
    for a, b in R:
        if a in s: hits[a] += s.count(a); s = s.replace(a, b)
    return s
for name in ('results_blocks_main.json', 'supplement_blocks.json'):
    p = os.path.join(O, name); blocks = json.load(open(p, encoding='utf-8')); blocks = [walk(b, sub) for b in blocks]
    if name.startswith('supplement'):
        blocks[0]['x'] += ' Abbreviations are defined in the main text.'
    json.dump(blocks, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
missing = [a for a, n in hits.items() if n == 0 and a != 'Hold-out refers to spatial block 0']
print('replacements with no match:', missing)
