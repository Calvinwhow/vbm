"""Processing: per-voxel atrophy z-scores for each tissue, and the composite atrophy score.

Convention: a positive z-score means atrophy in every tissue (less GM / WM, more CSF than controls).
"""
from typing import Dict, Tuple

import numpy as np
import pandas as pd


def voxel_mean_std(frame: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Mean and population std (ddof=0) across subjects, per voxel."""
    return frame.values.mean(axis=1), frame.values.std(axis=1)

def zscore(frame: pd.DataFrame, mean: np.ndarray, std: np.ndarray) -> pd.DataFrame:
    """(value - mean) / std per voxel, for every subject."""
    return pd.DataFrame((frame.values - mean[:, np.newaxis]) / std[:, np.newaxis], index=frame.index, columns=frame.columns)

def orient_atrophy_positive(zscores: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Negate GM and WM so tissue loss is positive. CSF already is: expansion is positive."""
    return {tissue: frame if tissue == "cerebrospinal_fluid" else -frame for tissue, frame in zscores.items()}

def tissue_atrophy_zscores(preprocessed: Dict[str, pd.DataFrame], control_stats: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> Dict[str, pd.DataFrame]:
    """Atrophy z-score per voxel for each tissue against the controls."""
    return orient_atrophy_positive({tissue: zscore(frame, *control_stats[tissue]) for tissue, frame in preprocessed.items()})

def atrophy_norm(zscores: Dict[str, pd.DataFrame], atrophy_only: bool, exclude_wm:bool=True) -> np.ndarray:
    """Voxels x subjects: L2 norm of the GM and CSF z-scores (WM is left out). With atrophy_only, only positive (atrophic) z-scores count."""
    if exclude_wm:
        stacked = np.stack([zscores["grey_matter"].values, zscores["cerebrospinal_fluid"].values], axis=2)
    else:
        stacked = np.stack([zscores["grey_matter"].values, zscores["white_matter"].values, zscores["cerebrospinal_fluid"].values], axis=2)
    if atrophy_only:
        stacked = np.where(stacked > 0, stacked, 0)
    return np.sqrt(np.sum(stacked ** 2, axis=2))

def composite_zscore(zscores: Dict[str, pd.DataFrame], composite_stats: Tuple[np.ndarray, np.ndarray], atrophy_only: bool) -> pd.DataFrame:
    """Each subject's atrophy norm z-scored against the controls' norm. Columns follow the GM files."""
    norms = pd.DataFrame(atrophy_norm(zscores, atrophy_only), index=zscores["grey_matter"].index, columns=zscores["grey_matter"].columns)
    return zscore(norms, *composite_stats)

def norm_stats(control_zscores: Dict[str, pd.DataFrame], atrophy_only: bool) -> Tuple[np.ndarray, np.ndarray]:
    """Per-voxel mean and population std (ddof=0) of the controls' atrophy norm."""
    control_norm = atrophy_norm(control_zscores, atrophy_only)
    return control_norm.mean(axis=1), control_norm.std(axis=1)

def generate_norm_map(patient_zscores: Dict[str, pd.DataFrame], control_zscores: Dict[str, pd.DataFrame], atrophy_only: bool) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Patients' composite z (atrophy norm vs the controls' norm), plus the control norm mean and std. Both inputs must be atrophy-positive z-scores."""
    mean, std = norm_stats(control_zscores, atrophy_only)
    return composite_zscore(patient_zscores, (mean, std), atrophy_only), mean, std

def atrophy_zscores(preprocessed: Dict[str, pd.DataFrame], control_stats: Dict[str, Tuple[np.ndarray, np.ndarray]], atrophy_only: bool) -> Dict[str, pd.DataFrame]:
    """Atrophy z-scores for grey_matter, white_matter, cerebrospinal_fluid and the composite."""
    zscores = tissue_atrophy_zscores(preprocessed, control_stats)
    return {**zscores, "composite": composite_zscore(zscores, control_stats["composite"], atrophy_only)}

def control_stats_from_scans(preprocessed_controls: Dict[str, pd.DataFrame], atrophy_only: bool) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """The same (mean, std) stats a --control-stats-dir holds, computed from control scans: per tissue, and for the controls' own atrophy norm."""
    tissue_stats = {tissue: voxel_mean_std(frame) for tissue, frame in preprocessed_controls.items()}
    return {**tissue_stats, "composite": norm_stats(tissue_atrophy_zscores(preprocessed_controls, tissue_stats), atrophy_only)}
