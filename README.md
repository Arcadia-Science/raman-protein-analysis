# Analyzing protein perturbations with Raman spectroscopy

Code and data for generating figures in the 2026 Arcadia Science pub titled ["Spontaneous Raman spectroscopy detects chemical perturbation of protein structure"](https://doi.org/10.57844/arcadia-f4fe-ep62).


## Running the notebooks

We use [uv](https://docs.astral.sh/uv/) for package management. 

We use uv to manage the dependencies and run the scripts.

First install the dependencies:

```bash
uv sync
```

Then, run the notebooks in `/notebooks`.

Run `notebooks/generate-raman-figures.ipynb` to reproduce Raman spectra in the figures. Figures are written to `outputs/Raman/`

Run `notebooks/generate-SEC-figures.ipynb` to reproduce SEC (size-exclusion chromatorgraphy) figures. Figures are written to `outputs/SEC/`.

## Raw data

**Raman:** Raw data for all experiments is in `data/raman-chemical-perturbations` and `data/raman-ph-perturbations`. InstantRaman CSV files organized by date and condition. Each experiment directory contains a `sample_table.csv` mapping filenames to sample names and group IDs for coloring.

**SEC:** Raw tab-separated CSVs (one per condition per protein). `generate-SEC-figures.ipynb` normalizes these to Excel first, then plots.

The raw data used in each figure is shown [here](outputs/experiment-sample-map.md).
