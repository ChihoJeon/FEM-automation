# Bridge PSCI (OpenSeesPy) — 엑셀 기반 모델링/해석 패키지 (v3)

이 패키지는 `notebooks/효자교(상행)251118.ipynb`(Jupyter Notebook)로 작성된 **PSCI 교량(OpenSeesPy) 구조해석 코드**를,
**“엑셀 입력 템플릿 → 모델 생성 → 모달(고유치) → 이동하중 동해석”**이 한 번에 실행되도록 패키징/모듈화한 버전입니다.

핵심 목표는 **사람이 엑셀에서 변수만 입력하면**, 코드가 그 값을 읽어 **모델링과 해석을 자동으로 수행**하고 결과를 저장하는 것입니다.

---

## 1) 전체 워크플로우(실행 흐름)

1. **엑셀 템플릿 입력**  
   - 교량 형상/단면(PSCI), 재료, 텐던, 받침(스프링), 모달/동해석 설정을 시트별로 입력
   - `Cases` 시트에서 케이스(case_label)별 override(부분 변경) 정의 가능

2. **모델 빌드**  
   - OpenSeesPy로 PSCI 거더 + 바닥판 + 포장층 + 가로보 + 받침(스프링) 등을 생성
   - 노트북에서 사용하던 태깅(예: 거더별 노드 tag) 규칙을 최대한 유지

3. **모달 해석(고유치/고유진동수 추출)**  
   - `ops.eigen(numEigen)` → `f = sqrt(λ)/(2π)`로 고유진동수 산정
   - 간단한 정적 포인트 하중을 가해 처짐(검증용)도 같이 계산

4. **이동하중 동해석(Transient)**  
   - 차량(기본 6축 트럭) 이동을 노드별 PathSeries 하중 이력으로 생성
   - Newmark 적분 기반 Transient 해석 수행
   - 중앙부(미드스팬) 가속도 응답을 CSV로 저장

---

## 2) 폴더/패키지 구조

(패키지 root 기준)

```
bridge_psci/
├─ notebooks/
│  └─ 효자교(상행)251118.ipynb          # 원본 노트북(추적/검증용)
├─ CELL_MAPPING.md                      # 노트북 셀 → 모듈 매핑 문서
├─ bridge_input_template_v3.xlsx        # v3(멀티시트) 입력 템플릿(예시)
├─ scripts/
│  ├─ make_template.py                  # v3 엑셀 템플릿 생성
│  ├─ run_excel.py                      # 엑셀 기반 “모달 + 동해석” 원클릭 실행
│  ├─ run_modal.py                      # (엑셀 없이) 모달만 실행
│  ├─ run_case.py                       # (엑셀 없이) 동해석만 실행
│  └─ snapshot.py                       # 모델 스냅샷 저장(vfo 사용 가능)
└─ src/bridge_psci/
   ├─ __init__.py
   ├─ defaults_base.py                  # 노트북 기반 기본 파라미터(베이스라인) 딕셔너리
   ├─ config.py                         # 케이스(case1/2/5/6/9) 오버라이드/헬퍼
   ├─ io/
   │  └─ excel_io.py                    # v3 엑셀 템플릿 생성 + 로딩 + 타입 파싱/파생값 계산
   ├─ model/
   │  ├─ builder.py                     # Analysis 클래스 + build_bridge_model(params)
   │  └─ visualization.py               # snapshot_model (vfo / matplotlib)
   ├─ analysis/
   │  ├─ modal.py                       # 모달 + 정적 처짐 검증(run_modal)
   │  └─ moving_load.py                 # 이동하중 동해석(run_moving_load)
   └─ utils/
      └─ plotting.py                    # CSV 플롯 유틸(최소 기능)
```

> 참고: `legacy_globals.py`는 노트북의 “전역 변수/단면 계산 코드”를 **레퍼런스/비교용으로 보존**해 둔 파일입니다.  
> 실제 실행 경로는 `params` 딕셔너리(엑셀 로딩 결과)를 사용하도록 구성되어 있습니다.

---

## 3) 설치/환경

### 필수
- Python 3.9+ (권장: 3.10~3.12)
- `openseespy`
- `numpy`, `pandas`, `matplotlib`, `openpyxl`
- (선택) `vfo` : 모델 스냅샷용(없으면 `--no-vfo`로 실행 가능)

### 설치 예시
```bash
pip install -r requirements.txt
pip install -e .
```

---

## 4) 가장 쉬운 실행: 엑셀 기반 원클릭 실행

### (1) 템플릿 생성(선택)
```bash
python scripts/make_template.py --out bridge_input_template_v3.xlsx
```

### (2) 템플릿 작성
엑셀 파일(`bridge_input_template_v3.xlsx`)을 열고, 각 시트의 **Value** 칸을 채웁니다.

### (3) 실행
```bash
python scripts/run_excel.py --excel bridge_input_template_v3.xlsx --case baseline --out outputs
```

- 결과는 기본적으로 `outputs/<case>/` 폴더에 저장됩니다.

#### 옵션
- `--skip_modal` : 모달 해석 스킵
- `--skip_moving` : 동해석 스킵

---

## 5) 엑셀 템플릿(v3) 시트 설명

엑셀에는 다음 시트들이 있습니다.

