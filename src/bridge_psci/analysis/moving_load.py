"""Moving-load transient analysis (node-wise PathSeries).

This module is based on notebook case cells (19-23). The goal here is to keep the
behavior very close to the notebook, but expose it as a reusable function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt
try:
    import openseespy.opensees as ops  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    ops = None  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = e


from ..config import ensure_dir
from ..model.builder import build_bridge_model


def _get_girder_tags(start_tag: int, n_nodes: int) -> np.ndarray:
    tags = np.array(ops.getNodeTags(), dtype=int)
    idx0 = np.where(tags == int(start_tag))[0]
    if idx0.size == 0:
        raise RuntimeError(f"Start tag {start_tag} not found in current OpenSees domain.")
    i0 = int(idx0[0])
    return tags[i0 : i0 + int(n_nodes)]


def run_moving_load(
    params: dict,
    output_dir: str | Path,
    case_label: str = "case1",
    vehicle_loads_n: Tuple[float, ...] | None = None,
    vehicle_distances_mm: Tuple[float, ...] | None = None,
    make_plot: bool = True,
):
    if ops is None:  # pragma: no cover
        raise ImportError('openseespy is required') from _OPENSEESPY_IMPORT_ERROR

    """Run the transient moving-load analysis and write midspan acceleration CSVs.

    Outputs (same as notebook)
    --------------------------
    - `<case_label>mid_accel_g3.csv`
    - `<case_label>mid_accel_g4.csv`

    Returns
    -------
    (csv_path_g3, csv_path_g4)
    """
    output_dir = ensure_dir(output_dir)

    # Build the model (params are applied inside build_bridge_model)
    build_bridge_model(params)

    # Eigen extraction
    numEigen = int(params.get("numEigen", 3))
    eigen_value = ops.eigen(numEigen)

    # ------------------------------------------------------------
    # 0) Geometry setup
    # ------------------------------------------------------------
    girder3 = _get_girder_tags(int(params.get("girder3_start_tag", 3001)), int(params.get("girder_n_nodes", 149)))
    girder4 = _get_girder_tags(int(params.get("girder4_start_tag", 4001)), int(params.get("girder_n_nodes", 149)))

    coords_g3 = np.array([ops.nodeCoord(int(nd)) for nd in girder3], dtype=float)
    coords_g4 = np.array([ops.nodeCoord(int(nd)) for nd in girder4], dtype=float)
    x_g3, y_g3 = coords_g3[:, 0], coords_g3[:, 1]
    x_g4, y_g4 = coords_g4[:, 0], coords_g4[:, 1]
    bridge_length = float(abs(x_g3[-1] - x_g3[0]))

    # ------------------------------------------------------------
    # 1) Vehicle configuration (6-axle truck)
    # ------------------------------------------------------------
    if vehicle_loads_n is None:
        vehicle_loads_n = (
            61300.0 / 2, 114700.0 / 2, 110820.0 / 2,
            61300.0 / 2, 114700.0 / 2, 110820.0 / 2,
        )
    if vehicle_distances_mm is None:
        vehicle_distances_mm = (0.0, 3300.0, 4600.0, 0.0, 3300.0, 4600.0)

    vehicle_config = {"loads": list(vehicle_loads_n), "distances": list(vehicle_distances_mm)}

    velocity_kmh = float(params.get("velocity_kmh", 10))
    speed = velocity_kmh * 1000 * 1000 / 3600  # mm/s

    x_start_g3, y_start_g3 = x_g3[-1], y_g3[-1]
    x_start_g4, y_start_g4 = x_g4[-1], y_g4[-1]

    dt = float(params.get("dt", 0.1))
    truck_length = abs(max(vehicle_config["distances"]))
    t_total = (bridge_length + truck_length) / speed
    time_steps = np.arange(0, t_total + 5, dt)

    # ------------------------------------------------------------
    # 2) Node-wise load history initialization
    # ------------------------------------------------------------
    node_load_history_g3 = {int(nd): np.zeros(len(time_steps), dtype=float) for nd in girder3}
    node_load_history_g4 = {int(nd): np.zeros(len(time_steps), dtype=float) for nd in girder4}

    # ------------------------------------------------------------
    # 3) Load history generation
    # ------------------------------------------------------------
    for it, t in enumerate(time_steps):
        progress = speed * t

        for i_ax, (dist, load_val) in enumerate(zip(vehicle_config["distances"], vehicle_config["loads"])):
            if i_ax < 3:
                x_axle = x_start_g3 - progress + dist
                x_g, girder, node_hist = x_g3, girder3, node_load_history_g3
            else:
                x_axle = x_start_g4 - progress + dist
                x_g, girder, node_hist = x_g4, girder4, node_load_history_g4

            if x_g[0] <= x_axle <= x_g[-1]:
                idx = np.searchsorted(x_g, x_axle) - 1
                idx = int(np.clip(idx, 0, len(girder) - 2))
                xi, xj = x_g[idx], x_g[idx + 1]
                nd_i, nd_j = int(girder[idx]), int(girder[idx + 1])
                r = (x_axle - xi) / (xj - xi)

                node_hist[nd_i][it] += load_val * (1 - r)
                node_hist[nd_j][it] += load_val * r

    # ------------------------------------------------------------
    # 4) Analysis setup
    # ------------------------------------------------------------
    ops.wipeAnalysis()

    omega_list = np.sqrt(np.array(eigen_value, dtype=float))
    omega1, omega2 = omega_list[0], omega_list[min(2, len(omega_list) - 1)]
    zeta = float(params.get("zeta", 0.015))
    alphaM = zeta * (2 * omega1 * omega2) / (omega1 + omega2)
    betaK = 2 * zeta / (omega1 + omega2)
    ops.rayleigh(alphaM, 0.0, 0.0, betaK)

    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("SparseGeneral")
    ops.test("NormDispIncr", 1e-5, 10)
    ops.algorithm("Newton")
    ops.integrator("Newmark", 0.5, 0.25)
    ops.analysis("Transient")

    # ------------------------------------------------------------
    # 5) Recorders
    # ------------------------------------------------------------
    mid_node_g3 = int(girder3[len(girder3) // 2])
    mid_node_g4 = int(girder4[len(girder4) // 2])

    g3_path = Path(output_dir) / f"({case_label})mid_accel_g3.csv"
    g4_path = Path(output_dir) / f"({case_label})mid_accel_g4.csv"

    # OpenSees expects strings
    ops.recorder("Node", "-file", str(g3_path), "-time", "-node", mid_node_g3, "-dof", 3, "accel")
    ops.recorder("Node", "-file", str(g4_path), "-time", "-node", mid_node_g4, "-dof", 3, "accel")

    # ------------------------------------------------------------
    # 6) Create PathSeries (node-wise, unique tags)
    # ------------------------------------------------------------
    def create_pathseries_from_history(history_dict, girder_id: int):
        for nd, values in history_dict.items():
            if np.allclose(values, 0.0):
                continue
            ts_tag = 1000 * int(girder_id) + int(nd)
            pat_tag = 2000 * int(girder_id) + int(nd)
            ops.timeSeries("Path", ts_tag, "-dt", dt, "-values", *values.tolist(), "-factor", 1.0)
            ops.pattern("Plain", pat_tag, ts_tag)
            # NOTE: load vector is scaled by the Path time series; keep -1.0 to preserve notebook convention.
            ops.load(int(nd), 0.0, 0.0, -1.0, 0.0, 0.0, 0.0)

    create_pathseries_from_history(node_load_history_g3, 3)
    create_pathseries_from_history(node_load_history_g4, 4)

    # ------------------------------------------------------------
    # 7) Run analysis
    # ------------------------------------------------------------
    ops.analyze(len(time_steps), dt)

    # ------------------------------------------------------------
    # 8) Optional plot (same as notebook scaling: g & 1000)
    # ------------------------------------------------------------
    if make_plot:
        data_g3 = np.loadtxt(g3_path)
        data_g4 = np.loadtxt(g4_path)

        t = data_g3[:, 0]
        acc_g3 = data_g3[:, 1] / 9.81 / 1000
        acc_g4 = data_g4[:, 1] / 9.81 / 1000

        plt.figure(figsize=(10, 4))
        plt.plot(t, acc_g3, lw=1.2, label="Girder3")
        plt.plot(t, acc_g4, lw=1.2, label="Girder4")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (g)")
        plt.title("Midspan Acceleration Response (6-axle Truck, Node-wise PathSeries)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return g3_path, g4_path
