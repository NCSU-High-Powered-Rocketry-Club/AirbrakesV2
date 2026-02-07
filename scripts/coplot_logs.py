#!/usr/bin/env python3
"""
coplot_two_logs.py

Interactive Plotly coplotter for two FIRM CSV log formats, aligned by start of motor burn state.

Plots (from both logs):
  - vertical position (firm: est_position_z_meters, imu: current_altitude)
  - vertical velocity (firm: est_velocity_z_meters_per_s, imu: vertical_velocity)
  - vertical acceleration (firm: est_acceleration_z_gs -> m/s^2, imu: vertical_acceleration)
  - predicted apogee (predicted_apogee)

Alignment:
  - Finds the first row where state_letter == --motor-state in each file and sets that as t=0.
  - If motor state not found, falls back to first state change, then to first timestamp.

imu-format "estimated packets":
  - Keeps rows where at least one of (current_altitude, vertical_velocity, vertical_acceleration, predicted_apogee)
    is present.

Fixes for "values exist but not plotted":
  - Sort by time
  - connectgaps=True to avoid line breaks from occasional NaNs
  - Optionally collapse duplicate timestamps (median)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go


G0 = 9.80665  # m/s^2 per g

STATE_COLORS = {
    "S": "rgba(0, 102, 204, 0.15)",
    "M": "rgba(0, 153, 0, 0.15)",
    "C": "rgba(204, 0, 0, 0.15)",
    "F": "rgba(153, 0, 153, 0.15)",
    "L": "rgba(255, 153, 0, 0.15)",
}


def _to_float_series(s: pd.Series) -> pd.Series:
    # Handles blanks/strings safely
    return pd.to_numeric(s, errors="coerce")


def _to_int_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def find_motor_burn_start_time(
    df: pd.DataFrame,
    time_col: str,
    motor_state: str,
    state_col: str = "state_letter",
) -> Optional[float]:
    """
    Returns the timestamp (same units as time_col) for the first row where state_letter == motor_state.
    Fallbacks:
      1) first state change from the initial state
      2) first timestamp
    """
    if time_col not in df.columns or df.empty:
        return None

    t = _to_float_series(df[time_col])

    if state_col in df.columns:
        s = df[state_col].astype(str)

        m = (s == motor_state)
        if m.any():
            v = t[m].iloc[0]
            return float(v) if pd.notna(v) else None

        initial = s.iloc[0]
        ch = (s != initial)
        if ch.any():
            v = t[ch].iloc[0]
            return float(v) if pd.notna(v) else None

    v0 = t.iloc[0]
    return float(v0) if pd.notna(v0) else None


def add_state_regions(fig: go.Figure, df: pd.DataFrame, time_col: str = "t") -> None:
    """Adds vertical shaded regions for runs of the same state_letter."""
    if "state_letter" not in df.columns or time_col not in df.columns or df.empty:
        return

    s = df["state_letter"].astype(str)
    change_idx = s.ne(s.shift(fill_value=s.iloc[0])).to_numpy().nonzero()[0]

    for i, start in enumerate(change_idx):
        end = change_idx[i + 1] if i + 1 < len(change_idx) else len(df)
        state = s.iloc[start]
        if state not in STATE_COLORS:
            continue
        x0 = df[time_col].iloc[start]
        x1 = df[time_col].iloc[end - 1]
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=STATE_COLORS[state],
            line_width=0,
            layer="below",
        )


def _sort_and_dedupe(df: pd.DataFrame, time_col: str = "t") -> pd.DataFrame:
    """Sort by time and collapse duplicate timestamps (median) to keep lines continuous."""
    if df.empty or time_col not in df.columns:
        return df

    df = df.sort_values(time_col).reset_index(drop=True)

    # If there are duplicate timestamps, collapse them to one row per t
    if df[time_col].duplicated().any():
        # Aggregate numeric columns by median; keep first state_letter in that bin
        agg = {}
        for c in df.columns:
            if c == "state_letter":
                agg[c] = "first"
            elif c == time_col:
                continue
            else:
                # median for numeric, otherwise first
                agg[c] = "median"
        df = (
            df.groupby(time_col, as_index=False)
              .agg(agg)
              .sort_values(time_col)
              .reset_index(drop=True)
        )

    return df


def load_firm_format(path: Path, motor_state: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "timestamp_seconds" not in df.columns:
        raise SystemExit(f"{path.name}: missing required column 'timestamp_seconds'")

    t0 = find_motor_burn_start_time(df, "timestamp_seconds", motor_state)
    if t0 is None:
        raise SystemExit(f"{path.name}: could not determine motor burn start time")

    df = df.copy()
    df["t"] = _to_float_series(df["timestamp_seconds"]) - float(t0)

    # Normalize columns
    df["alt"] = _to_float_series(df["est_position_z_meters"]) if "est_position_z_meters" in df.columns else np.nan
    df["vel"] = _to_float_series(df["est_velocity_z_meters_per_s"]) if "est_velocity_z_meters_per_s" in df.columns else np.nan
    df["apogee"] = _to_float_series(df["predicted_apogee"]) if "predicted_apogee" in df.columns else np.nan

    # Vertical acceleration: convert g -> m/s^2 for comparability
    if "est_acceleration_z_gs" in df.columns:
        df["acc"] = _to_float_series(df["est_acceleration_z_gs"]) * G0
    else:
        df["acc"] = np.nan

    df = _sort_and_dedupe(df, "t")
    return df


def load_imu_format(path: Path, motor_state: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "timestamp" not in df.columns:
        raise SystemExit(f"{path.name}: missing required column 'timestamp' (ns)")

    df = df.copy()

    # Build candidate estimated-series fields
    alt = _to_float_series(df["current_altitude"]) if "current_altitude" in df.columns else pd.Series(np.nan, index=df.index)
    vel = _to_float_series(df["vertical_velocity"]) if "vertical_velocity" in df.columns else pd.Series(np.nan, index=df.index)
    acc = _to_float_series(df["vertical_acceleration"]) if "vertical_acceleration" in df.columns else pd.Series(np.nan, index=df.index)
    apo = _to_float_series(df["predicted_apogee"]) if "predicted_apogee" in df.columns else pd.Series(np.nan, index=df.index)

    # Keep only rows that look like "estimated packets"
    keep = alt.notna() | vel.notna() | acc.notna() | apo.notna()
    df = df.loc[keep].copy()

    if df.empty:
        raise SystemExit(f"{path.name}: after filtering, no estimated rows remained")

    t0_ns = find_motor_burn_start_time(df, "timestamp", motor_state)
    if t0_ns is None:
        raise SystemExit(f"{path.name}: could not determine motor burn start time")

    ts_ns = _to_int_series(df["timestamp"]).astype("float64")
    df["t"] = (ts_ns - float(t0_ns)) / 1e9

    # Normalize columns
    df["alt"] = _to_float_series(df["current_altitude"]) if "current_altitude" in df.columns else np.nan
    df["vel"] = _to_float_series(df["vertical_velocity"]) if "vertical_velocity" in df.columns else np.nan
    df["acc"] = _to_float_series(df["vertical_acceleration"]) if "vertical_acceleration" in df.columns else np.nan
    df["apogee"] = _to_float_series(df["predicted_apogee"]) if "predicted_apogee" in df.columns else np.nan

    df = _sort_and_dedupe(df, "t")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("firm_csv", type=Path, help="firm-format log CSV")
    ap.add_argument("imu_csv", type=Path, help="imu-format log CSV")
    ap.add_argument(
        "--motor-state",
        default="M",
        help="State letter for motor burn start (default: M). If missing, falls back to first state change.",
    )
    ap.add_argument(
        "--no-state-shading",
        action="store_true",
        help="Disable shaded regions for state_letter",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output HTML path. If omitted, opens in browser via Plotly default.",
    )
    args = ap.parse_args()

    if not args.firm_csv.exists():
        raise SystemExit(f"File not found: {args.firm_csv}")
    if not args.imu_csv.exists():
        raise SystemExit(f"File not found: {args.imu_csv}")

    df_firm = load_firm_format(args.firm_csv, args.motor_state)
    df_imu = load_imu_format(args.imu_csv, args.motor_state)

    fig = go.Figure()

    def add_line(x, y, name):
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=name,
                connectgaps=True,  # key fix for coast-phase visual gaps
            )
        )

    # Altitude
    add_line(df_firm["t"], df_firm["alt"], "firm: altitude (est_position_z_meters)")
    add_line(df_imu["t"], df_imu["alt"], "imu: altitude (current_altitude)")

    # Vertical velocity
    add_line(df_firm["t"], df_firm["vel"], "firm: vertical velocity (est_velocity_z_meters_per_s)")
    add_line(df_imu["t"], df_imu["vel"], "imu: vertical velocity (vertical_velocity)")

    # Vertical acceleration
    add_line(df_firm["t"], df_firm["acc"], "firm: vertical acceleration (est_acceleration_z_gs → m/s²)")
    add_line(df_imu["t"], df_imu["acc"], "imu: vertical acceleration (vertical_acceleration, m/s²)")

    # Predicted apogee
    add_line(df_firm["t"], df_firm["apogee"], "firm: predicted apogee")
    add_line(df_imu["t"], df_imu["apogee"], "imu: predicted apogee")

    # Optional state shading (both logs)
    if not args.no_state_shading:
        add_state_regions(fig, df_firm, time_col="t")
        add_state_regions(fig, df_imu, time_col="t")

    fig.update_layout(
        title=f"Coplots aligned to motor burn start (t=0)<br><sup>{args.firm_csv.name} vs {args.imu_csv.name}</sup>",
        xaxis_title="Time since motor burn start (s)",
        yaxis_title="Value",
        hovermode="x unified",
        template="plotly_white",
        legend_title="Traces",
    )

    if args.out is not None:
        fig.write_html(args.out, include_plotlyjs="cdn")
        print(f"Wrote: {args.out}")
    else:
        fig.show()


if __name__ == "__main__":
    main()
