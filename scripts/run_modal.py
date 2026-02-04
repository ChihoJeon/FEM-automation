#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from bridge_psci.config import make_params
from bridge_psci.analysis.modal import run_modal


def main():
    ap = argparse.ArgumentParser(description="Build PSCI bridge model and run modal extraction.")
    ap.add_argument("--case", default="baseline", help="Case name: baseline, case1, case2, case5, case6, case9")
    args = ap.parse_args()

    params = make_params(args.case)
    freqs_hz, eig, defl = run_modal(params)

    np.set_printoptions(precision=6, suppress=True)
    print(f"Case = {args.case}")
    print("Eigenvalues:", eig)
    print("Natural frequencies (Hz):", freqs_hz)
    print("Deflections at check nodes (mm):", defl)


if __name__ == "__main__":
    main()
