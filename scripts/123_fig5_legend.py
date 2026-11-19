import re,os,shutil
src=open(r'.\scripts\110_make_figures.py',encoding='utf-8').read().split('\n')
head='\n'.join(src[:52]); town='\n'.join(src[98:121])  # setup, town rasters, figure 5 block (before save)
town=town.replace("], 2, y=1.02)","], 1, y=1.02)")
assert "], 1, y=1.02)" in town
code=head+"\n"+town+"\nsave(fig,'fig12_agreement_map_town_v2')\n"
exec(compile(code,'fig5','exec'))

