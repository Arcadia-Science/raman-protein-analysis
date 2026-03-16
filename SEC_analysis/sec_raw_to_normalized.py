"""
Build a normalized SEC Excel "Data" sheet from raw instrument CSV exports.

Raw CSVs are tab-separated, UTF-16, with 3 header rows. Volume (ml) and UV (mAU)
are in columns 0 and 1. Each CSV is one condition (e.g. BSA_standards, BSA_TCEP).
Each trace is normalized to [0, 1] and interpolated onto a common volume grid.
The combined Data sheet (Volume/signal pairs + Pk_x/Pk_y) is consumed by plot_sec_to_svg.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def read_raw_sec_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Read one raw SEC instrument CSV. Returns (volume_ml, uv_mAU).
    Uses columns 0 and 1 (first UV channel); data starts at row 3.
    Tries UTF-16 then UTF-8 (repo exports may differ).
    """
    for enc in ("utf-16", "utf-8"):
        try:
            df = pd.read_csv(path, sep="\t", encoding=enc, header=None)
            break
        except Exception:
            continue
    else:
        df = pd.read_csv(path, sep="\t", header=None)
    vol = pd.to_numeric(df.iloc[3:, 0], errors="coerce").values
    uv = pd.to_numeric(df.iloc[3:, 1], errors="coerce").values
    valid = ~(np.isnan(vol) | np.isnan(uv))
    return vol[valid].astype(float), uv[valid].astype(float)


def normalize_signal(uv: np.ndarray) -> np.ndarray:
    """Scale UV to [0, 1]: (uv - min) / (max - min)."""
    u = uv.astype(float)
    lo, hi = np.nanmin(u), np.nanmax(u)
    if hi <= lo:
        return np.zeros_like(u)
    return (u - lo) / (hi - lo)


def peak_volume(vol: np.ndarray, uv: np.ndarray) -> float:
    """Return volume (mL) at maximum UV."""
    return float(vol[np.argmax(uv)])


def build_data_sheet(
    runs: list[tuple[str, Path]],
    volume_min: float = 0.0,
    volume_max: float = 25.0,
    n_points: int = 299,
) -> pd.DataFrame:
    """
    Build a single Data sheet from a list of (condition_name, csv_path).
    runs should be in desired column order (e.g. standards, TCEP, EDTA, TCEP_EDTA).
    """
    grid = np.linspace(volume_min, volume_max, n_points)
    series_data = []

    for name, path in runs:
        if not path.exists():
            raise FileNotFoundError(f"Raw CSV not found: {path}")
        vol, uv = read_raw_sec_csv(path)
        uv_n = normalize_signal(uv)
        pk = peak_volume(vol, uv)
        signal_on_grid = np.interp(grid, vol, uv_n)
        series_data.append((name, grid.copy(), signal_on_grid, pk))

    data_rows = []
    for j in range(n_points):
        row = []
        for _, (_, v, s, _) in enumerate(series_data):
            row.extend([v[j], s[j]])
        data_rows.append(row)

    col_names = []
    for i in range(len(series_data)):
        col_names.append("Volume (mL)" + (f".{i}" if i else ""))
        col_names.append(series_data[i][0])

    df_data = pd.DataFrame(data_rows, columns=col_names)

    pk_x_vals = [pk for (_, __, ___, pk) in series_data]
    pk_y_vals = [1.0] * 4  # normalized peak is always 1
    for i in range(4):
        df_data[f"Pk_x_{i}"] = np.nan
        df_data[f"Pk_y_{i}"] = np.nan
    df_data.loc[0, [f"Pk_x_{i}" for i in range(4)]] = pk_x_vals
    df_data.loc[0, [f"Pk_y_{i}" for i in range(4)]] = pk_y_vals

    return df_data


