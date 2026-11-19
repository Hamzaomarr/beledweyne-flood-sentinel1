"""Layout fixes found on inspection of the first export of script 110. The legend is anchored to the drawn panel positions, and the pre-event figure shares its northing axis."""
p = r'.\scripts\110_make_figures.py'; s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a)); s = s.replace(a, b)
rep('def rd(p):', '''def above_axes(fig, axs, handles, ncol, pad_in=0.3):
    # legend centred above a group of equal-aspect panels, placed from their drawn positions so that the gap to the panels stays small
    fig.canvas.draw()
    for a in axs: a.apply_aspect()
    pos = [a.get_position() for a in axs]; yt = max(q.y1 for q in pos); xc = (min(q.x0 for q in pos) + max(q.x1 for q in pos)) / 2
    return fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(xc, yt + pad_in / fig.get_figheight()), ncol=ncol, frameon=False, columnspacing=1.2, handlelength=1.5, handletextpad=0.5)
def rd(p):''')
rep("""above(fig, [Patch(color=VERM, label='Flagged, radar backscatter drop'), Patch(color=BLUE, label='Permanent water'), Patch(facecolor='#f2f2f2', edgecolor='#999999', label='Analysed, not flagged'),
            Patch(color='#c9c9c9', label='Excluded, HAND above 10 m or slope above 8°')], 2, y=0.88)""", """above_axes(fig, axs, [Patch(color=VERM, label='Flagged, radar backscatter drop'), Patch(color=BLUE, label='Permanent water'), Patch(facecolor='#f2f2f2', edgecolor='#999999', label='Analysed, not flagged'),
            Patch(color='#c9c9c9', label='Excluded, HAND above 10 m or slope above 8°')], 2)""")
rep("fig, axs = plt.subplots(1, 3, figsize=(W, 2.9), sharey=True); fig.subplots_adjust(top=0.82, wspace=0.3)", "fig, axs = plt.subplots(1, 3, figsize=(W, 2.9), sharey=True); fig.subplots_adjust(top=0.85, wspace=0.5)")
rep("above(fig, [Line2D([0], [0], color=VERM, lw=1.0, label='UNOSAT Pléiades 12 November flood extent')], 1, y=0.9)", "above_axes(fig, axs, [Line2D([0], [0], color=VERM, lw=1.0, label='UNOSAT Pléiades 12 November flood extent')], 1)")
rep("fig, axs = plt.subplots(1, 2, figsize=(W, 3.5)); fig.subplots_adjust(wspace=0.38)", "fig, axs = plt.subplots(1, 2, figsize=(W, 3.5), sharey=True); fig.subplots_adjust(wspace=0.42)")
rep("    a.set_xlabel('Easting, km', labelpad=5); a.set_ylabel('Northing, km', labelpad=5); a.tick_params(labelsize=7); letter(a, t)", "    a.set_xlabel('Easting, km', labelpad=5); a.tick_params(labelsize=7); letter(a, t)\naxs[0].set_ylabel('Northing, km', labelpad=5)")
open(p, 'w', encoding='utf-8', newline='').write(s); print('patched')
