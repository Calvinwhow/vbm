"""Preprocessing: zero near-empty tissue probabilities, then normalise each subject by total intracranial volume (TIV)."""
from typing import Dict

import numpy as np
import pandas as pd


def total_intracranial_volume(segments: Dict[str, pd.DataFrame], voxel_size_mm: float = 2.0) -> np.ndarray:
    """Per subject: GM + WM + CSF summed over all voxels, times the voxel volume (mm^3)."""
    tissue_sum = segments["grey_matter"].values + segments["white_matter"].values + segments["cerebrospinal_fluid"].values
    return tissue_sum.sum(axis=0) * voxel_size_mm ** 3

def zero_low_probabilities(frame: pd.DataFrame, prob_threshold: float) -> pd.DataFrame:
    """Voxels at or below the probability threshold become 0, which avoids huge z-scores from near-empty voxels."""
    return frame.where(frame > prob_threshold, 0)

def preprocess_segments(segments: Dict[str, pd.DataFrame], prob_threshold: float = 0.001) -> Dict[str, pd.DataFrame]:
    """Threshold every tissue, then divide each subject by its TIV (TIV is taken from the unthresholded segments)."""
    tiv = total_intracranial_volume(segments)
    return {tissue: zero_low_probabilities(frame, prob_threshold).div(tiv, axis="columns") for tissue, frame in segments.items()}
