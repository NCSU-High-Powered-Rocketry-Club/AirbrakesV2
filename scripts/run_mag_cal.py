from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from firm_client import FIRMClient


def _fit_ellipsoid_magcal(m: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit ellipsoid in algebraic form:
        x^T A x + b^T x + c = 1
    Returns:
        A (3,3) symmetric
        b (3,)
        c (scalar)
    """
    # m: (N,3)
    x = m[:, 0]
    y = m[:, 1]
    z = m[:, 2]

    # Design matrix for quadratic form:
    # [x^2, y^2, z^2, 2xy, 2xz, 2yz, 2x, 2y, 2z, 1] * p = 1
    D = np.column_stack(
        [
            x * x,
            y * y,
            z * z,
            2 * x * y,
            2 * x * z,
            2 * y * z,
            2 * x,
            2 * y,
            2 * z,
            np.ones_like(x),
        ]
    )

    ones = np.ones((m.shape[0],), dtype=float)

    # Least squares solve: D p ≈ 1
    p, *_ = np.linalg.lstsq(D, ones, rcond=None)

    # Unpack parameters into A, b, c
    A = np.array(
        [
            [p[0], p[3], p[4]],
            [p[3], p[1], p[5]],
            [p[4], p[5], p[2]],
        ],
        dtype=float,
    )
    b = np.array([p[6], p[7], p[8]], dtype=float)
    c = float(p[9])

    # Symmetrize A defensively
    A = 0.5 * (A + A.T)

    return A, b, c


def magcal_style_calibration(mag_uT: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Given raw magnetometer samples in microteslas, returns:
      offset_uT: (3,)
      scale_matrix: (3,3)
    Such that:
      mag_corr = scale_matrix @ (mag_raw - offset_uT)
    and mean(||mag_corr||) ~= mean(||mag_raw||).
    """
    if mag_uT.ndim != 2 or mag_uT.shape[1] != 3:
        raise ValueError("mag_uT must be (N,3).")
    if mag_uT.shape[0] < 20:
        raise ValueError("Need at least ~20 samples; more is better (hundreds+ preferred).")

    # Target radius = mean magnitude of recorded raw vectors (as requested)
    r_target = float(np.mean(np.linalg.norm(mag_uT, axis=1)))

    A, b, c = _fit_ellipsoid_magcal(mag_uT)

    # Compute center (offset) of ellipsoid: center = -0.5 A^{-1} b
    try:
        center = -0.5 * np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        raise RuntimeError("Ellipsoid fit produced singular matrix; collect more diverse data.")

    # Compute scalar to normalize to (x-center)^T W (x-center) = 1
    # s = 1 - c + 0.25 b^T A^{-1} b
    try:
        A_inv_b = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        raise RuntimeError("Ellipsoid normalization failed; collect more diverse data.")

    s = 1.0 - c + 0.25 * float(b.T @ A_inv_b)

    if not np.isfinite(s) or s <= 0:
        raise RuntimeError("Ellipsoid fit normalization invalid; collect more diverse data.")

    W = A / s  # (x-center)^T W (x-center) = 1

    # Ensure W is positive definite (small numerical issues can happen)
    eigvals, eigvecs = np.linalg.eigh(W)
    eps = 1e-12
    eigvals_clamped = np.maximum(eigvals, eps)
    W_pd = eigvecs @ np.diag(eigvals_clamped) @ eigvecs.T

    # Find L such that L^T L = W_pd (Cholesky gives that)
    # If Cholesky fails (rare after clamping), fall back to matrix sqrt via eig.
    try:
        L = np.linalg.cholesky(W_pd)  # lower-triangular: L @ L.T = W_pd
        # We want a matrix M where ||M (x-center)|| = 1 when ellipsoid equation holds.
        # Using L.T gives: (L.T z)^T (L.T z) = z^T (L L.T) z = z^T W z
        M_unit = L.T
    except np.linalg.LinAlgError:
        # Fallback: W_pd = V diag(d) V^T => sqrt(W_pd) = V diag(sqrt(d)) V^T
        sqrtW = eigvecs @ np.diag(np.sqrt(eigvals_clamped)) @ eigvecs.T
        M_unit = sqrtW

    # Scale to requested radius
    scale_matrix = r_target * M_unit

    offset_uT = center
    return offset_uT, scale_matrix


def main() -> None:
    port = "/dev/ttyACM0"  # Update as needed
    baud_rate = 2_000_000

    calib_seconds = 60.0

    mags: list[tuple[float, float, float]] = []

    with FIRMClient(port, baud_rate, timeout=0.2) as client:
        client.get_data_packets(block=True)  # Clear initial packets

        t0 = time.monotonic()
        while client.is_running() and (time.monotonic() - t0) < calib_seconds:
            packets = client.get_data_packets(block=True)
            for packet in packets:
                mx = float(packet.magnetic_field_x_microteslas)
                my = float(packet.magnetic_field_y_microteslas)
                mz = float(packet.magnetic_field_z_microteslas)
                mags.append((mx, my, mz))

                # Keep ONLY the mag print (optional)
                print(f"Mag (uT): x={mx:>8.4f}, y={my:>8.4f}, z={mz:>8.4f}")

    mag_arr = np.asarray(mags, dtype=float)

    offset_uT, scale_matrix = magcal_style_calibration(mag_arr)

    # Results
    np.set_printoptions(precision=8, suppress=True)
    print("\n=== Magnetometer calibration (magcal-style) ===")
    print(f"Samples collected: {mag_arr.shape[0]}")
    print("Offset (uT):")
    print(offset_uT)
    print("\nScale matrix (3x3):")
    print(scale_matrix)

    # Quick sanity check (optional):
    # corrected = (mag_raw - offset) mapped by scale matrix
    corrected = (scale_matrix @ (mag_arr - offset_uT).T).T
    raw_mean = float(np.mean(np.linalg.norm(mag_arr, axis=1)))
    corr_mean = float(np.mean(np.linalg.norm(corrected, axis=1)))
    print(f"\nMean |raw|  (uT): {raw_mean:.6f}")
    print(f"Mean |corr| (uT): {corr_mean:.6f}")


if __name__ == "__main__":
    main()
