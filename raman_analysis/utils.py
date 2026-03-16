"""
Utility functions for parsing and plotting InstantRaman spectroscopy data.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ramanspy as rp


def collect_spectra_from_dir(data_dir, instrument, include_files=None, recursive=False) -> tuple:
    """
    Collect spectra from files in a directory.

    Inputs:
        data_dir: str, directory with files
        instrument: str, type of instrument ('instantraman')
        include_files: list of str, filenames to include. If None, all files are included
        recursive: bool, if True, search for files recursively in subdirectories

    Returns:
        data_list: list of (filename, pd.DataFrame) tuples
        sample_df: pd.DataFrame with columns 'ID', 'Name', 'Group ID'
    """
    acceptable_ext = [".txt", ".tsv", ".csv"]
    if include_files:
        files = include_files
    else:
        data_path = Path(data_dir)
        if recursive:
            files = []
            for file_path in data_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in acceptable_ext:
                    files.append(str(file_path.relative_to(data_path)))
        else:
            files = [
                f.name
                for f in data_path.iterdir()
                if f.is_file() and f.suffix.lower() in acceptable_ext
            ]

    if "sample_table.csv" in files:
        files.remove("sample_table.csv")

    files.sort(key=lambda x: (Path(x).parent.as_posix(), Path(x).name))

    data_path = Path(data_dir)
    sample_table_path = data_path / "sample_table.csv"
    if not sample_table_path.exists():
        print(f"Warning: Creating new sample_table.csv in {data_dir}")
        sample_data = []
        for i, file in enumerate(files):
            file_path = Path(file)
            sample_data.append({"ID": file, "Name": file_path.with_suffix(""), "Group ID": i})
        sample_df = pd.DataFrame(sample_data)
        sample_df.to_csv(sample_table_path, index=False)
    else:
        print(f"Loading existing sample_table.csv: {sample_table_path}")
        try:
            sample_df = pd.read_csv(
                sample_table_path,
                index_col=0,
                dtype={"ID": str, "Name": str, "Group ID": int},
            )
        except Exception as e:
            raise ValueError(
                f"Error reading sample_table.csv: {e}. "
                "Ensure it has columns 'ID', 'Name', 'Group ID'."
            ) from e

    data_list = []
    for file in files:
        file_path = data_path / file
        if instrument.lower() == "instantraman":
            df = parse_instantraman_output(file_path)
        else:
            raise ValueError("Unsupported instrument type: ", instrument)
        if df is not None:
            data_list.append((file, df))

    if not data_list:
        raise ValueError(
            f"No valid data files found in {data_dir}. "
            "Check the directory. Set `recursive=True` to search subdirectories."
        )
    print(f"Collected {len(data_list)} files from {data_dir}")
    return data_list, sample_df


def process_spectra_from_dir(
    data_list,
    data_dir: str | Path,
    x_to_plot: str = "Wavenumber",
    col_to_plot: str = "Intensity",
    rp_pipeline=None,
    include: list | None = None,
    subtract_id: str | dict | None = None,
):
    """
    Load and preprocess spectra from a directory into a dict of RamanSPy Spectra.

    Inputs:
        data_list: list of (filename, pd.DataFrame) tuples
        data_dir: pathlib.Path, directory with files
        x_to_plot: str, column to use as spectral axis (default "Wavenumber")
        col_to_plot: str, column to use as intensity values
        rp_pipeline: ramanspy.preprocessing.Pipeline, applied after subtraction (optional)
        include: list of sample names to include; must match 'Name' in sample_table.csv (optional)
        subtract_id: str or dict for background subtraction (optional)
            - str: subtract this spectrum from all others
            - dict: maps sample name → background name

    Returns:
        spectra: dict mapping sample name (str) to processed ramanspy.Spectrum
    """
    data_path = Path(data_dir)
    sample_table_path = data_path / "sample_table.csv"
    if not sample_table_path.exists():
        raise FileNotFoundError(f"sample_table.csv not found in {data_dir}")

    sample_table = pd.read_csv(
        sample_table_path, index_col=0, dtype={"ID": str, "Name": str, "Group ID": int}
    )

    if include is not None:
        sample_table = sample_table[sample_table["Name"].isin(include)]
        data_list = [f for f in data_list if f[0] in sample_table.index.values]

    # Factorizing is needed because Group IDs may not be contiguous integers starting at 0
    sample_table["Group ID factorized"] = pd.factorize(sample_table["Group ID"])[0]

    sorted_data_list = []
    for index, _ in sample_table.iterrows():
        matching_files = [f for f in data_list if f[0] == index]
        if len(matching_files) > 1:
            print(f"Warning: Multiple files match sample '{index}'. Using the first match.")
        elif len(matching_files) == 0:
            print(f"Warning: No files match sample '{index}'. Skipping.")
        if matching_files:
            sorted_data_list.append(matching_files[0])

    subtract_spectrum = None
    subtract_spectra_dict = {}

    if subtract_id is not None:

        def find_spectrum_data(target_id):
            for file, df in sorted_data_list:
                if file in sample_table.index:
                    if target_id == sample_table.loc[file]["Name"]:
                        return (file, df)
                if target_id == file:
                    return (file, df)
            return None

        if isinstance(subtract_id, str):
            subtract_data = find_spectrum_data(subtract_id)
            if subtract_data is None:
                print(
                    f"Warning: Could not find subtract spectrum '{subtract_id}'. "
                    "Proceeding without subtraction."
                )
            else:
                file, df = subtract_data
                if col_to_plot not in df.columns:
                    raise ValueError(f"Column '{col_to_plot}' not found in subtract spectrum data.")
                if x_to_plot not in df.columns:
                    raise ValueError(f"Column '{x_to_plot}' not found in subtract spectrum data.")
                subtract_spectrum = rp.Spectrum(df[col_to_plot].values, df[x_to_plot].values)

        elif isinstance(subtract_id, dict):
            for key, value in subtract_id.items():
                subtract_data = find_spectrum_data(value)
                if subtract_data is None:
                    print(
                        f"Warning: Could not find subtract spectrum '{value}' "
                        f"for key '{key}'. Skipping."
                    )
                else:
                    file, df = subtract_data
                    if col_to_plot not in df.columns:
                        raise ValueError(
                            f"Column '{col_to_plot}' not found in subtract spectrum '{value}'."
                        )
                    if x_to_plot not in df.columns:
                        raise ValueError(
                            f"Column '{x_to_plot}' not found in subtract spectrum '{value}'."
                        )
                    subtract_spectra_dict[key] = rp.Spectrum(
                        df[col_to_plot].values, df[x_to_plot].values
                    )
        else:
            raise TypeError("subtract_id must be either a str or dict")

    spectra = {}

    for file, df in sorted_data_list:
        if col_to_plot not in df.columns:
            raise ValueError(f"Column '{col_to_plot}' not found in '{file}' spectrum data.")
        if x_to_plot not in df.columns:
            raise ValueError(f"Column '{x_to_plot}' not found in '{file}' spectrum data.")

        sample_id = Path(file).stem
        spectrum = rp.Spectrum(df[col_to_plot].values, df[x_to_plot].values)
        sample_name = sample_table.loc[file]["Name"]

        spectrum_to_subtract = None

        if subtract_spectrum is not None:
            is_subtract_spectrum = (
                subtract_id == file or subtract_id == sample_id or subtract_id == sample_name
            )
            if not is_subtract_spectrum:
                spectrum_to_subtract = subtract_spectrum

        elif subtract_spectra_dict:
            for key_to_try in [file, sample_id, sample_name]:
                if key_to_try in subtract_spectra_dict:
                    spectrum_to_subtract = subtract_spectra_dict[key_to_try]
                    break

        if spectrum_to_subtract is not None:
            y_data_subtract = spectrum_to_subtract.spectral_data
            if len(spectrum.spectral_data) == len(y_data_subtract):
                spectrum.spectral_data = spectrum.spectral_data - y_data_subtract

        if rp_pipeline is not None:
            spectrum = rp_pipeline.apply(spectrum)

        spectra[sample_name] = spectrum

    if not spectra:
        raise ValueError(
            "No valid spectra found to plot. Check your data directory and filtering conditions."
        )

    return spectra


def plot_spectra(
    spectra: dict,
    data_dir: str | Path,
    colors=None,
    y_offset: float = 0,
    **plotting_kwargs,
):
    """
    Plot a dict of RamanSPy spectra using Plotly.

    Inputs:
        spectra: dict mapping sample name (str) to ramanspy.Spectrum,
            as returned by process_spectra_from_dir
        data_dir: str or pathlib.Path, used for group-based coloring via sample_table.csv
        colors: list of str, colors for each group. Defaults to Plotly D3 palette
        y_offset: float, vertical offset per group for visual separation (default 0)
        plotting_kwargs: additional keyword arguments passed to fig.update_layout

    Returns:
        fig: plotly Figure
    """
    if colors is None:
        colors = px.colors.qualitative.D3

    data_path = Path(data_dir)
    sample_table_path = data_path / "sample_table.csv"
    if not sample_table_path.exists():
        raise FileNotFoundError(f"sample_table.csv not found in {data_dir}")

    sample_table = pd.read_csv(
        sample_table_path, index_col=0, dtype={"ID": str, "Name": str, "Group ID": int}
    )
    # Factorizing is needed because Group IDs may not be contiguous integers starting at 0
    sample_table["Group ID factorized"] = pd.factorize(sample_table["Group ID"])[0]
    name_to_group = dict(
        zip(sample_table["Name"], sample_table["Group ID factorized"], strict=False)
    )

    fig = go.Figure()

    for i, (data_name, spectrum) in enumerate(spectra.items()):
        x_data = spectrum.spectral_axis
        y_data = spectrum.spectral_data
        group_label = name_to_group.get(data_name, i)

        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data + y_offset * group_label,
                name=data_name,
                line=dict(color=colors[group_label % len(colors)]),
                text=data_name.replace(" ", "<br>"),
                hoverinfo="text+x+y",
            )
        )

    fig.update_layout(
        showlegend=True,
        title_text=data_path.parent.name,
        template="plotly_white",
        **plotting_kwargs,
    )

    return fig


def plot_spectra_in_dir(
    data_list,
    data_dir: str | Path,
    x_to_plot: str = "Wavenumber",
    col_to_plot: str = "Intensity",
    rp_pipeline=None,
    include: list | None = None,
    colors=None,
    subtract_id: str | dict | None = None,
    y_offset=0,
    **plotting_kwargs,
):
    """
    Preprocess and plot spectra from a directory.

    Inputs:
        data_list: list of (filename, pd.DataFrame) tuples
        data_dir: pathlib.Path, directory with files
        x_to_plot: str, column to use as spectral axis (default "Wavenumber")
        col_to_plot: str, column to use as intensity values
        rp_pipeline: ramanspy.preprocessing.Pipeline (optional)
        include: list of sample names to include; must match 'Name' in sample_table.csv (optional)
        colors: list of str, colors for each group (optional)
        subtract_id: str or dict for background subtraction (optional)
        y_offset: float, vertical offset per group (default 0)
        plotting_kwargs: additional keyword arguments for fig.update_layout

    Returns:
        fig: plotly Figure
        spectra_names: list of str, names of processed spectra in plot order
        spectral_container: ramanspy.SpectralContainer with all plotted spectra
    """
    spectra = process_spectra_from_dir(
        data_list, data_dir, x_to_plot, col_to_plot, rp_pipeline, include, subtract_id
    )
    fig = plot_spectra(spectra, data_dir, colors, y_offset, **plotting_kwargs)
    spectra_names = list(spectra.keys())
    spectral_container = rp.SpectralContainer.from_stack(list(spectra.values()))
    return fig, spectra_names, spectral_container


def parse_instantraman_output(file_path):
    """
    Parse InstantRaman output CSV. Expects columns ['Pixel', 'Intensity'] where
    Pixel is actually wavenumber (instrument firmware quirk).
    """
    df = pd.read_csv(file_path)
    if "Wavenumber" not in df.columns and "Pixel" in df.columns:
        print("Warning: 'Pixel' column found, renaming to 'Wavenumber'.")
        df.rename(columns={"Pixel": "Wavenumber"}, inplace=True)

    if not _is_like_spectrum(df):
        print(
            f"Warning: {file_path} does not resemble a spectrum. "
            "Expected at least two numeric columns. Ignoring this file."
        )
        return None
    return df


def _is_like_spectrum(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    return len(numeric_cols) >= 2
