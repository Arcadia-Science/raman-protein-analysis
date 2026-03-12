# SEC_analysis

Pipeline and GUI for SEC (size-exclusion chromatography) curves: **raw instrument CSVs → normalized Excel → Arcadia-styled SVG figures**.

## Supported proteins

| Raw data folder (inside `data/`) | Normalized Excel |
|----------------------------------|------------------|
| `data/BSA_raw_data/` | `bsa_curves_normalized.xlsx` |
| `data/DNase_raw_data/` | `DNAse_curves_normalized.xlsx` |
| `data/CytC_raw_data/` | `Cyt_C_curves_normalized.xlsx` |
| `data/Hemoglobin_raw_data/` | `Hemo_curves_normalized (2).xlsx` |

All four use the same Python pipeline and the same batch SVG script and web GUI.

## Folder layout (repo)

- **`data/<protein>_raw_data/`** — Raw instrument CSV exports (one CSV per condition). Do not rename these folders.
- **`normalized/`** — Created when you run step 1. Normalized `.xlsx` files are written here.
- **`output/`** — SVGs written by step 2.

## Pipeline

1. **Raw → normalized Excel**  
   From this folder (`SEC_analysis/`):
   ```bash
   python sec_raw_to_normalized.py
   ```
   Reads CSVs from `data/<protein>_raw_data/`, writes normalized Excel into `normalized/`.

2. **Normalized Excel → SVG**  
   ```bash
   python plot_sec_to_svg.py
   ```
   Reads `normalized/*.xlsx`, writes SVGs to `output/`.

3. **Web GUI**  
   For ad‑hoc plots from CSV: `python app.py`, then open http://127.0.0.1:5000.

## Dependencies

```bash
pip install -r requirements.txt
```

**Local:** `python app.py` then open http://127.0.0.1:5000. **Deploy** (e.g. Render): same install, start command `gunicorn app:app`.

Requires: pandas, openpyxl, matplotlib, arcadia-pycolor, flask, gunicorn. Python 3.8+.

## Config

`sec_raw_to_normalized.SEC_PROTEIN_CONFIG` — Folder names and CSV filename substrings must match what’s in the repo. The script is set up for the filenames in `data/*_raw_data/` (e.g. `2026_02_20 BSA  001.csv`, `DNase_EDTA 2 001.csv`). If you add files with different names, adjust the config.

**Note:** CytC is missing `CytochromeC_EDTA` in the repo; that protein is skipped until the file is added.

**Fonts (optional):** `Atkinson_Hyperlegible/` for Arcadia-style text; plots still work without it.
