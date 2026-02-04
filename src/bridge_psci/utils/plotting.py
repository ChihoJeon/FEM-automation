"""Plotting utilities extracted from the original notebook."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

def plot_acceleration_with_min(csv_path, index=None, n_channels=6):
    """
    시간-변위 그래프를 그리고 선택된 센서(index)의 최소값과 최대값(hline) 및 수치를 표시하는 함수
    -------------------------------------------------------------------
    Parameters
    ----------
    csv_path : str
        CSV 파일 경로
    index : int or None
        특정 센서(열) 인덱스 (0부터 시작). None이면 모든 센서를 그림.
    n_channels : int, default=6
        변위 데이터 열 개수 (시간열 다음에 있는 센서 개수)
    """
    # ============================================================
    # 1️⃣ 데이터 불러오기
    # ============================================================
    df = pd.read_csv(csv_path)

    # ============================================================
    # 2️⃣ 시간열 + 변위 데이터 추출
    # ============================================================
    time = df.iloc[:, 0].values
    disp_data = df.iloc[:, 1+6:n_channels+1+6]  # 변위 데이터 (예: 7~12열)

    # ============================================================
    # 3️⃣ 특정 인덱스 선택
    # ============================================================
    if index is not None:
        if index < 0 or index >= disp_data.shape[1]:
            raise ValueError(f"index={index} is out of range (0 ~ {disp_data.shape[1]-1})")
        disp_data = disp_data.iloc[:, [index]]

    # ============================================================
    # 4️⃣ 그래프 시각화
    # ============================================================
    plt.figure(figsize=(12, 8))

    for col in disp_data.columns:
        y = disp_data[col].values
        min_val = y.min()
        max_val = y.max()
        min_time = time[y.argmin()]
        max_time = time[y.argmax()]

        # 변위 그래프
        plt.plot(time, y, lw=0.9, label=str(col))

        # 최소값 표시
        plt.axhline(min_val, color='red', linestyle='--', alpha=0.6)
        plt.text(
            time[-1]*0.98,
            min_val,
            f"{col} min: {min_val:.4f}",
            color='red',
            fontsize=12,
            ha='right', va='bottom'
        )

        # 최대값 표시
        plt.axhline(max_val, color='blue', linestyle='--', alpha=0.6)
        plt.text(
            time[-1]*0.98,
            max_val,
            f"{col} max: {max_val:.4f}",
            color='blue',
            fontsize=12,
            ha='right', va='bottom'
        )

    plt.xlabel("Time [sec]")
    plt.ylabel("Displacement")
    title_suffix = f" (Sensor {index})" if index is not None else " (All Sensors)"
    plt.title(f"Time–Displacement History with Min/Max Values{title_suffix}")
    plt.legend(loc="upper right", ncol=2)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    # ============================================================
    # 5️⃣ 최소값 / 최대값 요약 출력
    # ============================================================
    print("📊 최소값 및 최대값 요약")
    for col in disp_data.columns:
        y = disp_data[col].values
        print(f"{col:10s}: min = {y.min():.6f} at t = {time[y.argmin()]:.3f} sec")
        print(f"{'':10s}  max = {y.max():.6f} at t = {time[y.argmax()]:.3f} sec\n")

