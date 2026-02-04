"""Model visualization utilities extracted from the original notebook."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

try:
    import vfo.vfo as vfo
except Exception:  # pragma: no cover
    vfo = None

try:
    import openseespy.opensees as ops  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    ops = None  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = e


def _set_equal_aspect_3d(ax):
    xlim = np.array(ax.get_xlim3d())
    ylim = np.array(ax.get_ylim3d())
    zlim = np.array(ax.get_zlim3d())
    c = np.array([xlim.mean(), ylim.mean(), zlim.mean()])
    r = max(xlim.ptp(), ylim.ptp(), zlim.ptp()) / 2
    ax.set_xlim3d(c[0]-r, c[0]+r)
    ax.set_ylim3d(c[1]-r, c[1]+r)
    ax.set_zlim3d(c[2]-r, c[2]+r)

def snapshot_model(path=None, use_vfo=True, elev=20, azim=-60, dpi=200, lw=0.8, node_size=6):

    if use_vfo and (vfo is not None):
        # VFO가 matplotlib 위에서 그리므로 그냥 저장 가능
        vfo.plot_model()
        try:
            ax = plt.gca()
            ax.view_init(elev=elev, azim=azim)
        except Exception:
            pass
        if path:
            plt.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close()
        return

    # ── Fallback: 간단 와이어프레임 ─────────────────────────────
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 요소 선 그리기
    for et in ops.getEleTags():
        nds = ops.eleNodes(et)
        coords = np.array([ops.nodeCoord(n) for n in nds], dtype=float)
        # 선형/빔: 연속 선
        for k in range(len(coords)-1):
            ax.plot([coords[k,0], coords[k+1,0]],
                    [coords[k,1], coords[k+1,1]],
                    [coords[k,2], coords[k+1,2]],
                    linewidth=lw)
        # 쉘(삼각/사각)은 마지막-처음을 닫아줌
        if len(coords) in (3,4):
            ax.plot([coords[-1,0], coords[0,0]],
                    [coords[-1,1], coords[0,1]],
                    [coords[-1,2], coords[0,2]],
                    linewidth=lw)

    # 노드 산점
    all_nodes = ops.getNodeTags()
    if all_nodes:
        X = [ops.nodeCoord(n)[0] for n in all_nodes]
        Y = [ops.nodeCoord(n)[1] for n in all_nodes]
        Z = [ops.nodeCoord(n)[2] for n in all_nodes]
        ax.scatter(X, Y, Z, s=node_size)

    ax.view_init(elev=elev, azim=azim)
    _set_equal_aspect_3d(ax)
    ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_zlabel('Z (mm)')

    if path:
        plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

