# Notebook → package mapping
원본 노트북(`효자교(상행)251118.ipynb`)의 셀을 기준으로, 현재 생성한 패키지 구조로 옮긴 매핑입니다.
## 셀 매핑
| Cell | 원본 역할(요약) | 패키지 위치 | 비고 |
|---:|---|---|---|
| 0 | Imports + matplotlib backend/magic | `model/builder.py (imports cleaned)` | Jupyter magic(%matplotlib) 제거 |
| 1 | plot_acceleration_with_min() | `utils/plotting.py` |  |
| 2 | snapshot_model() + 3D aspect helper | `model/visualization.py` | vfo 사용 가능 |
| 3 | 교량/모델 전역 파라미터(기하/배치 등) | `legacy_globals.py` | legacy 글로벌 변수 유지 |
| 4 | PSCI 단면/물성 산정(단면2차모멘트 등) | `legacy_globals.py` | legacy 글로벌 변수 유지 |
| 5 | Analysis class (OpenSees 래퍼) | `model/builder.py` | 추후 config 주입형으로 리팩터 권장 |
| 6 | 케이스용 E/thickness/bearing 등 파라미터 | `config.py` | cell7 기준으로 defaults 구성 |
| 7 | defaults 파라미터 + bearing stiffness + helper | `config.py` | bearing stiffness 기본 multiplier=0.3 |
| 8 | build_bridge_model() 함수 | `model/builder.py` | legacy builder로 유지, 반환값 Bridge1 |
| 9 | (중복) 전역 실행형 모델 구축 코드 | `(미이관)` | 패키지에서는 함수형(builder)로 대체 |
| 10 | snapshot_model() 실행 | `scripts/snapshot.py` |  |
| 11 | build_bridge_model() 실행 | `scripts/*` | CLI에서 실행하도록 변경 |
| 12 | 정적 처짐 체크 + 고유진동수 | `analysis/modal.py` | run_modal() |
| 13 | (빈/보조) | `(미이관)` |  |
| 14 | (빈/보조) | `(미이관)` |  |
| 15 | (보조 실행) | `(미이관)` |  |
| 16 | (고유진동수 결과 배열) | `(미이관)` |  |
| 17 | 동해석(before update) 1 | `analysis/moving_load.py` | run_moving_load()로 통합 |
| 18 | 동해석(before update) 2 | `analysis/moving_load.py` | 동일 |
| 19 | Case1 동해석 | `analysis/moving_load.py + config.py` | case_label로 출력 파일 구분 |
| 20 | Case2 동해석(베어링 multiplier 변경) | `analysis/moving_load.py + config.py` | CASE_OVERRIDES['case2'] |
| 21 | Case5 (거더1 E 감소 0.7) | `analysis/moving_load.py + config.py` | CASE_OVERRIDES['case5'] |
| 22 | Case6 (거더1 E 감소 0.5) | `analysis/moving_load.py + config.py` | CASE_OVERRIDES['case6'] |
| 23 | Case9 (deck E 감소 0.7) | `analysis/moving_load.py + config.py` | CASE_OVERRIDES['case9'] |

## 지금 상태에서의 실행 방법
프로젝트 루트(`bridge_psci/`)에서:
```bash
pip install -e .
python scripts/run_modal.py --case baseline
python scripts/run_case.py --case case2 --out outputs/responses
python scripts/snapshot.py --case baseline --out outputs/snapshots/model.png
```

## 다음 리팩터 우선순위(추천)
1) `legacy_globals.py`의 전역 변수 의존 제거 → `BridgeConfig` dataclass/YAML로 치환
2) `build_bridge_model()`이 생성한 주요 태그(거더/슬래브/지점) 레지스트리를 `BuiltModel`로 반환
3) 케이스 관리: `config.py`의 dict override → 명확한 케이스 스펙 파일(예: `cases/case2.yaml`)
4) recorders/outputs 표준화 + 결과 postprocess 모듈화
