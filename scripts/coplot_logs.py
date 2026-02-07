#!/usr/bin/env python3
"""
coplot_two_logs.py

Interactive Plotly coplotter for two FIRM CSV log formats, aligned by start of motor burn state.

It plots (from both logs, if present):
  - vertical position (old: est_position_z_meters, new: current_altitude)
  - vertical velocity (old: est_velocity_z_meters_per_s, new: vertical_velocity)
  - predicted apogee (predicted_apogee)

Alignment:
  - Finds the first row where state_letter == --motor-state in each file and sets that as t=0.
  - If the motor state is not found, falls back to the first state change, then to first timestamp.

New-format "estimated packets":
  - Keeps only rows where at least one of (current_altitude, vertical_velocity, predicted_apogee)
    is present (non-empty / non-NaN).

Usage:
  python coplot_two_logs.py old.csv new.csv --motor-state M
  python coplot_two_logs.py old.csv new.csv --motor-state B --out out.html
  python coplot_two_logs.py old.csv new.csv --no-state-shading
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go


STATE_COLORS = {
    "S": "rgba(0, 102, 204, 0.15)",
    "M": "rgba(0, 153, 0, 0.15)",
    "C": "rgba(204, 0, 0, 0.15)",
    "F": "rgba(153, 0, 153, 0.15)",
    "L": "rgba(255, 153, 0, 0.15)",
}


def _to_float_series(s: pd.Series) -> pd.Series:
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
    if time_col not in df.columns:
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


def load_old_format(path: Path, motor_state: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "timestamp_seconds" not in df.columns:
        raise SystemExit(f"{path.name}: missing required column 'timestamp_seconds'")

    t0 = find_motor_burn_start_time(df, "timestamp_seconds", motor_state)
    if t0 is None:
        raise SystemExit(f"{path.name}: could not determine motor burn start time")

    df = df.copy()
    df["t"] = _to_float_series(df["timestamp_seconds"]) - float(t0)

    # Normalize columns to common names (alt/vel/apogee)
    if "est_position_z_meters" in df.columns:
        df["alt"] = _to_float_series(df["est_position_z_meters"])
    else:
        df["alt"] = np.nan

    if "est_velocity_z_meters_per_s" in df.columns:
        df["vel"] = _to_float_series(df["est_velocity_z_meters_per_s"])
    else:
        df["vel"] = np.nan

    if "predicted_apogee" in df.columns:
        df["apogee"] = _to_float_series(df["predicted_apogee"])
    else:
        df["apogee"] = np.nan

    return df


def load_new_format(path: Path, motor_state: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "timestamp" not in df.columns:
        raise SystemExit(f"{path.name}: missing required column 'timestamp' (ns)")

    df = df.copy()

    # Keep only "estimated-ish" packets: rows with at least one key estimated field present
    alt = _to_float_series(df["current_altitude"]) if "current_altitude" in df.columns else pd.Series(np.nan, index=df.index)
    vel = _to_float_series(df["vertical_velocity"]) if "vertical_velocity" in df.columns else pd.Series(np.nan, index=df.index)
    apo = _to_float_series(df["predicted_apogee"]) if "predicted_apogee" in df.columns else pd.Series(np.nan, index=df.index)

    keep = alt.notna() | vel.notna() | apo.notna()
    df = df.loc[keep].copy()

    if df.empty:
        raise SystemExit(f"{path.name}: after filtering, no estimated rows remained")

    t0_ns = find_motor_burn_start_time(df, "timestamp", motor_state)
    if t0_ns is None:
        raise SystemExit(f"{path.name}: could not determine motor burn start time")

    ts_ns = _to_int_series(df["timestamp"]).astype("float64")
    df["t"] = (ts_ns - float(t0_ns)) / 1e9

    # Normalize columns to common names (alt/vel/apogee)
    df["alt"] = _to_float_series(df["current_altitude"]) if "current_altitude" in df.columns else np.nan
    df["vel"] = _to_float_series(df["vertical_velocity"]) if "vertical_velocity" in df.columns else np.nan
    df["apogee"] = _to_float_series(df["predicted_apogee"]) if "predicted_apogee" in df.columns else np.nan

    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("old_csv", type=Path, help="Old-format log CSV")
    ap.add_argument("new_csv", type=Path, help="New-format log CSV")
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

    if not args.old_csv.exists():
        raise SystemExit(f"File not found: {args.old_csv}")
    if not args.new_csv.exists():
        raise SystemExit(f"File not found: {args.new_csv}")

    df_old = load_old_format(args.old_csv, args.motor_state)
    df_new = load_new_format(args.new_csv, args.motor_state)

    fig = go.Figure()

    # Altitude
    fig.add_trace(
        go.Scatter(
            x=df_old["t"],
            y=df_old["alt"],
            mode="lines",
            name=f"Old: altitude (est_position_z_meters)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_new["t"],
            y=df_new["alt"],
            mode="lines",
            name=f"New: altitude (current_altitude)",
        )
    )

    # Vertical velocity
    fig.add_trace(
        go.Scatter(
            x=df_old["t"],
            y=df_old["vel"],
            mode="lines",
            name=f"Old: vertical velocity (est_velocity_z_meters_per_s)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_new["t"],
            y=df_new["vel"],
            mode="lines",
            name=f"New: vertical velocity (vertical_velocity)",
        )
    )

    # Predicted apogee
    fig.add_trace(
        go.Scatter(
            x=df_old["t"],
            y=df_old["apogee"],
            mode="lines",
            name=f"Old: predicted apogee",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_new["t"],
            y=df_new["apogee"],
            mode="lines",
            name=f"New: predicted apogee",
        )
    )

    # State shading (do both; old and new may differ)
    if not args.no_state_shading:
        add_state_regions(fig, df_old, time_col="t")
        add_state_regions(fig, df_new, time_col="t")

    fig.update_layout(
        title=f"Coplots aligned to motor burn start (t=0)<br><sup>{args.old_csv.name} vs {args.new_csv.name}</sup>",
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
