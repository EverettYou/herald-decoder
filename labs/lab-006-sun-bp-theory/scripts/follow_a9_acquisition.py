#!/usr/bin/env python3
"""Run the registered full-data audit automatically once all paired cells exist."""
import json, os, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone
LAB=Path(__file__).resolve().parents[1]
STATE=LAB/'results/a9-follow-on.json'
def state(status, **kwargs):
    temp=STATE.with_suffix('.follow.tmp')
    temp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated=datetime.now(timezone.utc).isoformat(),**kwargs),indent=2)+'\n')
    temp.replace(STATE)
def main():
    state('waiting_for_acquisition',trigger='600 paired cells',next_action='Audit all shot indicators, directed replays, SU2 identity and registered paired statistics; regenerate all three figures.')
    while True:
        counts=[len(json.loads(p.read_text())['rows']) for p in sorted((LAB/'results').glob('a9-hidden-*.json'))]
        if len(counts)==6 and counts==[100]*6: break
        time.sleep(20)
    state('analyzing')
    for script in ('analyze_a9_orientation.py','render_a9_orientation.py'):
        subprocess.run([sys.executable,str(LAB/'scripts'/script)],check=True)
    state('analysis_complete',next_action='Integrate measured conclusions into Wiki and REPORT, verify the final browser delivery, and close the active contract only after acceptance gates pass.')
if __name__=='__main__':
    try: main()
    except Exception as e:
        state('failed',error=repr(e)); raise
