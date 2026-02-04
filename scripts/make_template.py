#!/usr/bin/env python
"""Create an Excel input template."""
from __future__ import annotations

import argparse
from pathlib import Path

from bridge_psci.io.excel_io import create_excel_template


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bridge_input_template_v3.xlsx", help="Output .xlsx path")
    args = ap.parse_args()

    out = Path(args.out)
    create_excel_template(out)
    print("✅ Wrote template:", out.resolve())


if __name__ == "__main__":
    main()
