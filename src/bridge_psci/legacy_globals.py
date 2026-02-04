"""Legacy global parameters & section-property calculations.

This module is a **direct lift** of the original notebook's parameter cells.
It intentionally defines many variables at module import time so that the
legacy `Analysis` class and `build_bridge_model()` (also lifted from the notebook)
can reference them as globals.

If you refactor further, the goal is to replace these globals with explicit
`config` objects and pure functions.
"""

import math
import numpy as np

# -------------------------
# Notebook cell: geometry / global constants
# -------------------------
Bridge_width = 12.5 #m
Bridge_skew = 36 # angle

girder_number = 6
Left_Cantilever, Right_Cantilever = 1.05, 1.05
girder_spacing = [2.08]
gravity = 9.81
#
UF = np.array(700)
UT = np.array(170)
UFT = np.array(200)
WH = np.array(1200)
WT = np.array(220)
LFT = np.array(200)
LT = np.array(230)
LF = np.array(680)
girder_H = UT + UFT + WH + LFT + LT
girder_length  = 29600   #거더 길이 (mm)

#####################################################################################################################################
#강연선 프로파일
number_tendon = 4

area_t = 50.27*12
z_coef_list = np.array([1500, 1086, 700, 294])   # 긴장재 끝단에서 하부플랜지로부터의 이격거리 #1, #2, #3, #4 .... 이 순서
z_intercept_list = np.array([200, 80, 80, 80])   # 중앙부에서 하부플랜지와의 이격거리

y_coef_list = np.array([0, 0, 0, 0])   # 
y_intercept_list = np.array([0, 0, -150, 150])   # 

tendon_horizontal_length = girder_length/2 

#PS강연선
Ep = np.array(200000.0)                                    #ps 강연선 탄성계수  (N/mm^2)
Ec = np.array(28896.0)                                         #콘크리트 탄성계수   (N/mm^2)
Ap_N = np.array([50.27*12, 50.27*12, 50.27*12, 50.27*12])                              #ps 강연선 면적 환산계수 곱하지 않은 것  (mm^2)

#덕트
A_duct_N = np.array([50.27*12, 50.27*12, 50.27*12, 50.27*12])                               # - 덕트 면적    (mm^2)
y_duct_N = np.array([1850, 1920, 1920, 1920])                     #상단-하단평균거리 (2000-80=1920) ############################################################################

# -------------------------
# Notebook cell: PSCI section property calculations
# -------------------------
### 교량 및 부재 제원###
#####################################################################################################################################
####단면 계산을 위한 제원이라, Openseespy에서 단면을 그릴 때는 높이 또는 두께에 대한 재계산이 필요함 Ex: 복부 단면은 h3-h2-h4 = 884(1200-60-256)####
# 총 단면

b1 = UF                                        #상부플랜지    (mm)
b2 = (UF-WT)/2                                         #상부 헌치     (mm)  삼각형부분만
b3 = WT                                         #웨브          (mm)
b4 = (LF-WT)/2                                        #하부 헌치     (mm)  삼각형부분만
b5 = LF                                      #하부 플랜지   (mm)

h1 = UT                                       #상부플랜지    (mm)
h2 = UFT                                          #상부 헌치     (mm)
h3 = UFT + WH + LFT                                     #웨브          (mm)
h4 = LFT                                          #하부 헌치     (mm)
h5 = LT                                        #하부 플랜지   (mm)

Ag1 = b1*h1
Ag2 = b2*h2
Ag3 = b3*h3
Ag4 = b4*h4
Ag5 = b5*h5
Ag = Ag1+Ag2+Ag3+Ag4+Ag5                        #총 단면적

yg1 = h1/2
yg2 = h1+h2/3
yg3 = h1+h3/2
yg4 = h1+h3-h4/3
yg5 = h1+h3+h5/2

Qg1 = Ag1*yg1
Qg2 = Ag2*yg2
Qg3 = Ag3*yg3
Qg4 = Ag4*yg4
Qg5 = Ag5*yg5
Qg = Qg1+Qg2+Qg3+Qg4+Qg5                       #총 단면의 단면1차모멘트

yt1 = Qg/Ag                                    #상면에서 총 단면의 중심축까지의 거리

yn_g1 = np.abs(yt1-yg1)                           #상부 플랜지 사각형의 도심에서 중심축까지의 거리
yn_g2 = np.abs(yt1-yg2)                           #상부 헌치 삼각형의 도심에서 중심축까지의 거리
yn_g3 = np.abs(yt1-yg3)                           #웨브 사각형의 도심에서 중심축까지의 거리
yn_g4 = np.abs(yt1-yg4)                           #하부 헌치 삼각형의 도심에서 중심축까지의 거리
yn_g5 = np.abs(yt1-yg5)                           #하부 플랜지 사각형의 도심에서 중심축까지의 거리

