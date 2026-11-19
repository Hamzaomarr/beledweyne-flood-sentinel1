"""Editorial pass on the paper-style Methods: remove repeated 'in the table below' phrasing, fix one tense slip, tighten the mechanical phase-by-phase overview."""
p = r'.\scripts\25_make_methods_paperstyle_docx.js'
t = open(p, encoding='utf-8-sig').read()
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80]); t = t.replace(a, b)
rep("The datasets, their identifiers and their roles are listed in the table below (Table 1). A pixel was the unit of analysis throughout.", "The datasets, their identifiers and their roles are summarised first (Table 1). A pixel was the unit of analysis throughout.")
rep("as set out in the table below (Table 2).", "as summarised here (Table 2).")
rep("The rule parameters and the masks described below are listed with their basis in the table below (Table 3).", "The rule parameters and the masks described below are given with their basis (Table 3).")
rep("and the configurations are listed in the table below (Table 4).", "and each configuration is defined (Table 4).")
rep("These eligible pixels are referred to as the analysed area,", "These eligible pixels were referred to as the analysed area,")
old_start = "K.push(body(['The analysis had five phases, and its datasets and processing steps are shown in the workflow diagram (Figure 1). In the first phase,"
a = t.index(old_start); b = t.index("Raster processing used Google Earth Engine ', D('10.1016/j.rse.2017.06.031')")
new = ("K.push(body(['The analysis had five phases, and its datasets and processing steps are shown in the workflow diagram (Figure 1). "
       "The first phase assembled Sentinel-2 and Sentinel-1 imagery, optical flood mapping from the United Nations Satellite Centre, hereafter UNOSAT, and ancillary layers. "
       "The second produced a land-cover map with a Random Forest classifier trained on labels where two existing products agreed. "
       "The third detected flooding from Sentinel-1 backscatter change with a threshold rule calibrated against the UNOSAT mapping of one date. "
       "The fourth removed small clusters, applied permanent-water and terrain masks and assigned intensity and persistence classes. "
       "The fifth tabulated flagged area by land-cover class, assessed accuracy on independent dates and tested how far the flagged area depended on analyst choices. ")
t = t[:a] + new + t[b:]
open(p, 'w', encoding='utf-8', newline='').write(t); print('style pass applied')
