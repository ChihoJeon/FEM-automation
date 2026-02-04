#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from bridge_psci.config import make_params, ensure_dir
from bridge_psci.model.builder import build_bridge_model
from bridge_psci.model.visualization import snapshot_model


def main():
    ap = argparse.ArgumentParser(description="Build model and save a 3D snapshot image.")
    ap.add_argument("--case", default="baseline")
    ap.add_argument("--out", default="outputs/snapshots/model.png")
    ap.add_argument("--no-vfo", action="store_true")
    args = ap.parse_args()

    params = make_params(args.case)
    build_bridge_model(params)

    out_path = Path(args.out)
    ensure_dir(out_path.parent)
    snapshot_model(str(out_path), use_vfo=(not args.no_vfo))
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
