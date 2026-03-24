# Raman Protein Perturbation

Code and data for generating figures in "Applying Raman spectroscopy for protein analysis".


## Running the notebooks

We use [uv](https://docs.astral.sh/uv/) for package management. To reproduce the figures, download the codebase, install dependencies launch the notebooks within `/notebooks`.

Run `notebooks/generate-raman-figures.ipynb` to reproduce Raman spectra in the figures. Figures are written to `plots/Raman/`

Run `notebooks/generate-SEC-figures.ipynb` to reproduce SEC (size-exclusion chromatorgraphy) figures. Figures are written to `plots/SEC/`.

## Raw data

**Raman:** Raw data for all experiments is in `notebooks/data/raman-chemical-perturbations` and `notebooks/data/raman-ph-perturbations`. InstantRaman CSV files organized by date and condition. Each experiment directory contains a `sample_table.csv` mapping filenames to sample names and group IDs for coloring.

**SEC:** Raw tab-separated CSVs (one per condition per protein). `generate-SEC-figures.ipynb` normalizes these to Excel first, then plots.

The raw data used in each figure is shown [here](experiment-sample-map.md).