def raw_folder_to_data_sheet(
    raw_dir: Path,
    file_to_condition: list[tuple[str, str]],
    volume_min: float = 0.0,
    volume_max: float = 25.0,
    n_points: int = 299,
) -> pd.DataFrame:
    """
    file_to_condition: list of (filename_substring, condition_name) in desired column order.
    Matches the first CSV in raw_dir whose filename contains the substring.
    """
    runs = []
    for sub, cond in file_to_condition:
        candidates = list(raw_dir.glob("*.csv"))
        match = next((p for p in candidates if sub in p.name), None)
        if match is None:
            raise FileNotFoundError(f"No CSV in {raw_dir} containing '{sub}' for condition {cond}")
        runs.append((cond, match))
    return build_data_sheet(runs, volume_min=volume_min, volume_max=volume_max, n_points=n_points)


def write_normalized_excel(
    data_df: pd.DataFrame,
    output_path: Path,
    sheet_name: str = "Data",
) -> None:
    """Write DataFrame to Excel as the Data sheet."""
    data_df.to_excel(output_path, sheet_name=sheet_name, index=False)


# Config for all proteins: (raw_folder_name, output_xlsx_filename, file_to_condition).
# Raw folders live inside the SEC data directory (e.g. data/SEC/BSA_raw_data).
# file_to_condition: list of (filename_substring, condition_name).
SEC_PROTEIN_CONFIG = [
    (
        "BSA_raw_data",
        "bsa_curves_normalized.xlsx",
        [
            ("TCEP and buffer", "BSA_TCEP"),
            ("2026_02_20 BSA  001", "BSA_standards"),
            ("BSA_EDTA", "BSA_EDTA"),
            ("BSA_TCEP_EDTA", "BSA_TCEP_EDTA"),
        ],
    ),
    (
        "DNase_raw_data",
        "DNAse_curves_normalized.xlsx",
        [
            ("DNAse  001", "DNAse I standard"),
            ("DNAse_TCEP", "DNAse I_TCEP"),
            ("DNase_EDTA", "DNAse_I_EDTA"),
            ("DNase_TCE_EDTA", "DNAse_I_TCEP_EDTA"),
        ],
    ),
    (
        "CytC_raw_data",
        "Cyt_C_curves_normalized.xlsx",
        [
            ("CytochromeC standard", "Cyt_C_standard"),
            ("CytochromeC_TCEP", "Cyt_C_TCEP"),
            ("CytochromeC_EDTA", "Cyt_C_EDTA"),
            ("CytochromeC_TCEP_EDTA", "Cyt_C_TCEP_EDTA"),
        ],
    ),
    (
        "Hemoglobin_raw_data",
        "Hemo_curves_normalized (2).xlsx",
        [
            ("hemoglobin commercial", "Hemoglobin_standard"),
            ("Hemoglobin TCEP", "Hemoglobin_TCEP"),
            ("Hemoglobin_EDTA", "Hemoglobin_EDTA"),
            ("Hemoglobin_TCEP_EDTA", "Hemoglobin_TCEP_EDTA"),
        ],
    ),
]


def run_all_proteins(
    sec_data_dir: Path,
    output_dir: Path,
    volume_min: float = 0.1,
    volume_max: float = 25.0,
    n_points: int = 299,
) -> None:
    """
    Build normalized Excel Data sheets for all proteins in SEC_PROTEIN_CONFIG.
    sec_data_dir: path to folder containing BSA_raw_data, DNAse_raw_data, etc.
    output_dir: where to write the .xlsx files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for raw_folder, out_name, mapping in SEC_PROTEIN_CONFIG:
        raw_dir = Path(sec_data_dir) / raw_folder
        if not raw_dir.is_dir():
            print(f"  Skip {raw_folder}: not a directory")
            continue
        try:
            df = raw_folder_to_data_sheet(
                raw_dir, mapping, volume_min=volume_min, volume_max=volume_max, n_points=n_points
            )
            out_path = output_dir / out_name
            write_normalized_excel(df, out_path, sheet_name="Data")
            print(f"  Wrote {out_path.name}")
        except FileNotFoundError as e:
            print(f"  Skip {raw_folder}: {e}")
        except Exception as e:
            print(f"  Error {raw_folder}: {e}")
