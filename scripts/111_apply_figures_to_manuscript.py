"""Points the manuscript build at the new figure files in outputs/figures/png, sizes every figure to the printed text width, switches panel letters to capitals and rewrites the captions of figures whose titles and notes were removed from the images.
Patches scripts 82, 14 and 110."""
import re, os
S = r'.\scripts'
def patch(path, pairs, regex=()):
    t = open(path, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (os.path.basename(path), a[:70], t.count(a)); t = t.replace(a, b)
    for pat, rep in regex:
        t, n = re.subn(pat, rep, t, flags=re.S); assert n == 1, (pat[:50], n)
    open(path, 'w', encoding='utf-8', newline='').write(t)
CAP = {
 'Figure 2.': "Land-cover map of the study area and UNOSAT analysis extents. Coordinates are in kilometres in the Universal Transverse Mercator zone 38N projection. The solid outline is the Pléiades extent and the dashed outline is the extent shared by the Gaofen-2 and WorldView-2 mapping",
 'Figure 3.': "Flagged flood extent on 14 November and 26 November 2023. A. Flagged area on 14 November. B. Flagged area on 26 November",
 'Figure 7.': "Backscatter difference between the 2 October scenes and area flagged only with the 21 October reference. A. Mean change in VV backscatter from 9 October to 21 October on a 100 m grid. B. Share of each 100 m cell flagged on 14 November only with the 21 October reference, with the outline of the main footprint",
}
patch(S + r'\82_restructure_exhibits.py', [
 ("FMAP = {'2': '2', '3': '3', '4': '4a', '5': '4b', '6': '5', '7': '7'}", "FMAP = {'2': '2', '3': '3', '4': '4A', '5': '4B', '6': '5', '7': '7'}"),
 ("        else: y = copy.deepcopy(x); y['label'] = 'Figure %s.' % FMAP[k]; main_out.append(y)",
  "        else:\n            y = copy.deepcopy(x); y['label'] = 'Figure %s.' % FMAP[k]; y['file'] = os.path.join(fd, os.path.basename(x['file'])); y['w'] = 600; y['h'] = fh(y['file']); y['title'] = NEWCAP.get(y['label'], y['title']); main_out.append(y)"),
 ("w=600, h=268, label='Figure 6.', title='Agreement of the radar flag with UNOSAT flood extents on the calibration date and on the two independent dates outside the calibration extent, for the final rule, the calibrated rule without the cluster filter and the fixed thresholds'",
  "w=600, h=fh(os.path.join(fd, 'fig4_validation_vs_unosat.png')), label='Figure 6.', title='Agreement of the radar flag with UNOSAT flood extents on the calibration date and on the 2 independent dates outside the calibration extent, for the final rule, the calibrated rule without the cluster filter and the fixed thresholds. A. Precision. B. Recall. C. Balanced accuracy. D. Cohen\\'s kappa. The radar dates differ from the optical mapping dates by 2 to 4 days'"),
 ("file=fig45, w=440, h=h45, label='Figure 4.', title='Intensity of backscatter change on 14 November 2023, panel a, and persistence of the flag from 14 November to 8 December 2023, panel b'",
  "file=fig45, w=600, h=fh(fig45), label='Figure 4.', title='Intensity of backscatter change and persistence of the flag. A. Intensity of backscatter change on 14 November 2023. B. Persistence of the flag from 14 November to 8 December 2023'"),
 ("w=600, h=265, label='Figure S1.', title='Share of reference pixels mapped as flooded by UNOSAT by size of the backscatter drop, panel a, and by number of dates on which the pixel was flagged, panel b'",
  "w=600, h=fh(os.path.join(fd, 'fig5_severity_justification.png')), label='Figure S1.', title='Share of reference pixels mapped as flooded by UNOSAT by backscatter change and persistence. A. Flooded share by size of the backscatter change in VV. B. Flooded share by number of dates on which the pixel was flagged. The shares support ordinal classes only, and no water depth was measured or inferred'"),
 ("w=600, h=233, label='Figure S2.', title='Sentinel-1 VV backscatter before and after the flood and its change over Beledweyne, with the UNOSAT Pléiades flood extent of 12 November in orange'",
  "w=600, h=fh(os.path.join(fd, 'fig11_sentinel1_before_after_town.png')), label='Figure S2.', title='Sentinel-1 VV backscatter before and after the flood and its change over Beledweyne. A. VV before the flood, as the mean of 9 and 21 October. B. VV on 14 November. C. Change in VV between the 2 periods. The outline shows the UNOSAT Pléiades flood extent of 12 November'"),
], regex=[(r"# ---------- combined figure 4.*?h45 = round\(440 \* canvas\.height / canvas\.width\)",
           "# ---------- figures are drawn by script 110 at the printed width and stored in outputs/figures/png\nfd = os.path.join(O, 'figures', 'png'); fig45 = os.path.join(fd, 'fig_intensity_persistence_combined.png')\nfh = lambda f: round(600 * Image.open(f).height / Image.open(f).width)\nNEWCAP = " + repr(CAP))])
t = open(S + r'\14_make_methods_docx.js', encoding='utf-8').read()
a = t.index("K.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, keepNext: true,\n  children: [new ImageRun({ type: 'png', data: fs.readFileSync(path.join(BASE, 'outputs', 'figures', 'fig_methods_workflow.png'))")
b = t.index('\n', t.index('name: \'Workflow\'', a))
new = ("const WF = fs.readFileSync(path.join(BASE, 'outputs', 'figures', 'png', 'fig_methods_workflow.png')); const WFW = 600, WFH = Math.round(600 * WF.readUInt32BE(20) / WF.readUInt32BE(16));\n"
       "K.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, keepNext: true,\n  children: [new ImageRun({ type: 'png', data: WF, transformation: { width: WFW, height: WFH }, altText: { title: 'Workflow', description: 'Analysis workflow from input datasets to flagged area by land-cover class', name: 'Workflow' } })] }));")
t = t[:a] + new + t[b:]; open(S + r'\14_make_methods_docx.js', 'w', encoding='utf-8', newline='').write(t)
patch(S + r'\110_make_figures.py', [("colors=[ORANGE if cm_ == 'RdBu' else VERM]", "colors=[VERM]")])
print('patched')
