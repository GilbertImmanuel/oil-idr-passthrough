"""Theme-aware chart styling and the appearance toggle shared by the dashboard.

Render a visible Dark and Light toggle in the sidebar, re-theme the whole app through the
Streamlit theme config, and re-skin the plotly charts to match. Centralize the sector colors so a
theme change touches this file only.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# Fixed sector colors, reused across the home, event-study, and IRF pages.
ENERGY_COLOR = "#E8833A"
CONSUMER_COLOR = "#4C9BE8"
RESPONSE_COLOR = "#4C9BE8"
ZERO_LINE_COLOR = "#888888"


def template_for(theme_type: str | None) -> str:
    """Plotly template name for a Streamlit theme type. Dark maps to plotly_dark, else plotly."""
    return "plotly_dark" if theme_type == "dark" else "plotly"


def is_dark() -> bool:
    """Active appearance from the sidebar toggle. Default dark.

    Read the toggle state rather than st.context.theme, which does not reflect a runtime theme
    override in streamlit 1.59.
    """
    return bool(st.session_state.get("dark_mode", True))


def render_toggle() -> None:
    """Render the sidebar Dark and Light toggle and re-theme the app when it changes.

    ponytail: st._config.set_option mutates process-global config and is a private API. It is the
    only way found to re-theme the connected client at runtime in streamlit 1.59, since
    st.context.theme exposes no setter. Global mutation is acceptable for a single-viewer
    dashboard; revisit if the deploy serves concurrent users with independent themes.
    """
    if "_applied_base" not in st.session_state:
        st.session_state["_applied_base"] = "dark"  # matches .streamlit/config.toml
    dark = st.sidebar.toggle("Dark mode", value=True, key="dark_mode")
    want = "dark" if dark else "light"
    if st.session_state["_applied_base"] != want:
        st.session_state["_applied_base"] = want
        st._config.set_option("theme.base", want)
        st.rerun()


def band_color() -> str:
    """Fill color for the IRF confidence band, tuned for the active theme."""
    return "rgba(150,170,200,0.28)" if is_dark() else "rgba(70,90,120,0.18)"


def style_fig(fig: go.Figure, height: int = 460) -> go.Figure:
    """Apply the theme template, transparent backgrounds, margins, and a horizontal legend.

    Transparent paper and plot backgrounds let the figure blend with the active app theme, so the
    toggle is reflected without a per-figure color list.
    """
    # Keep the plotly default legend (vertical, top right) so it never overlaps the top title.
    fig.update_layout(
        template=template_for("dark" if is_dark() else "light"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin={"l": 10, "r": 10, "t": 56, "b": 10},
        title={"x": 0, "xanchor": "left", "yanchor": "top"},
    )
    return fig


def demo() -> None:
    """Self-check: the template mapping."""
    assert template_for("dark") == "plotly_dark"
    assert template_for("light") == "plotly"
    print("theme demo ok")


if __name__ == "__main__":
    demo()