- **README**: 템플릿 사용 요약
- **Meta**: 프로젝트 라벨 등 메타 정보(`project_name`, `notes`)
- **Geometry**: 교량 폭/스큐/거더 개수/거더 간격/캔틸레버/길이/중력 등
- **Section**: PSCI 단면 치수(UF, UT, WH, …)  
  - `b1~b5`, `h1~h5` 등 파생값은 **자동 계산(수정 비권장)**
- **Materials**: 거더/바닥판 탄성계수(E) 리스트, 두께 리스트 등
- **Tendon**: 텐던 그룹 수, y/z intercept, Ap 리스트 등
- **Bearings**: 받침(스프링) 설정  
  - `bearing_mode`:
    - `multiplier` : 기본 `Bearing_Stiffness`에 `bearing_multiplier` 배수 적용
    - `table` : `BearingsTable` 시트 값을 그대로 사용
- **Modal**: `numEigen`, `zeta`(감쇠비)
- **Dynamic**: `dt`, `velocity_kmh`(차량 속도) 등
- **Output**: 결과 추출을 위한 레거시 태그(거더3/거더4 시작 tag, 노드 수 등)
- **Advanced**: 위 시트에 포함되지 않은 키들을 “전체 커버리지” 목적으로 나열(필요 시 수정)
- **Cases**: 케이스별 override 테이블  
  - 컬럼: `case_label, key, value, type, description`
- **BearingsTable**: 받침 강성 6자유도 테이블(옵션)

### 타입 입력 규칙(중요)
엑셀 `Type` 컬럼에 따라 값이 파싱됩니다.

- `float`, `int`, `str`, `bool`
- `list[float]`, `list[int]`  
  - **JSON 배열**(`[1,2,3]`) 또는 **콤마 구분**(`1,2,3`) 모두 지원
- `json`  
  - 배열/중첩배열 등 JSON 문자열로 입력(예: `[[...],[...]]`)

---

## 6) 출력물(현재 기본)

### (1) 모달 결과
- `outputs/<case>/(<case>)modal_results.json`  
  - 고유치(eigenvalues), 고유진동수(Hz), 정적 처짐(mm) 등이 저장됩니다.

### (2) 이동하중 동해석 결과
- `outputs/<case>/(<case>)mid_accel_g3.csv`
- `outputs/<case>/(<case>)mid_accel_g4.csv`

(거더 3/4 중앙부 노드의 Z방향 가속도 응답을 기록합니다.)

### (3) 모델 스냅샷(선택)
```bash
python scripts/snapshot.py --case baseline --out outputs/snapshots/model.png
```

---

## 7) (엑셀 없이) 빠른 테스트용 실행 스크립트

### 모달만 실행
```bash
python scripts/run_modal.py --case baseline
```

### 동해석만 실행(내장 case)
```bash
python scripts/run_case.py --case case2 --out outputs/responses
```

---

## 8) 케이스(case) 운영 방식

- `config.py`에는 노트북에서 사용하던 대표 케이스(`baseline, case1, case2, case5, case6, case9`)가 포함되어 있습니다.
- **권장 방식(최종 목표)**: 케이스는 `Cases` 시트에서 override로 운영  
  - 예: `case5`에서 `E_girder1` 일부만 감소, `bearing_multiplier`만 변경 등

---

## 9) 단위/모델링 주의사항

- 본 코드는 노트북의 단위 체계를 그대로 계승합니다.  
  예) 길이: mm 혼용, 강성/하중: N 기반, 탄성계수: MPa 등  
- OpenSees 해석은 **단위 일관성**이 핵심이므로, 엑셀 입력 시 단위 컬럼(Unit)을 반드시 확인하세요.
- 노드/요소 tag 규칙은 레거시(노트북) 구조를 유지합니다.  
  (`Output` 시트의 `girder3_start_tag`, `girder_n_nodes` 등을 변경하면 결과 추출 로직이 함께 영향을 받습니다.)

---

## 10) 확장/개발 가이드(추천)

### (1) 엑셀 입력 항목 확장
- 새 파라미터를 추가하려면:
  1) `defaults_base.py` 또는 `config._default_params()`에 기본값 추가
  2) `excel_io.create_excel_template()`에서 해당 키를 적절한 시트에 추가(또는 `Advanced` 시트로 자동 노출 활용)
  3) `builder.py / modal.py / moving_load.py`에서 `params[...]`로 참조

### (2) 해석 기능 추가
- 모듈 위치 권장:
  - 모달/정적 검증: `analysis/modal.py`
  - 동해석/이동하중: `analysis/moving_load.py`
  - 후처리: `utils/plotting.py` 또는 신규 `post/` 모듈

### (3) 원본 노트북과의 추적성
- `CELL_MAPPING.md`를 통해 “노트북 셀 → 현재 모듈 함수/파일” 관계를 확인할 수 있습니다.

---

## 문의/다음 단계(추천)

원한다면 다음을 바로 추가로 진행할 수 있습니다.

- **엑셀 템플릿을 더 ‘사람 친화적’으로 개선**  
  (예: 드롭다운/데이터 검증, 단위 자동 변환, 필수값 누락 체크, 시트별 입력 가이드 강화)
- **차량 모델/축하중/축간거리의 엑셀 입력화**  
  (현재는 moving_load 모듈 기본값 기반)
- **결과 정리 자동화**  
  (케이스 다중 실행 → 결과 폴더 정리 → 요약 CSV/그림 자동 생성)

