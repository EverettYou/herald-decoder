# Scripts

Run from this lab directory:

```bash
python3 scripts/render_sample.py --p 0.12 --pm 0 --q 0.75 --ph 0 --seed 2
```

The script writes the Decoder On view to `figures/sample-configuration.svg`. Red and purple bonds are residual errors, while green bonds show resolved matches. Gold circles are recomputed residual syndromes; blue diamonds are original heralds that remain unresolved.

`local_decoder.py` is the unique executable source of truth for Stage 1. Its current synchronous order is distance-one herald pairs, then syndrome–herald–syndrome, then distance-two herald pairs; each rule consumes touched heralds only at the end of its snapshot update, and rule outputs combine over GF(2). The interactive viewer calls `predecode_payload` from this module and contains no decoder implementation.

The same module defines the square-lattice logical check as a smooth-to-smooth line through the right open-plaquette centers. It evaluates logical error by the mod-two residual-error parity on the retained horizontal data edges crossed by that line.

Run its unit checks with:

```bash
python3 scripts/test_local_decoder.py
```

`mwpm_decoder.py` owns the Stage 2 experiment. It imports PyMatching, builds the detector-by-edge sparse check matrix, validates rough-boundary singleton columns, and returns the MWPM correction string. The dashboard only exposes this Lab function over HTTP.

Run the Stage 2 checks with:

```bash
python3 scripts/test_mwpm_decoder.py
```

Validate the interactive square/honeycomb geometry with:

```bash
node scripts/test_viewer_geometry.js
```
