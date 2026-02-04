#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from bridge_psci.io.excel_io import load_params_from_excel
from bridge_psci.analysis.modal import run_modal
from bridge_psci.analysis.moving_load import run_moving_load


def main():
    ap = argparse.ArgumentParser(description="Run modal + moving-load analyses from an Excel workbook.")
    ap.add_argument("--excel", required=True, help="Path to v3 (multi-sheet) or v2 Excel template")
    ap.add_argument("--case", default="baseline", help="Case label (from Excel 'Cases' sheet). Default: baseline")
    ap.add_argument("--out", default="outputs", help="Output directory")
    ap.add_argument("--skip_modal", action="store_true", help="Skip modal analysis")
    ap.add_argument("--skip_moving", action="store_true", help="Skip moving-load analysis")
    args = ap.parse_args()

    excel_path = Path(args.excel)
    out_dir = Path(args.out) / args.case
    out_dir.mkdir(parents=True, exist_ok=True)

    params = load_params_from_excel(excel_path, case=args.case)

    if not args.skip_modal:
        run_modal(params=params, output_dir=out_dir, case_label=args.case)

    if not args.skip_moving:
        run_moving_load(params=params, output_dir=out_dir, case_label=args.case)

    print(f"✅ Done. Results in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
