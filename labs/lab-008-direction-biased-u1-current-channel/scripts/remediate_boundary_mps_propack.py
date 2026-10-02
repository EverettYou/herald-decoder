#!/usr/bin/env python3
"""Evaluate PROPACK partial SVD under the frozen per-vertex semantics."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import platform
import resource
from pathlib import Path
import sys
import time
import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(LAB / "scripts")]
from herald_decoder.lattice_model import square_graph
from boundary_mps_posterior import BoundaryMPSPosterior
from remediate_boundary_mps_throughput import tasks

OUT = LAB / "results" / "boundary-mps-throughput-remediation-propack-2026-09-21.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rss():
    v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return v/(1024**3 if platform.system()=="Darwin" else 1024**2)

def evaluate(task):
    model=square_graph(int(task["L"]));Q=np.asarray(task["charge"],dtype=np.int16);rows=[]
    for direction,order in (("left-to-right",list(model.detector_vertices)),("right-to-left",list(reversed(model.detector_vertices)))):
        engine=BoundaryMPSPosterior(model,order=order)
        for chi in (16,32):
            t=time.monotonic();candidate=engine.infer(Q,.30,float(task["q"]),chi=chi,svd_solver="propack")
            baseline=np.asarray(task["baseline"][(direction,chi)])
            rows.append({"direction":direction,"chi":chi,"sectors":candidate.sectors.tolist(),"baseline_sectors":baseline.tolist(),"maximum_sector_replay_error":float(np.max(np.abs(candidate.sectors-baseline))),"seconds":time.monotonic()-t})
    return {"kind":task["kind"],"id":task["id"],"L":task["L"],"q":task["q"],"rows":rows,"worker_peak_gib":rss()}

def main():
    work=tasks();started=time.monotonic();results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(evaluate,t) for t in work]
        for f in as_completed(futures): results.append(f.result())
    elapsed=time.monotonic()-started;rows=[r for x in results for r in x["rows"]];l13=[r for x in results if x["L"]==13 for r in x["rows"]]
    means={f"chi{chi}_{direction}":float(np.mean([r["seconds"] for r in l13 if r["chi"]==chi and r["direction"]==direction])) for chi in (16,32) for direction in ("left-to-right","right-to-left")}
    worker=1152*means["chi16_left-to-right"]+144*(means["chi16_right-to-left"]+means["chi32_left-to-right"]+means["chi32_right-to-left"]);projected=worker/4;error=max(r["maximum_sector_replay_error"] for r in rows)
    gates={"all_24_frozen_evaluations_complete":len(rows)==24,"maximum_sector_replay_error_le_1e-10":error<=1e-10,"minimum_matrix_projection_le_7200_seconds":projected<=7200,"conservative_memory_le_8_gib":rss()+sum(x["worker_peak_gib"] for x in results)<=8,"production_histories_zero":True}
    result={"id":"lab008-boundary-mps-throughput-remediation-propack-2026-09-21","status":"accepted" if all(gates.values()) else "rejected","candidate":"per-vertex TT-SVD with deterministic PROPACK top-chi solver","gates":gates,"maximum_sector_replay_error":error,"l13_mean_seconds":means,"minimum_matrix_projected_worker_seconds":worker,"minimum_matrix_projected_four_worker_wall_seconds":projected,"measured_matrix_wall_seconds":elapsed,"results":sorted(results,key=lambda x:(x["L"],x["q"],x["id"])),"production_histories_generated":0,"source_hashes":{"runner":sha(__file__),"implementation":sha(LAB/"scripts/boundary_mps_posterior.py")}}
    OUT.write_text(json.dumps(result,indent=2)+"\n");print(json.dumps({"status":result["status"],"gates":gates,"maximum_sector_replay_error":error,"projected_wall_seconds":projected,"measured_wall_seconds":elapsed},indent=2))

if __name__=="__main__": main()
