#!/usr/bin/env python3
"""
Plot SEC (size-exclusion chromatography) curves from Excel files in
'Final SEC figures' and export as SVGs per 2026 Arcadia Style Guide.
Output: SEC_figures_SVG/ in the same Protein Raman folder.

Also provides plot_from_mapping() for CSV + column mapping (used by web GUI).
"""

import io
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import arcadia_pycolor as apc


# Paths: repo has data/ (raw folders) and normalized/ (xlsx from sec_raw_to_normalized). Read xlsx from normalized/ or data/.
_SCRIPT_DIR = Path(__file__).resolve().parent
if (_SCRIPT_DIR / "normalized").is_dir():
    INPUT_DIR = _SCRIPT_DIR / "normalized"
    OUTPUT_DIR = _SCRIPT_DIR / "output"
elif (_SCRIPT_DIR / "data").is_dir():
    INPUT_DIR = _SCRIPT_DIR / "data"
    OUTPUT_DIR = _SCRIPT_DIR / "output"
else:
    INPUT_DIR = _SCRIPT_DIR / "Final SEC figures "
    OUTPUT_DIR = _SCRIPT_DIR / "SEC_figures_SVG"

COLOR_NOPERTURBATION = apc.chateau
COLOR_TCEP = apc.canary
COLOR_EDTA = apc.aegean
COLOR_BOTH = apc.lime
COLOR_GRAY = apc.bark
BLACK = "#000000"
LINE_COLORS = [COLOR_NOPERTURBATION, COLOR_TCEP, COLOR_EDTA, COLOR_BOTH]
FONT_TICKS_FONTSIZE = 14.5

# Legend order by suffix (same on every plot)
SUFFIX_ORDER = ("_standards", "_standard", "_TCEP", "_EDTA", "_TCEP_EDTA")

def _color_index_for_label(label: str) -> int:
    """Same suffix = same color. Returns 0=standard(s), 1=TCEP, 2=EDTA, 3=TCEP_EDTA."""
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
    """Order: _standards, _TCEP, _EDTA, _TCEP_EDTA (index 0,1,2,3)."""
    return _color_index_for_label(item[2])

def _display_name(name: str) -> str:
    """Show 'No Treatment' instead of 'standard'/'standards'; underscores -> ' + '; Cyt C -> Cytochrome c; DNAse + I -> DNAse I."""
    n = name.replace("standards", "No Treatment").replace("standard", "No Treatment")
    n = n.replace("_", " + ")
    n = n.replace("Cyt + C", "Cytochrome c")
    n = n.replace("DNAse + I", "DNAse I")
    n = n.replace("DNAse", "DNase")
    return n


def _condition_display(label: str) -> str:
    """Return the condition/suffix only (for legend line): No Treatment, TCEP, EDTA, TCEP + EDTA."""
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
    """Return the protein part for legend title (e.g. BSA, DNase I, Cytochrome c)."""
    full = _display_name(label)
    cond = _condition_display(label)
    # Remove condition from end; can be " + Condition" or " Condition" (e.g. "DNase I standard" -> "DNase I No Treatment")
    for suffix in (" + " + cond, " " + cond):
        if full.endswith(suffix):
            return full[: -len(suffix)].strip()
    return full



