"""Bring the wording fixes made in the paper-style version into the chosen (flat-subheading) Methods, and build matching author notes."""
D = r'.\scripts'
p = D + r'\14_make_methods_docx.js'; t = open(p, encoding='utf-8-sig').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80]); t = t.replace(a, b)
rep("The datasets and their roles are listed in the table below (Table 1).", "The datasets and their roles are summarised first (Table 1).")
rep("are listed with their basis in the table below (Table 2).", "are given with their basis (Table 2).")
rep("and the configurations are listed in the table below (Table 3).", "and each configuration is defined (Table 3).")
rep("These eligible pixels are referred to as the analysed area", "These eligible pixels were referred to as the analysed area")
rep("with water to water, trees, grass and shrub and scrub to vegetation or rangeland, crops to cropland, built area to built-up, and bare ground to bare soil or sand.",
    "with the water class to water, the trees, grass, and shrub and scrub classes to vegetation or rangeland, the crops class to cropland, the built class to built-up, and the bare class to bare soil or sand.")
open(p, 'w', encoding='utf-8', newline='').write(t); print('methods wording fixed')

# author notes for this version (subheading names, no numbering)
s = open(D + r'\28_make_author_notes_docx.js', encoding='utf-8-sig').read()
a = s.index("K.push(body('This file is for the authors"); b = s.index("K.push(H2('Placeholders inserted'));")
intro = "K.push(body('This file is for the authors and is not part of the manuscript. It lists what must still be supplied and what could not be settled. It refers to the subheadings of MANUSCRIPT_Methods.docx.'));\n"
ph = ("K.push(H2('Placeholders inserted'));\nK.push(body('Institution where the study was conducted, under study design and setting. Rationale for capping land-cover points at 500 per class, under sample size. "
      "Location of the archived scripts and output tables, under software and reproducibility. Ethics approval status, under ethical considerations. Basis for the 75% surface water occurrence threshold, in Table 2.'));\n")
un = ("K.push(H2('Unresolved issues'));\nK.push(body('The attribute dates of two UNOSAT layers contradict their file names, the Pléiades flood layer carrying 21 July 2023 and the WorldView-2 layer of 30 November carrying 23 November 2023, and the file names were used. "
      "The Pléiades layer file names give Shabelle Region whereas the Gaofen-2 and WorldView-2 file names give Hiraan Region, and Hiraan region was used as supplied. "
      "The HAND limit, slope limit and intensity class boundaries were derived from the calibration data, so their values are given as the parameters used, and the author should confirm that this belongs in the Methods and not in the Results. "
      "The dark-surface cut-off and the minimum cluster size were added after earlier scoring of the later dates, and this order is stated in the section on Sentinel-1 flood detection. "
      "A first implementation of the cluster filter inside Earth Engine gave totals that depended on how the request was tiled and was replaced by the local implementation, and the author should decide whether this belongs in the Results or a supplement. "
      "No peer-reviewed article with a DOI was identified for ESA WorldCover, the Copernicus DEM or the UNOSAT product, so these were described by name and version without citation. "
      "The setting of the study area and of the 2023 flood is not described in this version and would need verified sources from the literature check if the authors want it added.'));\n")
notes = s[:a] + intro + ph + un + s[s.index('const doc = new Document'):]
open(D + r'\31b_make_author_notes_original.js', 'w', encoding='utf-8', newline='').write(notes.replace("'METHODS_author_notes.docx'", "'METHODS_author_notes.docx'"))
print('notes script written')
