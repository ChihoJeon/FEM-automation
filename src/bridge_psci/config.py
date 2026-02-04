"""Configuration helpers.

The original notebook relied heavily on module-level globals.
For a first packaging step, we keep that behavior but centralize the
mutable parameters in a plain dict (so you can later replace it with
dataclasses / YAML).

Usage
-----
from bridge_psci.config import make_params
params = make_params(case="case2")
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

import numpy as np

from .defaults_base import get_default_base_params
# -------------------------
# Defaults (lifted from notebook cells 6/7)
# -------------------------
def _default_params() -> Dict[str, Any]:
    base = get_default_base_params()
    girder_number = int(base.get('girder_number', 6))

    free = 0
    consts = 1e9 / 1e3
    consts1 = 80000
    consts_crack = 1e9 / 1e4

    A1_B1 = [free, consts1, consts, 0, 0, 0]
    A1_B2 = [free, consts1, consts, 0, 0, 0]
    A1_B3 = [free, consts1, consts_crack, 0, 0, 0]
    A1_B4 = [free, consts1, consts_crack, 0, 0, 0]
    A1_B5 = [free, consts1, consts_crack, 0, 0, 0]
    A1_B6 = [free, consts1, consts, 0, 0, 0]

    A2_B1 = [consts1, free, consts_crack, 0, 0, 0]
    A2_B2 = [consts1, free, consts, 0, 0, 0]
    A2_B3 = [consts1, free, consts_crack, 0, 0, 0]
    A2_B4 = [consts1, free, consts_crack, 0, 0, 0]
    A2_B5 = [consts1, free, consts_crack, 0, 0, 0]
    A2_B6 = [consts1, consts1, consts, 0, 0, 0]

    bearing_multiplier = 0.3
    Bearing_Stiffness_A1 = np.vstack((A1_B1, A1_B2, A1_B3, A1_B4, A1_B5, A1_B6)) * bearing_multiplier
    Bearing_Stiffness_A2 = np.vstack((A2_B1, A2_B2, A2_B3, A2_B4, A2_B5, A2_B6))
    Bearing_Stiffness = np.vstack((Bearing_Stiffness_A1, Bearing_Stiffness_A2))

    params: Dict[str, Any] = dict(get_default_base_params())
    params.update(dict(
        # Material / stiffness sets
        E_girder1=[28000] * girder_number * 2,
        E_girder2=[28000] * girder_number * 2,
        E_deck1=[25000] * (girder_number + 1),
        E_deck2=[25000] * (girder_number + 1),
        thickness1=[250] * (girder_number + 2),
        thickness2=[250] * (girder_number + 2),

        # Bearings / springs
        Bearing_Stiffness=Bearing_Stiffness,
        bearing_multiplier=bearing_multiplier,
        consts1=consts1,
        consts_crack=consts_crack,

        # Prestress / diaphragm / pavement etc
        load=-290 * 1000 / 2,
        PE=600,
        diaphragm1_Ec=[24000] * 5,
        diaphragm2_Ec=[24000] * 5,
        pave_thick=[80],

        # Modal/dynamic analysis knobs
        numEigen=3,
        zeta=0.015,
        dt=0.1,
        velocity_kmh=10,

        # Node-tag conventions used in notebook
        girder3_start_tag=3001,
        girder4_start_tag=4001,
        girder_n_nodes=149,
    ))
    return params


# -------------------------
# Case overrides (lifted from case cells)
# -------------------------
CASE_OVERRIDES: Dict[str, Dict[str, Any]] = {
    # baseline / case1: same as defaults in notebook
    "baseline": {},
    "case1": {},

    # case2: bearing multiplier changed (cell 20)
    "case2": {"bearing_multiplier": 0.5},

    # case5/case6: local stiffness reduction in one girder line (cells 21/22)
    "case5": {"E_girder1": [28000 * 0.7, 28000, 28000, 28000, 28000, 28000]},
    "case6": {"E_girder1": [28000 * 0.5, 28000, 28000, 28000, 28000, 28000]},

    # case9: deck stiffness reduction (cell 23)
    "case9": {"E_deck1": "deck_0.7"},
}


def make_params(case: str = "baseline") -> Dict[str, Any]:
    """Return a parameters dict for the selected case.

    Notes
    -----
    - This is intentionally *thin* and close to the notebook behavior.
    - Further refactor target: replace this dict with dataclasses / YAML.
    """
    case = case.strip().lower()
    params = _default_params()
    girder_number = int(params.get('girder_number', 6))

    if case not in CASE_OVERRIDES:
        raise ValueError(f"Unknown case: {case}. Available: {sorted(CASE_OVERRIDES)}")

    overrides = dict(CASE_OVERRIDES[case])

    # Apply special override encodings
    if overrides.get("E_deck1") == "deck_0.7":
        overrides["E_deck1"] = [25000 * 0.7] * (int(girder_number) + 1)

    # bearing multiplier rebuild
    if "bearing_multiplier" in overrides:
        bm = float(overrides["bearing_multiplier"])
        overrides.pop("bearing_multiplier", None)

        free = 0
        consts = 1e9 / 1e3
        consts1 = params["consts1"]
        consts_crack = params["consts_crack"]

        A1_B1 = [free, consts1, consts, 0, 0, 0]
        A1_B2 = [free, consts1, consts, 0, 0, 0]
        A1_B3 = [free, consts1, consts_crack, 0, 0, 0]
        A1_B4 = [free, consts1, consts_crack, 0, 0, 0]
        A1_B5 = [free, consts1, consts_crack, 0, 0, 0]
        A1_B6 = [free, consts1, consts, 0, 0, 0]

        A2_B1 = [consts1, free, consts_crack, 0, 0, 0]
        A2_B2 = [consts1, free, consts, 0, 0, 0]
        A2_B3 = [consts1, free, consts_crack, 0, 0, 0]
        A2_B4 = [consts1, free, consts_crack, 0, 0, 0]
        A2_B5 = [consts1, free, consts_crack, 0, 0, 0]
        A2_B6 = [consts1, consts1, consts, 0, 0, 0]

        Bearing_Stiffness_A1 = np.vstack((A1_B1, A1_B2, A1_B3, A1_B4, A1_B5, A1_B6)) * bm
        Bearing_Stiffness_A2 = np.vstack((A2_B1, A2_B2, A2_B3, A2_B4, A2_B5, A2_B6))
        params["Bearing_Stiffness"] = np.vstack((Bearing_Stiffness_A1, Bearing_Stiffness_A2))
        params["bearing_multiplier"] = bm

    # Normal overrides
    params.update(overrides)
    return params


def ensure_dir(p: str | Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p
