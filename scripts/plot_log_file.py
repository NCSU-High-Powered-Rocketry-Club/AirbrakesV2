#!/usr/bin/env python3
"""Interactive Plotly viewer for Airbrakes CSV logs.

Usage:
    python scripts/plot_log_file.py path-to-log.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import plotly.graph_objects as go

if TYPE_CHECKING:
    from collections.abc import Iterable


DEFAULT_TRACES = [
    ("estPressureAlt", "Estimated Pressure Altitude (m)"),
    ("current_altitude", "Processed Current Altitude (m)"),
    ("height_used_for_prediction", "Height Used for Prediction (m)"),
    ("vertical_velocity_meters_per_s", "Vertical Velocity (m/s)"),
    ("estCompensatedAccelZ", "Estimated Z Acceleration (m/s^2)"),
    ("predicted_apogee", "Predicted Apogee (m)"),
    ("current_position", "Airbrake Position"),
]

ESTIMATED_ROW_COLUMNS = (
    "estPressureAlt",
    "estOrientQuaternionW",
    "estOrientQuaternionX",
    "estOrientQuaternionY",
    "estOrientQuaternionZ",
    "estAttitudeUncertQuaternionW",
    "estAttitudeUncertQuaternionX",
    "estAttitudeUncertQuaternionY",
    "estAttitudeUncertQuaternionZ",
    "estAngularRateX",
    "estAngularRateY",
    "estAngularRateZ",
    "estCompensatedAccelX",
    "estCompensatedAccelY",
    "estCompensatedAccelZ",
    "estLinearAccelX",
    "estLinearAccelY",
    "estLinearAccelZ",
    "estGravityVectorX",
    "estGravityVectorY",
    "estGravityVectorZ",
    "current_altitude",
    "timestamp_seconds",
)

STATE_COLORS = {
    "S": "rgba(0, 102, 204, 0.15)",
    "M": "rgba(0, 153, 0, 0.15)",
    "C": "rgba(204, 0, 0, 0.15)",
    "F": "rgba(153, 0, 153, 0.15)",
    "L": "rgba(255, 153, 0, 0.15)",
}


def existing_traces(df: pd.DataFrame, traces: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return configured traces which are present in the log."""
    return [(column, label) for column, label in traces if column in df.columns]


def estimated_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows originating from estimated IMU packets and their processor output."""
    available_columns = [column for column in ESTIMATED_ROW_COLUMNS if column in df.columns]
    if not available_columns:
        raise SystemExit("CSV does not contain estimated IMU or processor packet columns.")

    return df.loc[df[available_columns].notna().any(axis=1)].copy()


def add_time_axis(df: pd.DataFrame) -> None:
    """Add elapsed seconds using the IMU timestamp or a supported fallback."""
    if "timestamp" in df.columns:
        timestamp_ns = pd.to_numeric(df["timestamp"], errors="coerce")
        if "update_timestamp_ns" in df.columns:
            timestamp_ns = timestamp_ns.combine_first(
                pd.to_numeric(df["update_timestamp_ns"], errors="coerce")
            )
        if timestamp_ns.notna().any():
            df["t"] = (timestamp_ns - timestamp_ns.min()) / 1_000_000_000
            return

    if "timestamp_seconds" in df.columns:
        timestamp_seconds = pd.to_numeric(df["timestamp_seconds"], errors="coerce")
        if timestamp_seconds.notna().any():
            df["t"] = timestamp_seconds - timestamp_seconds.min()
            return

    if "update_timestamp_ns" in df.columns:
        update_timestamp_ns = pd.to_numeric(df["update_timestamp_ns"], errors="coerce")
        if update_timestamp_ns.notna().any():
            df["t"] = (update_timestamp_ns - update_timestamp_ns.min()) / 1_000_000_000
            return

    raise SystemExit(
        "CSV must contain numeric values in 'timestamp', 'timestamp_seconds', "
        "or 'update_timestamp_ns'."
    )


def add_state_regions(fig: go.Figure, df: pd.DataFrame, time_col: str = "t") -> None:
    """Add vertical shaded regions for runs of the same state."""
    if "state_letter" not in df.columns:
        return

    states = df["state_letter"].dropna().astype(str)
    if states.empty:
        return

    state_changes = states.ne(states.shift(fill_value=states.iloc[0])).to_numpy().nonzero()[0]
    for index, start in enumerate(state_changes):
        end = state_changes[index + 1] if index + 1 < len(state_changes) else len(states)
        state = states.iloc[start]
        if state in STATE_COLORS:
            fig.add_vrect(
                x0=df[time_col].loc[states.index[start]],
                x1=df[time_col].loc[states.index[end - 1]],
                fillcolor=STATE_COLORS[state],
                line_width=0,
                layer="below",
            )


def add_altitude_source_trace(fig: go.Figure, df: pd.DataFrame, time_col: str = "t") -> None:
    """Add a stepped right-axis trace for pressure versus integrated altitude."""
    if "integrating_for_altitude" not in df.columns:
        return

    source = df["integrating_for_altitude"].astype(str).str.upper().map({"F": 0.0, "T": 1.0})
    if source.notna().any():
        fig.add_trace(
            go.Scatter(
                x=df[time_col],
                y=source,
                mode="lines",
                name="Altitude Source",
                line_shape="hv",
                yaxis="y2",
            )
        )
        fig.update_layout(
            yaxis2={
                "title": "Altitude Source",
                "overlaying": "y",
                "side": "right",
                "range": [-0.05, 1.05],
                "tickvals": [0, 1],
                "ticktext": ["Pressure (F)", "Integrated (T)"],
                "showgrid": False,
            }
        )


def main() -> None:
    """Create an interactive plot from an Airbrakes CSV log."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Path to an Airbrakes CSV log")
    parser.add_argument(
        "--no-state-shading",
        action="store_true",
        help="Disable shaded regions for state transitions",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write the plot to this HTML file instead of opening it in a browser",
    )
    args = parser.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"File not found: {args.csv}")

    dataframe = pd.read_csv(args.csv)
    if dataframe.empty:
        raise SystemExit(f"CSV contains no log rows: {args.csv}")

    dataframe = estimated_rows(dataframe)
    if dataframe.empty:
        raise SystemExit(f"CSV contains no estimated IMU rows: {args.csv}")

    add_time_axis(dataframe)
    traces = existing_traces(dataframe, DEFAULT_TRACES)
    if not traces:
        raise SystemExit(
            "None of the default plot columns were found.\n"
            f"Columns in file: {list(dataframe.columns)}"
        )

    figure = go.Figure()
    for column, label in traces:
        figure.add_trace(
            go.Scatter(
                x=dataframe["t"],
                y=pd.to_numeric(dataframe[column], errors="coerce"),
                mode="lines",
                name=label,
            )
        )

    add_altitude_source_trace(figure, dataframe)
    if not args.no_state_shading:
        add_state_regions(figure, dataframe)

    figure.update_layout(
        title=f"Airbrakes Log: {args.csv.name}",
        xaxis_title="Time Since Start (s)",
        yaxis_title="Value",
        hovermode="x unified",
        template="plotly_white",
        legend_title="Traces",
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        figure.write_html(args.out, include_plotlyjs="cdn")
        print(f"Wrote: {args.out}")  # noqa: T201
    else:
        figure.show()


if __name__ == "__main__":
    main()
