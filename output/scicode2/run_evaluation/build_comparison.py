"""Assemble reported boundaries and observed run metadata; render comparison."""
import csv,json,hashlib
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2];RUNS=Path('/Users/home/Downloads/runs')
def csvrows(p):return list(csv.DictReader(p.open()))
curves=[]
def add(name,family,points,source):
    curves.append(dict(name=name,family=family,points=points,source=str(source)))
for r in [1,2,3]:
    d=RUNS/'anthropic__claude-fable-5-1'/f'run_{r:02}'
    if r==1:
        for method,fam in [('hmw','MAP'),('ml','ML approximate')]:
            f=d/'data'/f'thresholds_{method}.csv'
            points=[(float(x['pc']),float(x['q'])) for x in csvrows(f) if x['pc']]
            points.append((.5,.8746283317581778 if method=='hmw' else .8380869238062519))
            add(f'Fable {r} {method.upper()}',fam,points,f)
    elif r==2:
        f=d/'data/thresholds_sections.csv';points=[(float(x['pc_final']),float(x['q'])) for x in csvrows(f) if x['pc_final'] and 0<float(x['pc_final'])<.5];points.append((.5,.882));add('Fable 2 MAP','MAP',points,f)
    else:
        f=d/'data/boundary.csv';add('Fable 3 MPS','ML approximate',[(float(x['x_c']),float(x['q'])) if x['var']=='p' else (float(x['p']),float(x['x_c'])) for x in csvrows(f)],f)
for r in [1,2,3]:
    d=RUNS/'anthropic__claude-opus-5-5'/f'run_{r:02}'
    if r==1:
        f=d/'results/boundary_estimates.csv';points=[(float(x['p']),float(x['q'])) for x in csvrows(f)]
    elif r==2:
        f=d/'data/boundary_pc_of_q.csv';points=[(float(x['p_c']),float(x['q'])) for x in csvrows(f)]
        points.append((.5,.8664))
    else:
        f=d/'data/thresholds.json';points=[(x['estimate']['xc'],x['value']) if x['kind']=='q' else (x['value'],x['estimate']['xc']) for x in json.loads(f.read_text())]
    add(f'Opus {r} ML','ML',points,f)
for r in [1,2,3]:
    d=RUNS/'openai__gpt-6-astra'/f'run_{r:02}'
    if r==1:
        f=d/'data/thresholds.csv';points=[(float(x['xc']),float(x['q'])) for x in csvrows(f) if x['xc']]
        points.append((.5,.886))
    elif r==2:
        f=d/'REPORT.md';points=[(.158,0),(.178,.2),(.206,.4),(.222,.5),(.250,.6),(.284,.7),(.342,.8),(.401,.85),(.429,.865),(.456,.875),(.5,.885)]
    else:
        f=d/'data/transitions.csv';points=[(float(x['pc']),float(x['fixed_value'])) if x['axis']=='p' else (float(x['fixed_value']),float(x['pc'])) for x in csvrows(f)]
    add(f'Astra {r} MAP','MAP',points,f)
(OUT/'reported_boundaries.json').write_text(json.dumps(curves,indent=2)+'\n')
fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
j=json.loads((ROOT/'labs/lab-003-herald-threshold-phase-diagram/results/current-evidence.json').read_text())
cells=j['evidence']['honeycomb_finite_window_trend']['cells']
vals=[c['posterior_log_odds_upward_vs_downward'] if c['posterior_log_odds_upward_vs_downward'] is not None else c['posterior_log_odds_censoring']['bound'] for c in cells]
sc=axes[0].scatter([c['p'] for c in cells],[c['q'] for c in cells],c=np.clip(vals,-6,6),s=65,marker='s',cmap='RdBu_r',vmin=-6,vmax=6)
fig.colorbar(sc,ax=axes[0],shrink=.7,label='Log posterior odds: increasing / decreasing LER')
axes[0].set_title('Repository BP evidence\nFinite window, mainly L = 7, 9, 11')
for c in curves:
    ax=axes[1] if c['family']=='MAP' else axes[2]
    pts=sorted(set(map(tuple,c['points'])),key=lambda z:z[1]);pts=[z for z in pts if 0<=z[0]<=.5 and 0<=z[1]<=1]
    ax.plot(*np.array(pts).T,'.--' if 'Fable' in c['name'] else '.-',lw=1.3,ms=4,label=c['name'])
axes[1].set_title('Reported configuration MAP boundaries\nDifferent tie rules and size ranges')
axes[2].set_title('Reported logical sector boundaries\nPlanar ML or approximate contraction')
for ax in axes:
    ax.set(xlim=(0,.5),ylim=(0,1),xlabel='Physical error probability p',ylabel='Herald availability q');ax.grid(alpha=.15)
for ax in axes[1:]:ax.legend(fontsize=8,loc='upper left')
fig.savefig(OUT/'boundary_comparison.png',dpi=180)
fig.savefig(OUT/'boundary_comparison.pdf')
plt.close(fig)

inventory=[];hashes={}
for d in sorted(RUNS.glob('*/run_*')):
    m=json.loads((d/'meta.json').read_text());elapsed=(datetime.fromisoformat(m['finished_at'].replace('Z','+00:00'))-datetime.fromisoformat(m['started_at'].replace('Z','+00:00'))).total_seconds()/3600
    inventory.append({'model':m['model'],'run':m['run'],'elapsed_hours':elapsed,'cost_usd':m['cost_usd'],'files':m['n_files'],'graded':m['graded'],'prompt_sha8':m['prompt_sha8']})
    for f in d.rglob('*'):
        if f.is_file() and (f.suffix in ['.py','.csv','.jsonl'] or f.name.lower() in ['report.md','meta.json','readme.md']):hashes[str(f.relative_to(RUNS))]=hashlib.sha256(f.read_bytes()).hexdigest()
(OUT/'run_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
(OUT/'input_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('Saved',len(curves),'curves;',len(inventory),'runs;',len(hashes),'input hashes')
print('Historical metadata cost total:',sum(x['cost_usd'] for x in inventory))
