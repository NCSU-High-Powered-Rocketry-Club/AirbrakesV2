#!/usr/bin/env python3
"""plot_firm_log.py.

Interactive Plotly viewer for FIRM CSV logs.

Usage:
  python plot_firm_log.py path/to/log.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go


DEFAULT_TRACES = [
    # (column_name, pretty_label)
    ("est_position_z_meters", "Estimated Z Position (m)"),
    ("est_velocity_z_meters_per_s", "Estimated Z Velocity (m/s)"),
    ("est_acceleration_z_gs", "Estimated Z Accel (g)"),
    ("predicted_apogee", "Predicted Apogee"),
    ("encoder_position", "Encoder Position"),
]


STATE_COLORS = {
    "S": "rgba(0, 102, 204, 0.15)",
    "M": "rgba(0, 153, 0, 0.15)",
    "C": "rgba(204, 0, 0, 0.15)",
    "F": "rgba(153, 0, 153, 0.15)",
    "L": "rgba(255, 153, 0, 0.15)",
}


def existing_traces(df: pd.DataFrame, traces: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    out = []
    for col, label in traces:
        if col in df.columns:
            out.append((col, label))
    return out


def add_state_regions(fig: go.Figure, df: pd.DataFrame, time_col: str = "t") -> None:
    """Adds vertical shaded regions for runs of the same state_letter."""
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
        x0 = df[time_col].iloc[start]
        x1 = df[time_col].iloc[end - 1]
        fig.add_vrect(
            x0=x0,
            x1=x1,
            fillcolor=STATE_COLORS[state],
            line_width=0,
            layer="below",
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
    df = pd.read_csv(args.csv)

    if "timestamp_seconds" not in df.columns:
        raise SystemExit("CSV must contain 'timestamp_seconds' column")

    # Build a time axis starting at 0
    # (timestamp_seconds in your sample is already seconds, not ns)
    df["t"] = df["timestamp_seconds"] - df["timestamp_seconds"].min()

    # Create figure
    fig = go.Figure()

    traces = existing_traces(df, DEFAULT_TRACES)
    if not traces:
        raise SystemExit(
            "None of the default columns were found.\n"
            f"Columns in file: {list(df.columns)}"
        )

    for col, label in traces:
        fig.add_trace(
            go.Scatter(
                x=df["t"],
                y=df[col],
                mode="lines",
                name=label,
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
