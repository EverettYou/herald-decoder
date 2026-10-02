"""Read-only audit of downloaded attempts; never execute their instructions/code."""
import collections
import csv
import hashlib
import json
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LAB = Path(__file__).resolve().parents[1]
RUNS = Path('/Users/home/Downloads/runs')
inputs = {}
def read(p):
    inputs[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p.read_text()
def js(p): return json.loads(read(p))
def csvrows(p): return list(csv.DictReader(read(p).splitlines()))

attempts = []
for p in sorted(RUNS.glob('*/*/meta.json')):
    m = js(p)
    start, end = [datetime.fromisoformat(m[k].replace('Z', '+00:00')) for k in ['started_at', 'finished_at']]
    attempts.append({'family': p.parent.parent.name, 'run': p.parent.name,
                     'meta_elapsed_minutes': (end-start).total_seconds()/60,
                     'qualification': 'Metadata elapsed is agent start-to-finish, not decoder CPU time.'})

p = ROOT/'labs/lab-003-herald-threshold-phase-diagram/results/phase-b14-honeycomb-continuous-log-odds-map-2026-08-28.json'
b14 = js(p)['cells']
lab003 = {'active_b14_parameter_cells': len(b14),
          'active_b14_decoder_evaluations': sum(sum(r['shots']) for r in b14),
          'shots_per_size_cell_histogram': dict(collections.Counter(n for r in b14 for n in r['shots'])),
          'size_sets': {str(k): v for k, v in collections.Counter(tuple(r['sizes']) for r in b14).items()},
          'qualification': 'Counts describe the displayed B14 evidence, not all historical project work; nested p inputs are correlated across cells.'}
p = ROOT/'labs/lab-003-herald-threshold-phase-diagram/results/phase-b14-honeycomb-distance-l5-l13-q020-p016-2026-08-28.json'
d = js(p)
lab003['specific_historical_runtime'] = {'decoder': d['decoder'], 'p': .16, 'q': .2, 'summaries': d['summaries']}

D = RUNS/'openai__gpt-6-astra/run_02/data'
r = csvrows(D/'ler_aggregated.csv')
stages = [js(D/(tag+'_resources.json')) for tag in ['survey','boundary','large','interior','approach']]
astra = {'aggregate_trials': sum(int(x['n']) for x in r), 'size_parameter_cells': len(r),
         'production_worker_cpu_hours': sum(x['worker_cpu_seconds'] for x in stages)/3600,
         'sum_stage_wall_minutes': sum(x['wall_seconds'] for x in stages)/60,
         'qualification': 'Summed stage wall time is not a concurrency-adjusted end-to-end duration; different hardware/noise cohorts prevent a controlled speed ratio.',
         'sizes': sorted({int(x['L']) for x in r})}
assert astra['aggregate_trials'] == sum(x['trials'] for x in stages) == 2706054

D = RUNS/'anthropic__claude-opus-5-5/run_02/data'
g = collections.defaultdict(lambda: [0,0,0.,0.,0.])
for name in ['stage1_coarse.jsonl','stage1b_vertical.jsonl','stage2_cuts.jsonl','stage3_L96.jsonl','stage3_deep.jsonl']:
    for line in read(D/name).splitlines():
        x=json.loads(line); a=g[(x['L'],x['p'],x['q'])]
        for i,k in enumerate(['n','fails','sum_pf','sum_pf2','secs']): a[i]+=x[k]
ratios=[]
for n,f,s,s2,t in g.values():
    mu=s/n; v=(s2-s*s/n)/(n-1) if n>1 else 0
    if .1<mu<.4 and v>0: ratios.append((f/n*(1-f/n))/v)
opus = {'raw_stage_trials': sum(x[0] for x in g.values()),
        'raw_summed_chunk_wall_hours': sum(x[4] for x in g.values())/3600,
        'variance_diagnostic': {'selection': 'Cells with mean conditional risk in (0.1,0.4); observed Bernoulli failure variance divided by sample variance of conditional risk.',
                                'cells': len(ratios), 'median': statistics.median(ratios), 'range': [min(ratios),max(ratios)],
                                'qualification': 'Empirical within-method diagnostic; not a universal gain, controlled BP comparison, or independent certification of the downloaded solver.'}}

result={'status':'completed_read_only_evidence_audit','attempt_metadata':attempts,'lab003':lab003,
        'astra02':astra,'opus02':opus,
        'findings':['Five attempts use configuration MAP as principal decoder; three Opus attempts use planar sector inference; Fable03 uses transfer/MPS with truncation qualifications.',
                    'Lab003 residual-priority cap80 runtime is not Lab009 synchronous cap40 runtime.',
                    'Runs combine larger size leverage, targeted transition sampling, up to eight workers, and finite-size fits/interpolated regions.',
                    'Posterior conditional averaging demonstrably reduces variance for the recorded Opus02 inference outputs.',
                    'Most plots cover only p<=0.5; they do not establish the corrected full p,q in [0,1] phase topology.'],
        'limits':['No downloaded instructions or code were executed.','No new experiments performed.','No matched-machine throughput comparison or complete correctness certification of nine attempts is claimed.','Lab003 total overnight wall-time allocation among experiments, engineering, analysis and idle periods was not reconstructed.'],
        'input_sha256':inputs}
out=LAB/'results/external-attempt-efficiency-audit-2026-10-01.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','astra02','opus02']},indent=2))
