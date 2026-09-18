#!/usr/bin/env python3
"""Render the canonical 3x2 full-irrep LER figure from audited raw counts."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

LAB = Path(__file__).resolve().parents[1]
FIGURE = 'figures/a8-full-record-ler-overview.png'
RESULT = 'results/a8-ler-overview-render.json'


def main():
    audit = json.loads((LAB/'results/a8-completion-audit-2026-09-07.json').read_text())
    assert audit['status'] == 'passed' and audit['sampled_cells'] == 600
    colors = ['#fca082', '#ef6548', '#cb181d', '#7f0000']
    sizes = (5, 7, 9, 11)
    with plt.rc_context({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False}):
        fig, axes = plt.subplots(3, 2, figsize=(12, 12.5), sharex=True, sharey=False)
        fig.subplots_adjust(left=.10, right=.975, top=.875, bottom=.18, hspace=.30, wspace=.23)
        panels = []
        for row, (group, label) in enumerate((('U1', 'U(1)'), ('SU2', 'SU(2)'), ('SU3', 'SU(3)'))):
            for col, lattice in enumerate(('square', 'honeycomb')):
                ax = axes[row, col]
                source = next(p for p in audit['panels'] if p['group'] == group and p['lattice'] == lattice)
                raw = (LAB/source['input']).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == source['input_sha256']
                data = json.loads(raw)
                assert data['status'] == 'complete' and data['scope']['measure_boundary_representation'] is False
                sampled = [r for r in data['rows'] if not r.get('exact_endpoint')]
                assert len(sampled) == 100
                for size, color in zip(sizes, colors):
                    curve = sorted((r for r in sampled if r['L'] == size), key=lambda r: r['p'])
                    assert len(curve) == 25 and all(r['shots'] == 20000 for r in curve)
                    x = np.array([r['p'] for r in curve]); y = np.array([r['ler'] for r in curve])
                    interval = np.array([r['wilson95'] for r in curve])
                    ax.errorbar(x, y, yerr=np.maximum(0, np.array([y-interval[:, 0], interval[:, 1]-y])),
                                fmt='o-', color=color, markersize=3, linewidth=1.5, capsize=2, elinewidth=.8)
                ymax = min(1, max(.001, 1.12*max(r['wilson95'][1] for r in sampled)))
                ax.set(xlim=(0, .5), ylim=(0, ymax), xticks=np.linspace(0, .5, 6))
                ax.set_title(f"({chr(97+row*2+col)})  {label}", loc='left', fontsize=12, fontweight='medium', pad=8)
                ax.grid(alpha=.20)
                panels.append({'row':row, 'column':col, 'lattice':lattice, 'group':group,
                               'input':source['input'], 'input_sha256':source['input_sha256'],
                               'sampled_cells':100, 'x_limits':[0,.5], 'y_limits':[0,ymax]})
        fig.suptitle('Full-irrep heralded logical error rate', y=.985, fontsize=18, fontweight='medium')
        fig.text(.5,.952,'Full interior (m,R) · directed channel · rough-boundary m and R unmeasured', ha='center',fontsize=11)
        for col, name in enumerate(('Square lattice','Honeycomb lattice')):
            position=axes[0,col].get_position()
            fig.text((position.x0+position.x1)/2,.907,name,ha='center',fontsize=15,fontweight='medium')
        fig.supylabel('Logical error rate', x=.018, y=.525, fontsize=13)
        fig.supxlabel('Physical edge-error probability p', y=.13, fontsize=13)
        handles=[Line2D([],[],color=color,marker='o',markersize=5,label=f'L = {size}') for size,color in zip(sizes,colors)]
        legend=fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.077),ncol=4,frameon=False,fontsize=12)
        fig.text(.5,.031,'20,000 shots per sampled cell · Wilson 95% intervals · independent vertical scales\nBP nonconvergence is diagnostic only; lines guide the eye. No threshold fit.',ha='center',fontsize=10,linespacing=1.7)
        assert len(fig.legends)==1 and all(ax.get_legend() is None for ax in axes.flat)
        assert all(axes[0,0].get_shared_x_axes().joined(axes[0,0],ax) for ax in list(axes.flat)[1:])
        assert all(not axes[0,0].get_shared_y_axes().joined(axes[0,0],ax) for ax in list(axes.flat)[1:])
        fig.canvas.draw()
        assert legend.get_window_extent().y1 < min(ax.get_window_extent().y0 for ax in axes.flat)
        path=LAB/FIGURE;temp=path.with_suffix('.tmp.png');fig.savefig(temp,dpi=200);plt.close(fig);temp.replace(path)
    result={'status':'passed','figure':FIGURE,'figure_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'layout':{'rows':['U1','SU2','SU3'],'columns':['square','honeycomb'],'shared_x':True,'shared_y':False,'legend':'one external legend below all panels, L=5,7,9,11 only','colors':dict(zip(map(str,sizes),colors)),'p_zero_marker':False},
            'sampled_cells':600,'shots':12000000,'panels':panels}
    (LAB/RESULT).write_text(json.dumps(result,indent=2)+'\n')
    print(f'Rendered {FIGURE}: 3x2 panels, one external legend, shared x and independent y.')

if __name__ == '__main__': main()
