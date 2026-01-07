#!/usr/bin/env python3
"""
Classify disease by comparing patient unthresholded composite maps to archetype maps.
Uses DamageScorer spatial correlation; prediction is stubbed to a fixed disease list for now.
"""

import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple

import nibabel as nib
import numpy as np
import pandas as pd

from calvin_utils.nifti_utils.damage_score_utils import DamageScorer

DEFAULT_BASE = Path("/root/data")
DEFAULT_MASK = Path("/root/assets/MNI152_T1_2mm_brain_mask.nii")
DEFAULT_ARCHETYPE_DIR = Path("/root/assets/archetypes")
DEFAULT_SESSION = "ses-01"

DISEASES = [
    "Alzheimer",
    "Parkinson",
    "Frontotemporal dementia",
    "Dementia with Lewy bodies",
]


def _clean_name(path: Path) -> str:
    stem = path.name
    if stem.endswith(".nii.gz"):
        stem = stem[:-7]
    elif stem.endswith(".nii"):
        stem = stem[:-4]
    return stem


def _load_nifti_arrays(paths: Iterable[Path]) -> Dict[str, np.ndarray]:
    arrays: Dict[str, np.ndarray] = {}
    for p in paths:
        img = nib.load(str(p))
        arrays[_clean_name(p)] = img.get_fdata().flatten()
    return arrays


def _find_composite_maps(base_dir: Path, session: str) -> Iterable[Path]:
    pattern = f"*/*/{session}/unthresholded_tissue_segment_z_scores/*_composite.nii*"
    return base_dir.glob(pattern)


def _extract_sub_ses(path: Path) -> Tuple[str, str]:
    parts = path.parts
    for idx in range(len(parts) - 3):
        sub, ses, analysis = parts[idx], parts[idx + 1], parts[idx + 2]
        if sub.startswith("sub-") and ses.startswith("ses-") and analysis == "unthresholded_tissue_segment_z_scores":
            return sub, ses
    raise ValueError(f"Could not parse subject/session from path: {path}")


def _spatial_corrs(composite: Path, archetype_arrays: Dict[str, np.ndarray], mask_path: Path) -> Dict[str, float]:
    comp_img = nib.load(str(composite))
    comp_data = comp_img.get_fdata().flatten()

    # DamageScorer expects DataFrames with columns as subjects/rois
    dv_df = pd.DataFrame({str(composite): comp_data})
    roi_df = pd.DataFrame(archetype_arrays)

    scorer = DamageScorer(mask_path=str(mask_path), dv_df=dv_df, roi_df=roi_df)
    damage_df = scorer.calculate_damage_scores(metrics=["spatial_correlation"])

    # Columns are named <roi>_spatial_corr
    corrs = {}
    for col in damage_df.columns:
        if col.endswith("_spatial_corr"):
            roi_name = col.removesuffix("_spatial_corr")
            corrs[roi_name] = float(damage_df.iloc[0][col])
    return corrs


def _predict_disease(prob_inputs: Dict[str, float]) -> pd.DataFrame:
    """
    Placeholder for ML classification. Replace with real model using prob_inputs (spatial correlations).
    """
    df = pd.DataFrame({"Disease": DISEASES, "Probability": [0.0] * len(DISEASES)})
    return df.sort_values(by="Probability", ascending=False).reset_index(drop=True)


def _save_predictions(df: pd.DataFrame, base_dir: Path, sub: str, ses: str) -> Path:
    out_dir = base_dir / sub / ses / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "disease_classification.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main(dry_run=True):
    if dry_run:
        print("main(dry_run=True). Skipping.")
        return
    parser = argparse.ArgumentParser(description="Classify disease by spatial correlation to archetypes.")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE, help="BIDS root (default: /root/data).")
    parser.add_argument("--session", default=DEFAULT_SESSION, help="Session label (e.g., ses-01).")
    parser.add_argument("--archetype-dir", type=Path, default=DEFAULT_ARCHETYPE_DIR, help="Directory of archetype NIfTIs.")
    parser.add_argument("--mask-path", type=Path, default=DEFAULT_MASK, help="Brain mask for DamageScorer.")
    args = parser.parse_args()

    archetype_paths = sorted(p for p in args.archetype_dir.rglob("*.nii*") if p.is_file())
    if not archetype_paths:
        raise SystemExit(f"No archetype NIfTI files found under {args.archetype_dir}")

    archetype_arrays = _load_nifti_arrays(archetype_paths)

    composites = list(_find_composite_maps(args.base_dir, args.session))
    if not composites:
        raise SystemExit(f"No composite maps found under {args.base_dir} for session {args.session}")

    for comp in composites:
        sub, ses = _extract_sub_ses(comp)
        corrs = _spatial_corrs(comp, archetype_arrays, args.mask_path)
        pred_df = _predict_disease(corrs)
        out_path = _save_predictions(pred_df, args.base_dir, sub, ses)
        print(f"Saved disease classification for {sub}/{ses} to {out_path}")


if __name__ == "__main__":
    main()
