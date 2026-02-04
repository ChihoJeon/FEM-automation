"""Base (geometry/section/tendon) defaults extracted from the original notebook globals.

This module is intentionally free of OpenSees imports and *does not* expose module-level
mutable globals used by the solver.

Edit strategy
-------------
- Keep these as a *baseline* starting point.
- Prefer overriding them via the Excel template (recommended) or programmatic overrides.

Generated automatically from legacy notebook globals.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

DEFAULT_BASE_PARAMS: Dict[str, Any] = {'Bridge_width': 12.5, 'Bridge_skew': 36, 'girder_number': 6, 'Left_Cantilever': 1.05, 'Right_Cantilever': 1.05, 'girder_spacing': [2.08], 'gravity': 9.81, 'UF': 700, 'UT': 170, 'UFT': 200, 'WH': 1200, 'WT': 220, 'LFT': 200, 'LT': 230, 'LF': 680, 'girder_H': 2000, 'girder_length': 29600, 'number_tendon': 4, 'area_t': 603.24, 'z_coef_list': [1500, 1086, 700, 294], 'z_intercept_list': [200, 80, 80, 80], 'y_coef_list': [0, 0, 0, 0], 'y_intercept_list': [0, 0, -150, 150], 'tendon_horizontal_length': 14800.0, 'Ep': 200000.0, 'Ec': 28896.0, 'Ap_N': [603.24, 603.24, 603.24, 603.24], 'A_duct_N': [603.24, 603.24, 603.24, 603.24], 'y_duct_N': [1850, 1920, 1920, 1920], 'b1': 700, 'b2': 240.0, 'b3': 220, 'b4': 230.0, 'b5': 680, 'h1': 170, 'h2': 200, 'h3': 1600, 'h4': 200, 'h5': 230, 'Ag1': 119000, 'Ag2': 48000.0, 'Ag3': 352000, 'Ag4': 46000.0, 'Ag5': 156400, 'Ag': 721400.0, 'yg1': 85.0, 'yg2': 236.66666666666669, 'yg3': 970.0, 'yg4': 1703.3333333333333, 'yg5': 1885.0, 'Qg1': 10115000.0, 'Qg2': 11360000.0, 'Qg3': 341440000.0, 'Qg4': 78353333.33333333, 'Qg5': 294814000.0, 'Qg': 736082333.3333333, 'yt1': 1020.3525552167082, 'yn_g1': 935.3525552167082, 'yn_g2': 783.6858885500415, 'yn_g3': 50.3525552167082, 'yn_g4': 682.9807781166251, 'yn_g5': 864.6474447832918, 'Ay2g1': 104111243903.5006, 'Ay2g2': 29479851451.798462, 'Ay2g3': 892453695.53178, 'Ay2g4': 21457286190.73237, 'Ay2g5': 116927017869.67111, 'Ay2_g_n_g': 272867853111.2343, 'Io_g1': 286591666.6666667, 'Io_g2': 106666666.66666667, 'Io_g3': 75093333333.33333, 'Io_g4': 102222222.22222222, 'Io_g5': 689463333.3333333, 'Io_g': 76278277222.22221, 'Ix_g': 349146130333.45654, 'Q_duct_N': [1115994.0, 1158220.8, 1158220.8, 1158220.8], 'i': 3, 'Q_duct': 4590656.399999999, 'A_duct': 2412.96, 'y_duct': 1902.4999999999998, 'A_net': 718987.04, 'Q_net': 731491676.9333333, 'yt2': 1017.3920199358993, 'y_net_P': 2.9605352808089265, 'y_duct_P_N': [832.6079800641007, 902.6079800641007, 902.6079800641007, 902.6079800641007], 'Ay2_g_net_P': 6322904.46402684, 'Ay2_duct_N_duct_P_N': [418187713.8768844, 491460331.18202597, 491460331.18202597, 491460331.18202597], 'Ay2_duct_duct_P': 1892568707.4229622, 'Ay2_net': 1898891611.886989, 'Io_net': 349146130333.45654, 'Ix_net': 351045021945.3435, 'Np': 6.921373200442968, 'Ap': 2412.96, 'yp_N': [1850, 1920, 1920, 1920], 'Qp_N': [1115994.0, 1158220.8, 1158220.8, 1158220.8], 'Qp': 4590656.399999999, 'yp': 1902.4999999999998, 'At_p': 16700.996677740863, 'At': 735688.0366777409, 'Qt': 763265323.1127353, 'yt3': 1037.485027702135, 'yt_P_N': [812.5149722978649, 882.5149722978649, 882.5149722978649, 882.5149722978649], 'Ay2_t_t_P_N': [2756418419.1915464, 3251820484.9754267, 3251820484.9754267, 3251820484.9754267], 'y_net_PP': 20.093007766235814, 'Io_t': 351045021945.3435, 'Ix_t': 363847177710.1606, 'A_t': 735688.0366777409, 'B_t': 763265323.1127353, 'I_n': 363847177710.1606}

def get_default_base_params() -> Dict[str, Any]:
    """Return a deep-copied baseline base-parameter dict."""
    return deepcopy(DEFAULT_BASE_PARAMS)