Ay2g1 = Ag1*yn_g1**2
Ay2g2 = Ag2*yn_g2**2
Ay2g3 = Ag3*yn_g3**2
Ay2g4 = Ag4*yn_g4**2
Ay2g5 = Ag5*yn_g5**2
Ay2_g_n_g = Ay2g1+Ay2g2+Ay2g3+Ay2g4+Ay2g5      #총 단면의 각 단면적 * 각 단면 도형의 도심에서 중심축까지 거리^2

Io_g1 = b1/12*h1*h1*h1
Io_g2 = b2/36*2*h2*h2*h2
Io_g3 = b3/12*h3 * h3 * h3
Io_g4 = b4/36*2*h4*h4*h4
Io_g5 = b5/12*h5*h5*h5
Io_g =  Io_g1 + Io_g2 + Io_g3 + Io_g4 + Io_g5             #각 단면 도형2 중심축에서의 단면2차모멘트

Ix_g = Io_g+Ay2_g_n_g                           #총 단면 단면2차모멘트

#####################################################################################################################################

Q_duct_N = []
for i in range(len(A_duct_N)):
    Q_duct_N.append(A_duct_N[i] * y_duct_N[i])
Q_duct_N = np.array(Q_duct_N)
Q_duct = np.sum(np.array(Q_duct_N))                           #쉬스관 단면1차모멘트
A_duct = np.sum(np.array(A_duct_N))                          #쉬스관 총 넓이
y_duct = Q_duct/A_duct                           #상면에서 쉬스관 모든 도형의 도심점까지의 거리

#####################################################################################################################################
#콘크리트 순 단면
A_net = Ag-A_duct                                #콘크리트 순면적 ( 왜 더하는가?) 
Q_net = Qg-Q_duct                                #콘크리트 순단면 단면1차모멘트
yt2 = Q_net/A_net                                #상면에서부터 콘크리트 순단면의 도심까지 거리

y_net_P = np.abs(yt2-yt1)                           #총 단면의 도심과 콘크리트 순단면의 도심사이 거리

y_duct_P_N = []
for i in range(len(y_duct_N)):
    y_duct_P_N.append(abs(yt2 - y_duct_N[i]))    #쉬스관 도형의 도심과 콘크리트 순단면의 도심사이 거리
y_duct_P_N = np.array(y_duct_P_N)
Ay2_g_net_P = Ag*y_net_P**2                      #총 단면적 * 총 단면의 도심과 콘크리트 순단면의 도심사이 거리^2

Ay2_duct_N_duct_P_N = []
for i in range(len(y_duct_P_N)):
    Ay2_duct_N_duct_P_N.append(A_duct_N[i]*y_duct_P_N[i]**2)
Ay2_duct_duct_P = np.sum(np.array(Ay2_duct_N_duct_P_N))                           #쉬스관의 각 단면적 * 쉬스관 도형의 각 도심과 콘크리트 순단면의 도심사이 거리^2

Ay2_net = Ay2_g_net_P+Ay2_duct_duct_P                          #총 단면적 * 총 단면의 도심과 콘크리트 순단면의 도심사이 거리^2
                                                               #   - 쉬스관의 각 단면적 * 각 단면 도형의 도심에서 중심축까지 거리^2
Io_net = Ix_g
Ix_net = Io_net+Ay2_net                            #순 단면 단면2차모멘트

#####################################################################################################################################

#####################################################################################################################################
Np = Ep/Ec

Ap = np.sum(np.array(Ap_N))
yp_N = y_duct_N

Qp_N = []
for i in range(len(Ap_N)):
    Qp_N.append(Ap_N[i] * yp_N[i])

Qp = np.sum(np.array(Qp_N))                             #PS강연선 총 단면1차모멘트
yp = Qp/Ap
#####################################################################################################################################
#PS강연선 환산단면
At_p = Ap*Np
At = A_net + At_p
Qt = Q_net+At_p*yp
yt3 = Qt/At

yt_P_N = np.array([abs(yt3 - yp_N[i]) for i in range(len(yp_N))])

Ay2_t_t_P_N = np.array([Ap_N[i]*Np*yt_P_N[i]**2 for i in range(len(yt_P_N))])

y_net_PP = np.abs(yt3-yt2)

Io_t = Ix_net
Ix_t = Io_t + np.sum(np.array(Ay2_t_t_P_N)) + A_net*y_net_PP**2

#####################################################################################################################################
A_t = np.array(At)
B_t = np.array(Qt)
I_n = np.array(Ix_t)

I_n, yt3   ##yt3은 상면에서 중립축까지 거리
