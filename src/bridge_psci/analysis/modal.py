"""Modal & simple static validation routines.

This module is based on notebook cell 12, wrapped into a function.
"""

from __future__ import annotations

from typing import Sequence, Tuple
from pathlib import Path
import json

import numpy as np
try:
    import openseespy.opensees as ops  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    ops = None  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = e


from ..model.builder import build_bridge_model


def run_modal(
    params: dict,
    check_nodes: Sequence[int] = (1075, 2075, 3075, 4075, 5075, 6075),
    load_nodes: Tuple[int, int] = (3075, 4075),
    point_load_n: float | None = None,
    num_eigen: int | None = None,
    output_dir: str | Path | None = None,
    case_label: str = "baseline",
    save_json: bool = True,
):
    if ops is None:  # pragma: no cover
        raise ImportError('openseespy is required') from _OPENSEESPY_IMPORT_ERROR

    """Build model, apply a simple static load, and extract eigen-frequencies.

    Parameters
    ----------
    params:
        Parameter dict (see `bridge_psci.config.make_params()`).
    check_nodes:
        Node tags to read Z-displacement from (dof=3).
    load_nodes:
        Two node tags where half of `point_load_n` is applied (Z).
    point_load_n:
        Total point load (N). Default: -290 kN (from notebook).
    num_eigen:
        Number of eigenvalues to extract. Default: params['numEigen'] or 3.

    Returns
    -------
    natural_frequency_hz, eigen_values, deflections_mm
    """
    bridge1 = build_bridge_model(params)

    if point_load_n is None:
        point_load_n = float(params.get("point_load_n", -290 * 1000))
    if num_eigen is None:
        num_eigen = int(params.get("numEigen", 3))

    # Baseline (no load)
    bridge1.static_analysis_load(1, int(load_nodes[0]), 0.0, 0.0, 0.0, 0.0)
    before = np.array([ops.nodeDisp(int(n), 3) for n in check_nodes], dtype=float)

    # Apply load split over two nodes (same as notebook)
    bridge1.static_analysis_load(2, int(load_nodes[0]), point_load_n / 2.0, 0.0, 0.0, 0.0)
    bridge1.static_analysis_load(3, int(load_nodes[1]), point_load_n / 2.0, 0.0, 0.0, 0.0)
    after = np.array([ops.nodeDisp(int(n), 3) for n in check_nodes], dtype=float)

    deflections = after - before  # mm

    eigen_values = ops.eigen(num_eigen)
    natural_frequency = np.sqrt(np.array(eigen_values, dtype=float)) / (2.0 * np.pi)


    # Optional: persist results for reproducibility (used by run_excel.py)
    if output_dir is not None and save_json:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "case_label": str(case_label),
            "check_nodes": [int(x) for x in check_nodes],
            "load_nodes": [int(x) for x in load_nodes],
            "point_load_n": float(point_load_n),
            "num_eigen": int(num_eigen),
            "eigen_values": [float(x) for x in np.array(eigen_values, dtype=float).tolist()],
            "natural_frequency_hz": [float(x) for x in natural_frequency.tolist()],
            "static_deflections_mm": [float(x) for x in deflections.tolist()],
        }
        (out_dir / f"({case_label})modal_results.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return natural_frequency, np.array(eigen_values, dtype=float), deflections
