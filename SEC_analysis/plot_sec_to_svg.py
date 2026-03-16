"""
Plot SEC (size-exclusion chromatography) curves from normalized Excel files.
Applies Arcadia color palette and legend ordering consistent with the Raman figures.
"""

import arcadia_pycolor as apc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLOR_NOPERTURBATION = apc.chateau
COLOR_TCEP = apc.canary
COLOR_EDTA = apc.aegean
COLOR_BOTH = apc.lime
LINE_COLORS = [COLOR_NOPERTURBATION, COLOR_TCEP, COLOR_EDTA, COLOR_BOTH]
FONT_TICKS_FONTSIZE = 14.5

# Consistent legend order across all SEC plots
SUFFIX_ORDER = ("_standards", "_standard", "_TCEP", "_EDTA", "_TCEP_EDTA")


def _color_index_for_label(label: str) -> int:
    """Map condition suffix to color index: 0=standard(s), 1=TCEP, 2=EDTA, 3=TCEP+EDTA."""
    u = label.upper()
    if "TCEP_EDTA" in u or u.endswith("TCEP_EDTA"):
        return 3
    if "STANDARD" in u:
        return 0
    if "TCEP" in u:
        return 1
    if "EDTA" in u:
        return 2
    return 0


def _sort_key_for_legend(item):
    return _color_index_for_label(item[2])


def _display_name(name: str) -> str:
    """Normalize label text for display."""
    n = name.replace("standards", "No Treatment").replace("standard", "No Treatment")
    n = n.replace("_", " + ")
    n = n.replace("Cyt + C", "Cytochrome c")
    n = n.replace("DNAse + I", "DNAse I")
    n = n.replace("DNAse", "DNase")
    return n


def _condition_display(label: str) -> str:
    """Return the condition label (e.g. 'No Treatment', 'TCEP', 'EDTA', 'TCEP + EDTA')."""
    u = label.upper()
    if "TCEP_EDTA" in u or u.endswith("TCEP_EDTA"):
        return "TCEP + EDTA"
    if "STANDARD" in u:
        return "No Treatment"
    if "TCEP" in u:
        return "TCEP"
    if "EDTA" in u:
        return "EDTA"
    return label


def _protein_display(label: str) -> str:
    """Extract protein name from label (e.g. 'BSA_TCEP' → 'BSA')."""
    full = _display_name(label)
    cond = _condition_display(label)
    for suffix in (" + " + cond, " " + cond):
        if full.endswith(suffix):
            return full[: -len(suffix)].strip()
    return full


def get_series_pairs(df: pd.DataFrame):
    """
    Extract (x, y, label, peak_vol, peak_y_val) tuples from the Excel Data sheet.
    Column layout: pairs (Volume, signal) at indices (0,1), (2,3), ... up to 4 pairs.
    Stops at columns prefixed with 'Pk_' (peak metadata columns).
    """
    pairs = []
    for i in range(0, min(8, df.shape[1] - 1), 2):
        if i + 1 >= df.shape[1]:
            break
        col0, col1 = df.columns[i], df.columns[i + 1]
        if isinstance(col0, str) and col0.startswith("Pk_"):
            break
        if isinstance(col1, str) and col1.startswith("Pk_"):
            break
        xx = df.iloc[1:, i]
        yy = df.iloc[1:, i + 1]
        xnum = pd.to_numeric(xx, errors="coerce")
        ynum = pd.to_numeric(yy, errors="coerce")
        mask = xnum.notna() & ynum.notna()
        x = xnum[mask].values
        y = ynum[mask].values
        if len(x) == 0:
            continue
        name = col1 if pd.notna(col1) and str(col1).strip() else f"Series {len(pairs) + 1}"
        if name == "Volume (mL)":
            name = f"Series {len(pairs) + 1}"
        peak_idx = np.argmax(y)
        peak_vol = float(x[peak_idx])
        peak_y_val = float(y[peak_idx])
        pairs.append((x, y, str(name), peak_vol, peak_y_val))
    return pairs


def render_sec_svg(
    pairs: list,
    legend_title: str | None = None,
    legend_labels: list[str] | None = None,
) -> plt.Figure:
    """
    Render SEC curves. pairs = [(x, y, label, peak_vol, peak_y_val), ...].
    legend_title and legend_labels are auto-computed from series names if not provided.
    Returns a matplotlib Figure.
    """
    if not pairs:
        raise ValueError("No series to plot")
    pairs = sorted(pairs, key=_sort_key_for_legend)
    if legend_title is None:
        legend_title = _protein_display(pairs[0][2])
    computed_labels = [
        f"{_condition_display(label)} ({peak_vol:.2f} mL)"
        for (_, __, label, peak_vol, ___) in pairs
    ]
    if legend_labels is None or len(legend_labels) != len(pairs):
        legend_labels = computed_labels
    else:
        legend_labels = [
            lbl.strip() if (lbl and lbl.strip()) else comp
            for lbl, comp in zip(legend_labels, computed_labels, strict=True)
        ]
    apc.mpl.setup()

    fig, ax = plt.subplots(figsize=(10, 6))
    for idx, (x, y, label, peak_vol, _peak_y_val) in enumerate(pairs):
        color = LINE_COLORS[_color_index_for_label(label)]
        leg_label = (
            legend_labels[idx]
            if idx < len(legend_labels)
            else f"{_condition_display(label)} ({peak_vol:.2f} mL)"
        )
        ax.plot(x, y, color=color, label=leg_label, linewidth=2)
    ax.set_xlabel("Volume (mL)")
    ax.set_ylabel("Normalised UV Absorbance")
    ax.tick_params(axis="both", labelsize=FONT_TICKS_FONTSIZE)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
        title=legend_title,
        borderaxespad=0.0,
        alignment="left",
    )

    apc.mpl.style_plot(ax)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.show()
    return fig
