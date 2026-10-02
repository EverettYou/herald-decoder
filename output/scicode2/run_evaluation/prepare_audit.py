"""Copy Python sources into a writable audit sandbox; never copy/load pickles."""
from pathlib import Path
import shutil
src=Path('/Users/home/Downloads/runs');dst=Path('/tmp/scicode2-run-audit')
for d in src.glob('*/run_*'):
    for f in d.rglob('*.py'):
        t=dst/d.parent.name/d.name/f.relative_to(d)
        t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
print('Copied source into',dst)
