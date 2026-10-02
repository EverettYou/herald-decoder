"""Archive the exact retained pilot prefixes, separately from confirmation."""
from pathlib import Path
import json,hashlib
import numpy as np
LAB=Path(__file__).resolve().parents[1]

def main():
    p=LAB/'results/phase-broad-grid.json';receipt=json.loads(p.read_text());directory=LAB/'data/phase-pilot';directory.mkdir(exist_ok=True)
    for row in receipt['rows']:
        if row['n']==0:continue
        source=LAB/row['vector'];dest=directory/source.name
        with np.load(source,allow_pickle=False)as z:arrays={k:z[k][:row['n']]for k in z.files}
        assert len(arrays['risk'])==row['n'] and abs(float(arrays['risk'].mean())-row['risk'])<1e-12
        assert int(arrays['failure'].sum())==row['direct_failures']
        np.savez_compressed(dest,**arrays)
        row['initial_vector_sha256']=row['sha256'];row['vector']=str(dest.relative_to(LAB));row['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
    receipt['archive_status']='Exact pilot prefixes archived separately; risk means and realized counts verified against frozen initial metadata. NPZ files reserialized, with separate initial and archival hashes.'
    p.write_text(json.dumps(receipt,indent=2)+'\n');print('archived',receipt['shots'],'pilot records')
if __name__=='__main__':main()
