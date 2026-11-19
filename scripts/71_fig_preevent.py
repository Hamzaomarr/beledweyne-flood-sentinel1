import os, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
B = r'.'; DG = os.path.join(B, 'data', 'processed', 'diag')
Z = np.load(os.path.join(DG, 's1_100m_means.npz')); d = Z['o21_VV'] - Z['o09_VV']; ex = np.load(os.path.join(DG, 'extra21_100m.npy')); mn = np.load(os.path.join(DG, 'main14_100m.npy'))
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Cambria', 'DejaVu Serif'], 'font.size': 8})
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.9), constrained_layout=True); ext = (498, 574, 490, 560)
im = ax[0].imshow(d, cmap='RdBu_r', vmin=-4, vmax=4, extent=ext, interpolation='nearest'); cb = fig.colorbar(im, ax=ax[0], shrink=0.8, pad=0.02); cb.set_label('Mean change in VV, dB')
rgb = np.ones(ex.shape + (3,)); ha = np.clip(mn, 0, 1); hb = np.clip(ex, 0, 1)
rgb[..., :] = 1 - hb[..., None] * (1 - np.array([0.85, 0.37, 0.0])); rgb = np.where(ha[..., None] > 0, 1 - ha[..., None] * (1 - np.array([0.17, 0.17, 0.17])) * 0 - 0, rgb) if False else rgb
im2 = ax[1].imshow(hb, cmap='YlOrBr', vmin=0, vmax=1, extent=ext, interpolation='nearest'); cb2 = fig.colorbar(im2, ax=ax[1], shrink=0.8, pad=0.02); cb2.set_label('Share of 100 m cell flagged only with the 21 October reference')
ax[1].contour(np.linspace(498.05, 573.95, mn.shape[1]), np.linspace(559.95, 490.05, mn.shape[0]), mn, levels=[0.05], colors='#333333', linewidths=0.4)
for a, t in zip(ax, ['a', 'b']):
    a.set_xlabel('Easting, km (UTM 38N)'); a.set_ylabel('Northing, km'); a.text(0.02, 0.97, t, transform=a.transAxes, va='top', fontweight='bold', fontsize=10, bbox=dict(fc='white', ec='none', pad=1.5))
fig.savefig(os.path.join(B, 'outputs', 'figures', 'fig13_preevent_scene_difference.png'), dpi=300); print('ok')
