"""
Raman Analysis Package — utilities for parsing and plotting InstantRaman spectroscopy data.
"""

from .utils import collect_spectra_from_dir, plot_spectra_in_dir

__version__ = "0.1.0"
__all__ = [
    "collect_spectra_from_dir",
    "plot_spectra_in_dir",
]
