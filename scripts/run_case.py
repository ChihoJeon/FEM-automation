#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from bridge_psci.config import make_params, ensure_dir
from bridge_psci.analysis.moving_load import run_moving_load


def main():
    ap = argparse.ArgumentParser(description="Run moving-load transient analysis (node-wise PathSeries).")
    ap.add_argument("--case", default="case1", help="Case name: case1, case2, case5, case6, case9")
    ap.add_argument("--out", default="outputs/responses", help="Output directory for recorder CSVs")
    ap.add_argument("--no-plot", action="store_true", help="Disable plotting")
    args = ap.parse_args()

    params = make_params(args.case)
    out_dir = ensure_dir(args.out)

    g3, g4 = run_moving_load(params, out_dir, case_label=args.case, make_plot=not args.no_plot)
    print("Wrote:")
    print(" -", g3)
    print(" -", g4)


if __name__ == "__main__":
    main()
