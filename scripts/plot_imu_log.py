#!/usr/bin/env python3
"""
plot_firm_log.py

Interactive Plotly viewer for FIRM CSV logs.
Supports mixed raw/estimation logs by filtering for estimation packets.

Usage:
  python plot_firm_log.py path/to/log.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go

# Updated to match the new CSV format headers
DEFAULT_TRACES = [
    # (column_name, pretty_label)
    ("current_altitude", "Altitude (m)"),
    ("vertical_velocity", "Vertical Velocity (m/s)"),
    ("vertical_acceleration", "Vertical Accel (m/s²)"),
    ("predicted_apogee", "Predicted Apogee (m)"),
]

STATE_COLORS = {
    "S": "rgba(0, 102, 204, 0.15)",   # Setup / Standby
    "M": "rgba(0, 153, 0, 0.15)",     # Motor Burn
    "C": "rgba(204, 0, 0, 0.15)",     # Coast
    "F": "rgba(153, 0, 153, 0.15)",   # Freefall / Descent
    "L": "rgba(255, 153, 0, 0.15)",   # Landed
}


def existing_traces(df: pd.DataFrame, traces: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    out = []
    for col, label in traces:
        if col in df.columns:
            out.append((col, label))
    return out


def add_state_regions(fig: go.Figure, df: pd.DataFrame, time_col: str = "t") -> None:
    """
    Adds vertical shaded regions for runs of the same state_letter.
    """
    if "state_letter" not in df.columns:
        return

    s = df["state_letter"].astype(str)
    # Change points where state differs from previous row
    change_idx = s.ne(s.shift(fill_value=s.iloc[0])).to_numpy().nonzero()[0]

    # Build segments [start_idx, end_idx)
    for i, start in enumerate(change_idx):
        end = change_idx[i + 1] if i + 1 < len(change_idx) else len(df)
        state = s.iloc[start]
        if state not in STATE_COLORS:
            continue

        # Get start and end times for this block
        x0 = df[time_col].iloc[start]
        x1 = df[time_col].iloc[end - 1]

        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=STATE_COLORS[state],
            line_width=0,
            layer="below",
            annotation_text=state,
            annotation_position="top left",
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="Path to the FIRM CSV log")
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

    if not args.csv.exists():
        raise SystemExit(f"File not found: {args.csv}")

    # Read CSV
    # mixed_types=False prevents warnings if columns have mixed empty/float strings
    df = pd.read_csv(args.csv, low_memory=False)

    # 1. Clean Headers (Strip whitespace, fix potential typo from prompt)
    df.columns = df.columns.str.strip()
    if "tate_letter" in df.columns and "state_letter" not in df.columns:
        df.rename(columns={"tate_letter": "state_letter"}, inplace=True)

    # 2. Filter Rows
    # We only want rows where estimation data exists.
    # Raw packets have empty 'current_altitude' (NaN).
    if "current_altitude" in df.columns:
        initial_count = len(df)
        df = df.dropna(subset=["current_altitude"]).copy()
        print(f"Filtered log: Kept {len(df)} estimation packets (dropped {initial_count - len(df)} raw packets).")
    else:
        print("Warning: 'current_altitude' not found. Plotting all rows.")

    if df.empty:
        raise SystemExit("No data remaining after filtering (is the CSV empty or missing estimation fields?)")

    # 3. Handle Time
    # New format has 'timestamp' in nanoseconds. Old format had 'timestamp_seconds'.
    if "timestamp" in df.columns:
        # Convert nanoseconds to relative seconds
        start_ns = df["timestamp"].iloc[0]
        df["t"] = (df["timestamp"] - start_ns) / 1e9
    elif "timestamp_seconds" in df.columns:
        df["t"] = df["timestamp_seconds"] - df["timestamp_seconds"].min()
    else:
        # Fallback: just use index
        print("Warning: No timestamp column found. Using index as time.")
        df["t"] = df.index

    # Create figure
    fig = go.Figure()

    traces = existing_traces(df, DEFAULT_TRACES)
    if not traces:
        print(f"Warning: None of the default columns {DEFAULT_TRACES} were found.")
        print(f"Available columns: {list(df.columns)}")

    for col, label in traces:
        fig.add_trace(
            go.Scatter(
                x=df["t"],
                y=df[col],
                mode="lines+markers", # Added markers since data might be sparser now
                name=label,
                marker=dict(size=4),
            )
        )

    # Optional shaded regions for states
    if not args.no_state_shading:
        add_state_regions(fig, df, time_col="t")

    # Layout
    fig.update_layout(
        title=f"FIRM Log: {args.csv.name}",
        xaxis_title="Time since start (s)",
        yaxis_title="Value",
        hovermode="x unified",
        template="plotly_white",
        legend_title="Traces",
    )

    # If user wants an output HTML file
    if args.out is not None:
        fig.write_html(args.out, include_plotlyjs="cdn")
        print(f"Wrote: {args.out}")
    else:
        fig.show()


if __name__ == "__main__":
    main()
