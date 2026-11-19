"""Timing diagnostic: score the same footprint (inside the calibration extent) on the 3 optical dates, and compare flooded reference area between dates."""
import numpy as np, rasterio, geopandas as gpd, glob, os, json, pandas as pd
exec(open(r'.\scripts\121_reviewer_local_analyses.py',encoding='utf-8-sig').read().split("# ---------------------------------------------------------------- positive backscatter")[0].split("rng = np.random.default_rng")[0])
rows=[]
inter=PA&GA&WA&vall&~PC
for nm,f,truth in [('Pleiades 12 Nov vs radar 14 Nov',f14,PF),('Gaofen-2 23 Nov vs radar 26 Nov',f26,GF),('WorldView-2 30 Nov vs radar 26 Nov',f26,WF)]:
    m=inter&(PF|~PW) if 'Pleiades' in nm else inter
    tp=(f&truth&m).sum(); fp=(f&~truth&m).sum(); fn=(~f&truth&m).sum(); tn=(~f&~truth&m).sum()
    pr,rc,ba,kp=metr(tp,fp,fn,tn); rows.append(dict(pair=nm,mask_km2=m.sum()*1e-4,reference_flooded_km2=(truth&m).sum()*1e-4,flagged_km2=(f&m).sum()*1e-4,precision=pr,recall=rc,kappa=kp))
t=pd.DataFrame(rows); t.to_csv(os.path.join(OUT,'revision2_same_footprint_dates.csv'),index=False); print(t.round(3).to_string(index=False))
# flooded reference change between optical dates over the footprint shared by all 3 extents
for a,b,na,nb in [(PF,GF,'PHR','GF2'),(GF,WF,'GF2','WV2'),(PF,WF,'PHR','WV2')]:
    print(na,'->',nb,'flooded km2',(a&inter).sum()*1e-4,(b&inter).sum()*1e-4,'| flooded in first only',(a&~b&inter).sum()*1e-4,'| second only',(~a&b&inter).sum()*1e-4,'| both',(a&b&inter).sum()*1e-4)
print('shared footprint km2',inter.sum()*1e-4)

