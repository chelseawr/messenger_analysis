from __future__ import annotations

from datetime import date, datetime
from typing import Dict

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html

from .metrics import ConversationStats


def _set_zeroes(obj: Dict[str, int], fmt: str) -> Dict[str, int]:
    """Fill missing dates with zeros to make plots continuous."""
    if not obj:
        return obj
    keys = list(obj.keys())
    try:
        start = datetime.strptime(min(keys), fmt).date()
        end = date.today()
    except ValueError:
        return obj

    freq = "D" if "%d" in fmt else "MS"
    for d in pd.date_range(start, end, freq=freq):
        key = d.strftime(fmt)
        obj.setdefault(key, 0)
    return obj


def _bar_from_mapping(counts: Dict[str, int], x_label: str, y_label: str, title: str):
    df = pd.DataFrame.from_dict(counts, orient="index", columns=[y_label])
    df.index.name = x_label
    df = df.sort_index()
    fig = px.bar(df, labels={"index": x_label, y_label: y_label}, title=title)
    return fig


def monthly_figure(stats: ConversationStats, person_a: str, person_b: str):
    counts = _set_zeroes(dict(stats.month_count), "%Y-%m")
    return _bar_from_mapping(
        counts,
        x_label="Month",
        y_label="Message Count",
        title=f"Monthly message count between {person_a} and {person_b}",
    )


def daily_figure(stats: ConversationStats, person_a: str, person_b: str):
    counts = _set_zeroes(dict(stats.day_count), "%Y-%m-%d")
    return _bar_from_mapping(
        counts,
        x_label="Day",
        y_label="Message Count",
        title=f"Daily message count between {person_a} and {person_b}",
    )


def hourly_figure(stats: ConversationStats, person_a: str, person_b: str):
    counts = {f"{h:02d}:00": stats.hour_count.get(h, 0) for h in range(24)}
    return _bar_from_mapping(
        counts,
        x_label="Hour of day",
        y_label="Message Count",
        title=f"Hourly message count between {person_a} and {person_b}",
    )


def run_single_figure_app(fig) -> None:
    """Run a very small Dash app to display a single figure."""
    app = Dash(__name__)
    app.layout = html.Div(
        children=[
            html.H1("Messenger Analysis"),
            dcc.Graph(id="graph", figure=fig),
        ]
    )
    app.run_server(debug=True)
