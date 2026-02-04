"""Bridge model builder (OpenSeesPy) — packaged from Jupyter notebook.

This module builds a PSCI bridge model, then (optionally) is used by downstream modal/dynamic analysis.

Key refactor vs notebook:
- No module-level mutable globals are required to *configure* the model.
- All configuration is provided via a `params` dict (typically loaded from an Excel template).
- The legacy notebook code is preserved as much as possible; only minimal edits were made to
  replace global-variable dependencies with `self.params` and `params[...]`.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

try:
    import openseespy.opensees as ops  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    ops = None  # type: ignore
    _OPENSEESPY_IMPORT_ERROR = e


try:  # optional
    import vfo.vfo as vfo  # type: ignore
except Exception:  # pragma: no cover
    vfo = None

plt.switch_backend('Agg')  # non-interactive backend


@dataclass
class BuiltModel:
    """Return object for a built OpenSees model."""
    analysis: Any
    params: Dict[str, Any]
    ctx: Dict[str, Any]

class Analysis():
    def __init__(self, length,  width, nums_girder, skew, params: dict | None = None):
        self.params = params or {}
        # Adopted units: N and mm
        self.kilo = 1e3
        self.milli = 1e-3
        self.N = 1
        self.mm = 1
        self.m = 1000*self.mm
        self.m3 = self.m * self.m * self.m
        self.mm2 = self.mm ** 2
        self.mm3 = self.mm ** 3
        self.mm4 = self.mm ** 4
        self.kN = self.kilo * self.N
        self.MPa = self.N / self.mm2
        self.GPa = self.kilo * self.MPa
        self.transftype = "Linear"
        self.nums_girder = nums_girder
        self.width = width * self.m
        self.skew = skew
        self.L = length * self.m

    def girder(self, girder_number, Ec, Pe,  spacing):
        name = 'girder' + str(girder_number) + '_centroid' # 교축 방향 라인 별로 이름 정의.
        # ---- parameters from Excel/config (avoid module-level globals) ----
        p = self.params
        h1 = float(p.get('h1', 0.0)); h2 = float(p.get('h2', 0.0)); h3 = float(p.get('h3', 0.0)); h4 = float(p.get('h4', 0.0)); h5 = float(p.get('h5', 0.0))
        b1 = float(p.get('b1', 0.0)); b2 = float(p.get('b2', 0.0)); b3 = float(p.get('b3', 0.0)); b4 = float(p.get('b4', 0.0)); b5 = float(p.get('b5', 0.0))
        girder_H = float(p.get('girder_H', 0.0))
        tendon_horizontal_length = float(p.get('tendon_horizontal_length', p.get('girder_length', 0.0)))
        y_intercept_list = list(p.get('y_intercept_list', []))
        z_intercept_list = list(p.get('z_intercept_list', []))
        Ap_N = list(p.get('Ap_N', []))
        Ag = float(p.get('Ag', 0.0))
        ####################  Concrete dimension   ########################################
        L = self.L  # girder design length (mm)
        division = int(L /self.m * 5)     ######## 길이 기준(Element)
        imax = division + 1   # element + 1 (노드 기준)

        x_loc = -1 * spacing * np.tan(math.radians(self.skew)) * self.m          #교축방향
        y_loc = spacing * self.m                                                 #교축직각
        centroid = yt3 #  거더 상연부터 도심까지 거리
                            #z1             y1         z2             y2       z3                 y3         z4              y4
        section1 = [    int(-h1),    int(-b1/2),   int(0),        int(-b1/2), int(0),        int(b1/2), int(-h1),        int(b1/2) ]           #100(h1), 1000(b1)
        section2 = [  int(-h1-h2),   int(-b3/2),  int(-h1),      int(-b1/2), int(-h1),     int(b1/2),  int(-h1-h2),   int(b3/2) ]           #100, (200, 400)
        section3 = [ int(-h1-h3+h4), int(-b3/2), int(-h1-h2),    int(-b3/2), int(-h1-h2),   int(b3/2),  int(-h1-h3+h4),  int(b3/2) ]         #600, 200
        section4 = [   int(-h1-h3),  int(-b5/2), int(-h1-h3+h4), int(-b3/2), int(-h1-h3+h4), int(b3/2), int(-h1-h3),    int(b5/2)]        #200, (200, 450)
        section5 = [ int(-h1-h3-h5), int(-b5/2),   int(-h1-h3),   int(-b5/2), int(-h1-h3),   int(b5/2),int(-h1-h3-h5),    int(b5/2)]        #150, 450
        sections = [section1, section2, section3, section4, section5]
        Acol = Ag * self.mm2
        ####################  Concrete MATERIAL   ########################################
        IDconcU = 1000 + girder_number       # unconfined cover concrete
        ops.uniaxialMaterial("Elastic", IDconcU , Ec)         # concrete
        
        #################### Tendon Material     ########################################
        IDstrand = 10 +  girder_number               # strand
        IDstrand_initial =  100 + girder_number      # strand
        Pe = Pe * self.MPa
        Fpy = 1364 * self.MPa                # strand yield stress
        Es = Ep * self.MPa
        Bps = 0.0236               # strain-hardening ratio
        ops.uniaxialMaterial("Steel01", IDstrand, Fpy, Es, Bps)             # Tendon
        ops.uniaxialMaterial("InitStressMaterial", IDstrand_initial, IDstrand, Pe)                 # Initial Stress for PS

        ####################   Section-property  ########################################
        J = ((b1*h1**3) + (b3 * h3**3) +  (b5 * h5**3))/3
        v = 0.17
        G = Ec / 2 / (1+v)
        GJ = G * J

        transfArgs=[0,0,1]  #local z방향 벡터 -- 로컬 z축이 전역 y축과 일치 
        ops.geomTransf(self.transftype, 1000 + girder_number, *transfArgs)  # 좌표변환을 정의함. 
       ####################   Node   ########################################
    
        mass_ratio = [0.0, 0.0, 1.0]  
        rho = 2.5e-9 # N·s²/mm⁴ 질량밀도 단위로 작성  # kg/mm³ → 2.5e-6  (콘크리트 밀도는 보통 2500 kg/m^3) 1 kg = 0.001 N·s²/mm
        muBeam = rho * Acol #N·s²/mm2
        nodes={}
        
        mass_before = []
        mass_after = []
        
        for j in range(0, imax): 
            ops.node(int(1000 * girder_number+j+1), x_loc+L/division*j,  y_loc, -centroid)
            mass_before.append(rho * Acol * L/division / 2)
            mass_after.append(rho * Acol * L/division / 2)
            
        mass_before[-1] = 0
        mass_after[0] = 0
        mass_all = np.array(mass_before) + np.array(mass_after)
        mass_all = mass_all.tolist()
        
        for j in range(0, imax):
            ops.mass(int(1000 * girder_number+j+1),0,  0, mass_all[j])  # ops.mass는 kg단위가 아닌, N*s^2/mm 단위로 넣어줘야함. 따라서. kg -> 0.001을 곱해줌) 
        
       # 기존
        # nodes[name] = np.c_[np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>=1000*girder_number],
        #           np.asarray([(ops.nodeCoord(int(t))) for t in np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>=1000*girder_number]])]

        # 수정: 거더별 노드 태그 하한/상한 범위 필터
        tags = np.asarray(ops.getNodeTags(), dtype=int)

        # 이미 위에서 계산된 imax = division + 1 사용
        lower = 1000 * girder_number + 1
        upper = 1000 * girder_number + imax  # 포함 상한

        sel = (tags >= lower) & (tags <= upper)
        gid_tags = np.sort(tags[sel])
        coords = np.array([ops.nodeCoord(int(t)) for t in gid_tags], dtype=float)
        nodes[name] = np.column_stack([gid_tags, coords])  # shape: (N, 1+3)

        nfY1, nfZ1 = 2,5
        nfY2, nfZ2 = 1,2
        nfY3, nfZ3 = 3,1
        nfY4, nfZ4 = 2,3
        nfY5, nfZ5 = 1,3

        #실제 무게 반영해야함(모델로부터 오면 좋을 듯)
        class Tendon():
            def __init__(self):
                pass
            def tendon_profile_vertical(self, x ,coeffiecient, intercept):
                x = np.array(x)
                z = coeffiecient* x **2 +  intercept
                return z
            def tendon_profile_horizontal(self, x ,coeffiecient, intercept):
                x = np.array(x)
                z = coeffiecient* x **2 +  intercept
                return z

        quads = ['quad1', 'quad2', 'quad3', 'quad4', 'quad5']  # 단면 수 fiber
        a_coef = (z_coef_list-z_intercept_list) / tendon_horizontal_length / tendon_horizontal_length
        b_coef = (y_coef_list-y_intercept_list) / tendon_horizontal_length / tendon_horizontal_length
        
        for i in range(0, imax):
            a = L * i / (imax - 1)
            ops.section('Fiber', int(nodes[name][i][0]), '-GJ', GJ)

            sections1 = [
            (section1, nfY1, nfZ1, 'quad1'),
            (section2, nfY2, nfZ2, 'quad2'),
            (section3, nfY3, nfZ3, 'quad3'),
            (section4, nfY4, nfZ4, 'quad4'),
            (section5, nfY5, nfZ5, 'quad5')]

            for sec, nfY, nfZ, quad in sections1:
                ops.patch('quad', IDconcU, nfY, nfZ, *sec)
                for k in np.arange(1, 1+number_tendon).tolist():
                    z = Tendon().tendon_profile_vertical(a - L / 2 , a_coef[k-1], z_intercept_list[k-1]) - girder_H
                    if sec[0] < z < sec[2]: #patch내에 있는지 확인( sec[0],[2]는 z값임)
                        y = Tendon().tendon_profile_horizontal(a - L / 2, b_coef[k-1], y_intercept_list[k-1])
                        ops.layer('straight', IDstrand_initial, 1, Ap_N[k-1], z, y, z, y)
                    else:
                        y = Tendon().tendon_profile_horizontal(a - L / 2, b_coef[k-1], y_intercept_list[k-1])
                        ops.layer('straight', IDstrand_initial, 1, 0, z, y, z, y)

        beam_el={}
        beam_el[name]=np.array([],dtype=int)
        numIntgrPts = 5
        
        for i in range(0, division, 1):
            ops.beamIntegration('Legendre', int(nodes[name][i][0]), int(nodes[name][i][0]), numIntgrPts)  # 단면을 부여하고 요소 사이를 어떻게 적분할지를 결정하는 부분, 현재 5개의 적분점에 전부 동일한 단면 부여
            if i < imax+1:
                ops.element('dispBeamColumn', int(nodes[name][i][0]), int(nodes[name][i][0]), int(nodes[name][i+1][0]), 
                    1000+girder_number, int(nodes[name][i][0])) #노드번호랑 요소 번호랑 동일 요소번호 = 노드-1 
            beam_el[name]=np.append(beam_el[name], int(nodes[name][i][0]))
            
        return nodes, beam_el

    def pavement(self, pave_number, tSlab, Ec_slab, bridge_width_spacings, slab_thickness_spacing_cumsum):
        name = 'deck'
        L = self.L  # girder design length
        #bridge_width_spacings = np.arange(0, 12.5, 1, dtype = np.float32)-ex) (0,1,2,3,4,5,6,7,8,9,10,11,12)
        slab_spacings = np.unique(np.round(np.sort(np.hstack([bridge_width_spacings, 
            slab_thickness_spacing_cumsum])), 3))
        #array([ 0.  ,  1.  ,  1.25,  2.  ,  3.  ,  3.25,  4.  ,  5.  ,  5.25, 6.  ,  7.  ,  7.25,  8.  ,  9.  ,  9.25, 10.  , 11.  , 11.25, 12., 12.5 ])
        slab_found_indices = np.where(np.isin(slab_spacings, slab_thickness_spacing_cumsum))[0]

        # cumsum이 존재하는 배열을 추출 -> [ 0,  2,  5,  8, 11, 14, 17, 19] -거더갯수+2(캔틸레버) 
        division = int(L / self.m * 5)
        imax = division + 1   # element + 1  --149
        spacing = slab_spacings * 1000
        
        name_list = []
        for i in range(len(spacing)):
            name_list.append('pavement' + str(i))

        nodes = {}
        for k in range(len(slab_found_indices)-1):
            if k != len(slab_found_indices)-2:
                slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1]) #np.arrange(0,4) = [0,1,2,3] -> 슬라이싱 
                spacing_list = slab_spacings[slicing_list]
            else:
                slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1]+1)
                spacing_list = slab_spacings[slicing_list]
                
            for i in range(len(spacing_list)):
                for j in range(division+1):
                    ops.node(int(pave_number * 100000 + 1000*slicing_list[i]+j+1),                     
                             float(-1 *  1000*spacing_list[i] * np.tan(math.radians(self.skew))+L/division*j),                
                             1000*float(spacing_list[i]),
                             tSlab[0]/2 + 220 ) # 바닥판 두께를 더해줘야함.
                    
                    # 아래는 opensees에서 정의된 node를 딕셔너리 변수에 할당
                nodes[name_list[slicing_list[i]]]=np.c_[np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>= pave_number * 100000 + 1000*slicing_list[i]],
                                        np.asarray([(ops.nodeCoord(int(t))) for t in np.asarray(ops.getNodeTags())
                                                 [np.asarray(ops.getNodeTags())>= pave_number * 100000 + 1000*slicing_list[i]]])]

        v = 0.1
        shell_el={}
        shell_el[name]=np.array([], dtype=int)

        #실제 무게 반영해야함(모델로부터 오면 좋을 듯)
        rho = 2.0e-9  # N·s²/mm^4
        tSlab = np.array(tSlab)/2 + np.array(tSlab)/2
        for k in range(len(slab_found_indices)-1):  # 두께 변화구간 
            slabSection = pave_number * 100 + 1 + k
            tSlabx = tSlab[0]
            Ec_slabx = Ec_slab[0]
            ops.section('ElasticMembranePlateSection', slabSection, Ec_slabx, v, tSlabx, 0) # 0대신 rho를 넣으면 질량이 중복으로 들어감. 해당 단면요소는 자동으로 질량을 노드에 부여하는 기능을 가짐. 현재 내코드로 작성 

            slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1])
            spacing_list = slab_spacings[slicing_list]
            for i in range(0, len(spacing_list)):
                for j in range(1, imax, 1):
                    #element('ShellMITC4', eleTag, *eleNodes, secTag)
                    #a list of four element nodes in counter-clockwise order
                    ops.element('ShellNLDKGQ', int(nodes[name_list[slicing_list[i]]][j-1,0]),
                               *(np.asarray([nodes[name_list[slicing_list[i]]][j-1][0],
                                             nodes[name_list[slicing_list[i]]][j][0],
                                             nodes[name_list[slicing_list[i]+1]][j][0],
                                             nodes[name_list[slicing_list[i]+1]][j-1][0]], dtype=(int))).tolist(), slabSection)
                    #shell_el[name] = np.append(shell_el[name], int(nodes[name_list[i]][j-1,0]))
                    
        volume_list = []  # shell element별 부피 구하기
        for k in range(len(slab_found_indices)-1):
            tSlabx = tSlab[0]
            slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1])
            spacing_list = slab_spacings[slicing_list]
            for i in range(0, len(spacing_list)):
                for j in range(1, imax, 1):
                    volume_list.append(tSlabx * (nodes[name_list[slicing_list[i]]][j][1] - nodes[name_list[slicing_list[i]]][j-1][1])*
                                             (nodes[name_list[slicing_list[i]+1]][j][2] - nodes[name_list[slicing_list[i]]][j][2]))              
        volume_list1 = np.array(volume_list).reshape(len(spacing)-1, -1) * rho
        
        volume_node_list = []
        for i in range(0, len(volume_list1)):
            a = np.insert(np.array(volume_list1[i]), 0, 0) / 4
            b = np.insert(np.array(volume_list1[i]), len(volume_list1[i]), 0) / 4
            volume_node_list.append(a + b)  
        volume_node_list = np.array(volume_node_list)
        
        volume_node_list1 = []
        for i in range(0, len(volume_node_list.T)):
            a = np.insert(np.array(volume_node_list.T[i]), 0, 0)
            b = np.insert(np.array(volume_node_list.T[i]), len(volume_node_list.T[i]), 0)
            volume_node_list1.append(a+b)
        volume_node_list1 =  np.array(volume_node_list1).T
        for i in range(len(volume_node_list1)):
            for j in range(len(volume_node_list1[i])):
                ops.mass(int(nodes['pavement'+str(i)][j][0]), 0, 0, volume_node_list1[i][j])

        return nodes
    
    def deck(self, deck_number, tSlab, Ec_slab, bridge_width_spacings, slab_thickness_spacing_cumsum):
        name = 'deck'
        L = self.L  # girder design length
        #bridge_width_spacings = np.arange(0, 12.5, 1, dtype = np.float32)-ex) (0,1,2,3,4,5,6,7,8,9,10,11,12)
        slab_spacings = np.unique(np.round(np.sort(np.hstack([bridge_width_spacings, slab_thickness_spacing_cumsum])), 3))
        #array([ 0.  ,  1.  ,  1.25,  2.  ,  3.  ,  3.25,  4.  ,  5.  ,  5.25, 6.  ,  7.  ,  7.25,  8.  ,  9.  ,  9.25, 10.  , 11.  , 11.25, 12., 12.5 ])
        slab_found_indices = np.where(np.isin(slab_spacings, slab_thickness_spacing_cumsum))[0]
        # cumsum이 존재하는 배열을 추출 -> [ 0,  2,  5,  8, 11, 14, 17, 19] -거더갯수+2(캔틸레버) 
        division = int(L / self.m * 5)
        imax = division + 1   # element + 1  --149
        spacing = slab_spacings * 1000
        
        name_list = []
        for i in range(len(spacing)):
            name_list.append('slab' + str(i))

        nodes = {}
        for k in range(len(slab_found_indices)-1):
            if k != len(slab_found_indices)-2:
                slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1]) #np.arrange(0,4) = [0,1,2,3] -> 슬라이싱 
                spacing_list = slab_spacings[slicing_list]
            else:
                slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1]+1)
                spacing_list = slab_spacings[slicing_list]
                
            for i in range(len(spacing_list)):
                for j in range(division+1):
                    ops.node(int(deck_number * 100000 + 1000*slicing_list[i]+j+1),                     
                             float(-1 *  1000*spacing_list[i] * np.tan(math.radians(self.skew))+L/division*j),                
                             1000*float(spacing_list[i]),
                             tSlab[k]/2)
                    
                    # 아래는 opensees에서 정의된 node를 딕셔너리 변수에 할당
                nodes[name_list[slicing_list[i]]]=np.c_[np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>= deck_number * 100000 + 1000*slicing_list[i]],
                                        np.asarray([(ops.nodeCoord(int(t))) for t in np.asarray(ops.getNodeTags())
                                                 [np.asarray(ops.getNodeTags())>= deck_number * 100000 + 1000*slicing_list[i]]])]

        v = 0.17
        shell_el={}
        shell_el[name]=np.array([], dtype=int)

        #실제 무게 반영해야함(모델로부터 오면 좋을 듯)
        rho = 2.5e-9  # N·s²/mm^4
        tSlab = np.array(tSlab[:-1])/2 + np.array(tSlab[1:])/2
        for k in range(len(slab_found_indices)-1):  # 두께 변화구간 
            slabSection = deck_number * 100 + 1 + k
            tSlabx = tSlab[k]
            Ec_slabx = Ec_slab[k]
            ops.section('ElasticMembranePlateSection', slabSection, Ec_slabx, v, tSlabx, 0) # 0대신 rho를 넣으면 질량이 중복으로 들어감. 해당 단면요소는 자동으로 질량을 노드에 부여하는 기능을 가짐. 현재 내코드로 작성 

            slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1])
            spacing_list = slab_spacings[slicing_list]
            for i in range(0, len(spacing_list)):
                for j in range(1, imax, 1):
                    #element('ShellMITC4', eleTag, *eleNodes, secTag)
                    #a list of four element nodes in counter-clockwise order
                    ops.element('ShellNLDKGQ', int(nodes[name_list[slicing_list[i]]][j-1,0]),
                               *(np.asarray([nodes[name_list[slicing_list[i]]][j-1][0],
                                             nodes[name_list[slicing_list[i]]][j][0],
                                             nodes[name_list[slicing_list[i]+1]][j][0],
                                             nodes[name_list[slicing_list[i]+1]][j-1][0]], dtype=(int))).tolist(), slabSection)
                    #shell_el[name] = np.append(shell_el[name], int(nodes[name_list[i]][j-1,0]))
                    
        volume_list = []  # shell element별 부피 구하기
        for k in range(len(slab_found_indices)-1):
            tSlabx = tSlab[k]
            slicing_list = np.arange(slab_found_indices[k], slab_found_indices[k+1])
            spacing_list = slab_spacings[slicing_list]
            for i in range(0, len(spacing_list)):
                for j in range(1, imax, 1):
                    volume_list.append(tSlabx * (nodes[name_list[slicing_list[i]]][j][1] - nodes[name_list[slicing_list[i]]][j-1][1])*
                                             (nodes[name_list[slicing_list[i]+1]][j][2] - nodes[name_list[slicing_list[i]]][j][2]))              
        volume_list1 = np.array(volume_list).reshape(len(spacing)-1, -1) * rho
        
        volume_node_list = []
        for i in range(0, len(volume_list1)):
            a = np.insert(np.array(volume_list1[i]), 0, 0) / 4
            b = np.insert(np.array(volume_list1[i]), len(volume_list1[i]), 0) / 4
            volume_node_list.append(a + b)  
        volume_node_list = np.array(volume_node_list)
        
        volume_node_list1 = []
        for i in range(0, len(volume_node_list.T)):
            a = np.insert(np.array(volume_node_list.T[i]), 0, 0)
            b = np.insert(np.array(volume_node_list.T[i]), len(volume_node_list.T[i]), 0)
            volume_node_list1.append(a+b)
        volume_node_list1 =  np.array(volume_node_list1).T
        for i in range(len(volume_node_list1)):
            for j in range(len(volume_node_list1[i])):
                ops.mass(int(nodes['slab'+str(i)][j][0]), 0, 0, volume_node_list1[i][j])

        return nodes
    
    def barrier(self, number,  spacing, Ec, deck_thickness, pave_thick,  height, width):
        L = self.L  # span
        division = int(L / self.m * 5)
        imax = division + 1   # element + 1

        #plate model 기준... 메쉬 크기를 어떻게 하는게 좋을까??
        y_loc = spacing * self.m
        name = 'guard' + str(number)
        deck_thickness = np.array(deck_thickness)
        pave_thick = np.array(pave_thick[0]);
        height =  height * self.m
        width = width * self.m
        width1 = np.abs(width) 
        A_guard = width1 * height
        x_loc = -(y_loc + width/2) * np.tan(math.radians(self.skew))

        nodes={}
        rho = 2.5e-9 # N·s²/mm^4
        mass_before = []
        mass_after = []
        
        for j in range(imax):
            ops.node(1000000 + 10000*number+j+1, x_loc+L/division*j, y_loc + width/2, height / 2 + deck_thickness + pave_thick)
            mass_before.append(rho * A_guard * L/division / 2)
            mass_after.append(rho * A_guard * L/division / 2)
                     
        mass_before[-1] = 0
        mass_after[0] = 0
        mass_all = np.array(mass_before) + np.array(mass_after)
        mass_all = mass_all.tolist()
        
        for j in range(0, imax):
            ops.mass(int(1000000 + 10000*number+j+1),0,  0, mass_all[j])

        # 아래는 opensees에서 정의된 node를 딕셔너리 변수에 할당
        nodes[name]=np.c_[np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>=1000000 + 10000*number],
            np.asarray([(ops.nodeCoord(int(t))) for t in np.asarray(ops.getNodeTags())[np.asarray(ops.getNodeTags())>=1000000 + 10000*number]])]

        transfArgs = [0,0,1]
        ops.geomTransf(self.transftype,10 + number, *transfArgs)
        numIntgrPts = 5
        beam_el = {}
        beam_el[name]=np.array([],dtype=int)

        A_guard = width1 * height
        Iz_guard = width1 * height * height* height / 12
        Iy_guard =  height * width1 * width1 * width1 / 12
        J_guard = Iz_guard+Iy_guard
        v = 0.2
        guardSection = 20 + number
        fc = -24 * self.MPa                    #fck가 34 MPa
        #Ec = 8500*(-fc)**(1/3)
        G = Ec / 2 / (1+v)
        ops.section('Elastic', guardSection, Ec, A_guard, Iz_guard, Iy_guard, G, J_guard)
         #실제 무게 반영해야함(모델로부터 오면 좋을 듯)
 
        for i in range(2, imax+1, 1):
            ops.beamIntegration('Legendre', int(nodes[name][i-2][0]), guardSection, numIntgrPts)
            ops.element('dispBeamColumn', int(nodes[name][i-2][0]), int(nodes[name][i-2][0]), int(nodes[name][i-1][0]),
                        10 + number, int(nodes[name][i-2][0]))
            beam_el[name]=np.append(beam_el[name],int(nodes[name][i-2][0]))

        return nodes, beam_el

    def diaphragm(self, bridge_number,  number, node, Ec, nums_girder):
        
        nodes= np.array([])

        length = girder_spacing[0] / math.cos(math.radians(self.skew)) * self.m # 가로보 길이 
        height = 1.795 * self.m
        thickness = 0.30 * self.m
        theta = math.radians(self.skew)
        
        transfArgs= [0, -math.sin(theta), math.cos(theta)]
        numIntgrPts = 5

        A_diaphragm = height * thickness      
        Iz_diaphragm = thickness * height *height* height  / 12
        Iy_diaphragm =  height * thickness * thickness * thickness / 12
        J_diaphragm = Iz_diaphragm + Iy_diaphragm
        v = 0.17

        fc = -24 * self.MPa
        rho = 2.5e-9
        
        mass_before = []
        mass_after = []
        for i in range(1, 1 + nums_girder):
            ops.node(bridge_number * 100 + 10 *number + i, ops.nodeCoord(node[i-1])[0], ops.nodeCoord(node[i-1])[1], -height/2)
            nodes = np.append(nodes, int(bridge_number * 100 + 10 * number + i))
            mass_before.append(rho * A_diaphragm * length / 2)
            mass_after.append(rho * A_diaphragm * length / 2)
            
        mass_before[-1] = 0
        mass_after[0] = 0
        mass_all = np.array(mass_before) + np.array(mass_after)
        mass_all = mass_all.tolist()   
        
        for i in range(len(nodes)):
            ops.mass(int(nodes[i].tolist()), 0,  0, mass_all[i])

        for i in range(1, nums_girder, 1):
            name = 'diaphragm' + str(bridge_number * 100 + 10 *number + i)
            ops.geomTransf(self.transftype, bridge_number * 100 + 10 *number + i, *transfArgs)
            
            beam_el = {}
            beam_el[name]=np.array([],dtype=int)
            Ec1 =  Ec[i-1]
            G = Ec1 / 2 / (1+v)
            diaphragm_Section = bridge_number * 100 + 10 * number + i
            ops.section('Elastic', diaphragm_Section, Ec1, A_diaphragm, Iz_diaphragm, Iy_diaphragm, G, J_diaphragm)
            ops.beamIntegration('Legendre', bridge_number * 100 + 10 *number + i, diaphragm_Section, numIntgrPts)
            ops.element('dispBeamColumn', bridge_number * 100 + 10 *number + i, bridge_number * 100 + 10 *number + i, bridge_number * 100 + 10 *number + i + 1, bridge_number * 100 + 10 *number + i, bridge_number * 100 + 10 *number + i)
            beam_el[name]=np.append(beam_el[name], bridge_number * 100 + 10 *number + i)
            
        return nodes

    def spring(self, spring_number, node, girder_height, *stiffness):
        stiffness = np.array(stiffness)[0] # 첫번째 행만 꺼냄 (하나의 받침정보들 )
        h = girder_height * self.mm            # girder height
        IDhspring_axis = spring_number * 100 - spring_number
        IDhspring_transverse = spring_number * 1000 - spring_number
        IDvspring = spring_number * 10000

        ID_spring_rot1 = spring_number * 100000 + spring_number
        ID_spring_rot2 = spring_number * 1000000 + spring_number
        ID_spring_rot3 = spring_number * 10000000 + spring_number

        kh_axis = stiffness[0] * self.kN / self.m    # 7549
        kh_transverse = stiffness[1] * self.kN / self.m    ##7549
        kv = stiffness[2]  * self.kN / self.m       # 659700

        k_rot1 = 0 * self.kN / self.m      ##비틀림
        k_rot2 = 0 * self.kN / self.m        ##수직방향 회전
        k_rot3 = 0 * self.kN / self.m     # 횡방향 회전

        ops.uniaxialMaterial("Elastic", IDvspring, kv)         # spring (z)
        ops.uniaxialMaterial("Elastic", IDhspring_axis, kh_axis)         # spring (x)
        ops.uniaxialMaterial("Elastic", IDhspring_transverse, kh_transverse)         # spring (y)

        ops.uniaxialMaterial("Elastic", ID_spring_rot1, k_rot1)         # spring
        ops.uniaxialMaterial("Elastic", ID_spring_rot2, k_rot2)         # spring
        ops.uniaxialMaterial("Elastic", ID_spring_rot3, k_rot3)         # spring

        support_node = 10000000 + spring_number
        spring_node = 100000000 + spring_number

        ####아래는 지점를 위한 노드
        ops.node(support_node,
                ops.nodeCoord(node)[0], ops.nodeCoord(node)[1], -int(h))
        ####아래는 지점 스프링 요소를 위한 노드
        ops.node(spring_node,
                ops.nodeCoord(node)[0], ops.nodeCoord(node)[1], -int(h))

        ops.element('zeroLength', support_node ,         spring_node, support_node, '-mat', IDhspring_axis,        '-dir', 1)     ## 교축임(가정)
        ops.element('zeroLength', support_node + 100,    spring_node, support_node, '-mat', IDhspring_transverse,  '-dir', 2)  # 'dir'에서 1이 교축인지 2가 교축인지 찾아야함(2가 없어도 해석이 돌아감)
        ops.element('zeroLength', support_node + 200,    spring_node, support_node, '-mat', IDvspring,             '-dir', 3)   #수직
        ops.element('zeroLength', support_node + 300,    spring_node, support_node, '-mat', ID_spring_rot1,        '-dir', 4)   #회전
        ops.element('zeroLength', support_node + 400,    spring_node, support_node, '-mat', ID_spring_rot2,        '-dir', 5)   #회전
        ops.element('zeroLength', support_node + 500,    spring_node, support_node, '-mat', ID_spring_rot3,        '-dir', 6)   #회전

        return [support_node, spring_node]


    def static_analysis_load(self, pattern_tag, node, point_z, moment_x, moment_y, moment_z):
        ops.wipeAnalysis()
        ops.timeSeries("Constant", pattern_tag) #시간에 따라 하중이 일정함. 
        ops.pattern("Plain", pattern_tag, pattern_tag)
        #필요시 for loop 넣어야함
        ops.load(node, 0, 0,  point_z, moment_x,  moment_y, moment_z)
                                    #교츅
        ops.constraints('Transformation')
        ops.numberer('RCM')
        #ops.system('ProfileSPD')
        ops.system('UmfPack')
        ops.test('NormDispIncr', 1.0e-6, 5, 0, 2) #수렴판정 조건 - 변위증분의 노름을 기준으로 하며 허용오차 1e-8, 최대반복횟수 7
        ops.algorithm('Newton')
        ops.integrator('LoadControl', 1)
        ops.analysis('Static')
        ops.analyze(1)
        ops.loadConst('-time', 0.0)

    def dynamic_analysis(self, pattern_tag):     
        ops.wipeAnalysis()
        input_parameters = (70.0, 500., 2.)
        pf, sfac_a, tkt = input_parameters
        t0 = 0. 
        tk = 1.
        Tp = 1/pf
        P0 = 15000.
        dt = 0.002
        n_steps = int((tk-t0)/dt)

        ops.wipeAnalysis()
        tsTag = pattern_tag

        ops.timeSeries('Trig', tsTag, t0, tk, Tp, '-factor', P0)
        ops.pattern('Plain', pattern_tag, tsTag)
        ops.load(4075,  0, 0,  1, 0, 0, 0)
        ops.constraints('Transformation')
        ops.numberer('RCM')
        ops.test('NormDispIncr', 1.0e-3, 3, 1)  
        ops.algorithm('Newton')
        ops.system('UmfPack')
        #ops.system('ProfileSPD')
        ops.integrator('Newmark', 0.5, 0.25)
        ops.analysis('Transient')

def build_bridge_model(params: Dict[str, Any]) -> 'BuiltModel':
    if ops is None:  # pragma: no cover
        raise ImportError('openseespy is required to build the model') from _OPENSEESPY_IMPORT_ERROR

    p = params
    ctx: Dict[str, Any] = {}  # replaces notebook's ctx[...] scratchpad
    # --- unpack commonly used base/material parameters ---
    Bridge_width = float(p['Bridge_width'])
    Bridge_skew = float(p.get('Bridge_skew', 0.0))
    girder_number = int(p['girder_number'])
    girder_length = float(p['girder_length'])
    girder_spacing = float(p['girder_spacing'])
    Left_Cantilever = float(p.get('Left_Cantilever', 0.0))
    Right_Cantilever = float(p.get('Right_Cantilever', 0.0))
    gravity = float(p.get('gravity', -9.81))
    # arrays / lists used by notebook code
    E_girder1 = list(p.get('E_girder1', []))
    E_girder2 = list(p.get('E_girder2', []))
    E_deck1 = list(p.get('E_deck1', []))
    E_deck2 = list(p.get('E_deck2', []))
    thickness1 = list(p.get('thickness1', []))
    thickness2 = list(p.get('thickness2', []))
    Bearing_Stiffness = np.array(p.get('Bearing_Stiffness'))
    PE = float(p.get('PE', 600))
    pave_thick = list(p.get('pave_thick', [80]))
    diaphragm1_Ec = list(p.get('diaphragm1_Ec', []))
    diaphragm2_Ec = list(p.get('diaphragm2_Ec', []))
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 6)

    nums_girder = girder_number
    Bridge1 = Analysis(girder_length / 1000, Bridge_width, nums_girder=nums_girder, skew=Bridge_skew, params=p)

    Left_Cantil, Right_Cantil = Left_Cantilever, Right_Cantilever
    spacing = girder_spacing
    girder_spacings = np.hstack([Left_Cantil, spacing*(nums_girder - 1)])
    girder_spacing_cumsum = np.round(np.cumsum(girder_spacings), 3)
    slab_thickness_spacing = np.hstack([0.0, girder_spacings, Right_Cantilever])
    slab_thickness_spacing_cumsum = np.round(np.cumsum(slab_thickness_spacing), 3)
    bridge_width_spacings = np.arange(0, Bridge_width, 1.0, dtype=np.float32)
    slab_spacings = np.unique(np.round(np.sort(np.hstack([bridge_width_spacings, slab_thickness_spacing_cumsum])), 3))
    girder_found_indices = np.where(np.isin(slab_spacings, girder_spacing_cumsum))[0]
    slab_found_indices = np.where(np.isin(slab_spacings, slab_thickness_spacing_cumsum))[0]

    for i in range(1, nums_girder+1):
        ctx['girder'+str(i)] = Bridge1.girder(i, E_girder1[i-1], PE, girder_spacing_cumsum[i-1])

    deck1 = Bridge1.deck(1, thickness1, E_deck1, bridge_width_spacings, slab_thickness_spacing_cumsum)
    barrier1 = Bridge1.barrier(1, slab_spacings[0], 25000, thickness1[0], pave_thick, 0.3, 3.88)

    node_number = []
    for i in range(1, girder_number+1):
        node_number.append(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0])
    node_array = np.array(node_number, dtype=np.int16).T

    diaphragm_start1 = Bridge1.diaphragm(1, 1, node_array[0].tolist(), diaphragm1_Ec, nums_girder)
    diaphragm_end1 = Bridge1.diaphragm(1, 2, node_array[-1].tolist(), diaphragm2_Ec, nums_girder)

    crossbeam_list = [5000.0, 10000.0, 15000, 20000, 25000]
    x_coords_array = []
    division = int(girder_length / 1000 * 5)
    imax = division + 1
    for j in range(imax):
        x_coords_array.append(girder_length/division*j)

    crossbeam_index = np.where(np.isin(x_coords_array, crossbeam_list))
    for idx, tag in enumerate(crossbeam_index[0]):
        ctx[f'crossbeam{idx+1}_1'] = Bridge1.diaphragm(1, 3+idx, node_array[tag].tolist(), diaphragm2_Ec, nums_girder)

    for i in range(1, nums_girder+1):
        ctx['spring'+str(i*2-1)] = Bridge1.spring(i*2-1, int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][0]), girder_H, Bearing_Stiffness[i-1])
        ctx['spring'+str(i*2)] = Bridge1.spring(i*2, int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][-1]), girder_H, Bearing_Stiffness[nums_girder+i-1])

    imax = len(girder1[0]['girder1_centroid'])
    for i in range(nums_girder):
        for j in range(imax):
            ops.rigidLink('beam',
                int(ctx['girder'+str(i+1)][0]['girder'+str(i+1)+'_centroid'].T[0][j]),
                int(deck1['slab'+str(girder_found_indices[i])].T[0][j]))

    for j in range(imax):
        ops.rigidLink('beam', int(deck1['slab0'].T[0][j]), int(barrier1[0]['guard1'][j][0]))

    for i in range(1, nums_girder+1):
        ops.fix(ctx['spring'+str(i*2-1)][0], 1,1,1,1,1,1)
        ops.fix(ctx['spring'+str(i*2)][0], 1,1,1,1,1,1)
        ops.rigidLink('beam',
            int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][0]),
            ctx['spring'+str(i*2-1)][1])
        ops.rigidLink('beam',
            int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][-1]),
            ctx['spring'+str(i*2)][1])

    for i in range(1, girder_number+1):
        ops.rigidLink('beam', int(diaphragm_start1[i-1]), int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][0]))
        ops.rigidLink('beam', int(diaphragm_end1[i-1]), int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][-1]))
        for idx in range(len(crossbeam_index[0])):
            ops.rigidLink('beam',
                int(ctx['girder'+str(i)][0]['girder'+str(i)+'_centroid'].T[0][crossbeam_index[0][idx]]),
                int(ctx[f'crossbeam{idx+1}_1'][i-1]))

    Bridge1 = Analysis(girder_length / 1000, Bridge_width, nums_girder=nums_girder, skew=Bridge_skew, params=p)
    pave_E = [2500]
    pavement = Bridge1.pavement(3, pave_thick, pave_E, bridge_width_spacings, slab_thickness_spacing_cumsum)

    for i in range(len(deck1.keys())):
        for j in range(imax):
            ops.rigidLink('beam',
                int(deck1['slab'+str(i)].T[0][j]),
                int(pavement['pavement'+str(i)].T[0][j]))

    print("✅ Bridge model successfully built.")
    return BuiltModel(analysis=Bridge1, params=p, ctx=ctx)