def get_series_pairs(df: pd.DataFrame):
    """
    From Data sheet: row 0 has headers. Column pairs (0,1), (2,3), (4,5), (6,7)
    are (Volume, signal). Stop at columns that look like Pk_x_* / Pk_y_*.
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
        # Legend text = sample name from column header (e.g. BSA_TCEP, BSA_standards)
        name = col1 if pd.notna(col1) and str(col1).strip() else f"Series {len(pairs)+1}"
        if name == "Volume (mL)":
            name = f"Series {len(pairs)+1}"
        # Peak volume = x at max y (for legend and annotation)
        peak_idx = np.argmax(y)
        peak_vol = float(x[peak_idx])
        peak_y_val = float(y[peak_idx])
        pairs.append((x, y, str(name), peak_vol, peak_y_val))
    return pairs


def pairs_from_mapping(df: pd.DataFrame, series: list[dict[str, Any]]) -> list[tuple]:
    """Build (x, y, name, peak_vol, peak_y_val) pairs from explicit column mapping.
    series: list of {"x_col": 0, "y_col": 1, "name": "BSA_TCEP"} (0-based column indices).
    """
    pairs = []
    for s in series:
        i, j = s["x_col"], s["y_col"]
        if i >= df.shape[1] or j >= df.shape[1]:
            continue
        xx = df.iloc[:, i]
        yy = df.iloc[:, j]
        xnum = pd.to_numeric(xx, errors="coerce")
        ynum = pd.to_numeric(yy, errors="coerce")
        mask = xnum.notna() & ynum.notna()
        x = xnum[mask].values
        y = ynum[mask].values
        if len(x) == 0:
            continue
        name = s.get("name", f"Series {len(pairs)+1}")
        peak_idx = np.argmax(y)
        peak_vol = float(x[peak_idx])
        peak_y_val = float(y[peak_idx])
        pairs.append((x, y, str(name), peak_vol, peak_y_val))
    return pairs


def suggest_legend(pairs: list[tuple]) -> tuple[str, list[str]]:
    """Return (legend_title, list of legend line strings) as they would appear on the figure."""
    if not pairs:
        return " - Condition", []
    pairs_sorted = sorted(pairs, key=_sort_key_for_legend)
    legend_title = _protein_display(pairs_sorted[0][2]) + " - Condition"
    labels = [
        f"{_condition_display(label)} ({peak_vol:.2f} mL)"
        for (_, __, label, peak_vol, ___) in pairs_sorted
    ]
    return legend_title, labels


def render_sec_svg(
    pairs: list,
    legend_title: Optional[str] = None,
    legend_labels: Optional[List[str]] = None,
) -> str:
    """Render SEC plot to SVG string. pairs = [(x, y, label, peak_vol, peak_y_val), ...].
    If legend_title / legend_labels are provided, use them; else compute from pairs.
    """
    if not pairs:
        raise ValueError("No series to plot")
    pairs = sorted(pairs, key=_sort_key_for_legend)
    if legend_title is None:
        legend_title = _protein_display(pairs[0][2])
    computed_labels = [f"{_condition_display(label)} ({peak_vol:.2f} mL)" for (_, __, label, peak_vol, ___) in pairs]
    if legend_labels is None or len(legend_labels) != len(pairs):
        legend_labels = computed_labels
    else:
        legend_labels = [lbl.strip() if (lbl and lbl.strip()) else comp for lbl, comp in zip(legend_labels, computed_labels)]
    apc.mpl.setup()

    fig, ax = plt.subplots(figsize=(10, 6))
    for idx, (x, y, label, peak_vol, peak_y_val) in enumerate(pairs):
        color = LINE_COLORS[_color_index_for_label(label)]
        leg_label = legend_labels[idx] if idx < len(legend_labels) else f"{_condition_display(label)} ({peak_vol:.2f} mL)"
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



def plot_one_file(excel_path: Path, output_dir: Path) -> None:
    """Load one Excel file, plot all series, save as SVG."""
    xl = pd.ExcelFile(excel_path)
    if "Data" not in xl.sheet_names:
        print(f"  Skip {excel_path.name}: no 'Data' sheet")
        return
    df = pd.read_excel(excel_path, sheet_name="Data", header=0)
    pairs = get_series_pairs(df)
    if not pairs:
        print(f"  Skip {excel_path.name}: no series found")
        return
    title = excel_path.stem.replace("_", " ").replace(" (2)", "").replace(" (27)", "")
    svg = render_sec_svg(pairs, title)
    out_path = output_dir / (excel_path.stem + ".svg")
    out_path.write_text(svg, encoding="utf-8")
    print(f"  Saved {out_path.name}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(INPUT_DIR.glob("*.xlsx"))
    if not files:
        print(f"No .xlsx files in {INPUT_DIR}")
        return
    print(f"Plotting {len(files)} file(s) -> {OUTPUT_DIR}")
    for path in files:
        plot_one_file(path, OUTPUT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
