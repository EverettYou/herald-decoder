#!/usr/bin/env python3
"""Audit/recover reference resources using recorded URLs and SHA-256 hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import tarfile
from urllib.request import Request, urlopen

try:
    import certifi
except ImportError:  # Fall back to the interpreter's configured trust store.
    certifi = None

ROOT = Path(__file__).resolve().parents[1]


def tls_context():
    """Use an explicit CA bundle when the managed Python lacks macOS CA paths."""
    return ssl.create_default_context(cafile=certifi.where() if certifi else None)


def audit(restore=False, include_paper_sources=False):
    rows = []
    for ref in json.loads((ROOT / 'references/references.json').read_text())['references']:
        folder = ROOT / 'references' / ref['id']
        provenance = json.loads((folder / 'provenance.json').read_text())
        for name, expected in provenance.get('sha256', {}).items():
            if name not in {'paper.pdf', 'source.tar', 'source.tar.gz', 'source.tgz'}:
                continue
            target = folder / name
            required = name == 'paper.pdf' or ref['kind'] == 'repository'
            url = provenance.get('urls', {}).get('pdf' if name == 'paper.pdf' else 'archive' if ref['kind'] == 'repository' else 'source')
            row = dict(id=ref['id'], resource=name, required_for_viewer=required, url=url)
            try:
                if target.exists():
                    body = target.read_bytes()
                    if hashlib.sha256(body).hexdigest() != expected:
                        raise ValueError('Existing resource checksum mismatch; refusing to overwrite')
                    row['status'] = 'verified'
                elif restore and (required or include_paper_sources):
                    if not url:
                        raise ValueError('No recorded download URL')
                    # Never switch to a current branch/version to satisfy a pinned snapshot.
                    with urlopen(Request(url, headers={'User-Agent': 'HeraldDecoder-reference-restore/1.0'}), timeout=60, context=tls_context()) as response:
                        body = response.read()
                    if hashlib.sha256(body).hexdigest() != expected:
                        raise ValueError('Downloaded checksum differs from provenance; not installed')
                    temporary = target.with_name(name + '.restore-part')
                    try:
                        temporary.write_bytes(body)
                        if name == 'paper.pdf':
                            if not body.startswith(b'%PDF-'):
                                raise ValueError('Not a PDF')
                        else:
                            with tarfile.open(temporary, 'r:*') as bundle:
                                bundle.getmembers()
                        temporary.replace(target)
                    finally:
                        temporary.unlink(missing_ok=True)
                    row['status'] = 'restored'
                else:
                    row['status'] = 'missing'
            except Exception as error:
                row.update(status='error', error=str(error))
            rows.append(row)
            print(ref['id'], name, row['status'], row.get('error', ''), flush=True)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--include-paper-sources', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rows = audit(args.restore, args.include_paper_sources)
    if args.report:
        from datetime import datetime, timezone
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'resources': rows}, indent=2) + '\n')
    raise SystemExit(any(r['status'] == 'error' or (r['required_for_viewer'] and r['status'] == 'missing') for r in rows))
