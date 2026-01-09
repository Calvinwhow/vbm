#!/usr/bin/env python3
"""
Compute regional atrophy (mean unthresholded composite Z) per ROI for each subject/session.
Outputs a CSV with columns: ROI, Atrophy_Z, sorted by descending Atrophy_Z.
"""

import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple

import nibabel as nib
import numpy as np
import pandas as pd

DEFAULT_MASK = Path("/root/assets/MNI152_T1_2mm_brain_mask.nii")
DEFAULT_ROI_DIR = Path("/root/assets/rois")
DEFAULT_BASE = Path("/root/data")
DEFAULT_SUB = "sub-01"
DEFAULT_SES = "ses-01"


def _clean_roi_name(path: Path) -> str:
    stem = path.name
    if stem.endswith(".nii.gz"):
        stem = stem[:-7]
    elif stem.endswith(".nii"):
        stem = stem[:-4]
    return stem


def _load_roi_arrays(roi_paths: Iterable[Path]) -> Dict[str, np.ndarray]:
    roi_arrays: Dict[str, np.ndarray] = {}
    expected_len = None
    for roi_path in roi_paths:
        try:
            data = nib.load(str(roi_path)).get_fdata().flatten()
        except Exception as exc:
            print(f"Warning: failed to load ROI {roi_path}: {exc}. Filling with NaNs.")
            if expected_len is not None:
                roi_arrays[_clean_roi_name(roi_path)] = np.full(expected_len, np.nan, dtype=float)
            continue
        if expected_len is None:
            expected_len = data.shape[0]
        if data.shape[0] != expected_len:
            print(f"Warning: ROI {roi_path} length {data.shape[0]} != expected {expected_len}. Filling with NaNs.")
            roi_arrays[_clean_roi_name(roi_path)] = np.full(expected_len, np.nan, dtype=float)
            continue
        roi_arrays[_clean_roi_name(roi_path)] = data
    return roi_arrays


def _find_composite_maps(base_dir: Path, session: str) -> Iterable[Path]:
    """Searches <sub>/<ses>/<unthresholded...>/<composite.nii>"""
    pattern = f"*/{session}/unthresholded_tissue_segment_z_scores/*_composite.nii*"
    return base_dir.glob(pattern)


def _extract_sub_ses_from_path(path: Path) -> Tuple[str, str]:
    """Expects .../<sub>/<ses>/unthresholded_tissue_segment_z_scores/..."""
    relpath = path.relative_to(DEFAULT_BASE)  # will raise if not under base
    if len(relpath.parts) < 2:
        print(f"Path {path} does not contain <sub>/<ses> under {DEFAULT_BASE}. Creating at {relpath.parts[0] if relpath.parts else '<missing>'}/{DEFAULT_SES}")
        sub = relpath.parts[0] if relpath.parts else "sub-unknown"
        ses = DEFAULT_SES
    else:
        sub = relpath.parts[0]
        ses = relpath.parts[1]
    return sub, ses


def compute_roi_means(composite_path: Path, roi_arrays: Dict[str, np.ndarray]) -> pd.DataFrame:
    """Expects a binary ROI mask"""
    comp_img = nib.load(str(composite_path))
    comp_data = comp_img.get_fdata().flatten()

    rows = []
    for roi_name, roi_data in roi_arrays.items():
        if roi_data.shape != comp_data.shape:
            print(f"Warning: shape mismatch for ROI {roi_name}: roi {roi_data.shape}, composite {comp_data.shape}. Recording NaN.")
            rows.append((roi_name, np.nan))
            continue
        
        roi_mask = (roi_data > 0) & np.isfinite(roi_data)
        if roi_mask.sum() == 0:
            print(f"ROI {roi_name} is empty. Leaving average as NAN")
            rows.append((roi_name, np.nan))
            continue
        
        comp_vals = comp_data[roi_mask & np.isfinite(comp_data)]
        if comp_vals.size == 0:
            print(f"ROI {roi_name} has no finite composite voxels. Recording NaN.")
            rows.append((roi_name, np.nan))
            continue
        roi_mean = np.nanmean(comp_vals)
        rows.append((roi_name, roi_mean))

    df = pd.DataFrame(rows, columns=["ROI", "Atrophy_Z"])
    return df.sort_values(by="Atrophy_Z", ascending=False).reset_index(drop=True)


def save_roi_csv(df: pd.DataFrame, base_dir: Path, sub: str, ses: str, fname: str) -> Path:
    out_dir = base_dir / sub / ses / "measurements"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{fname}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Measure regional atrophy (mean composite Z per ROI).")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE, help="BIDS root (default: /root/data).")
    parser.add_argument("--session", default=DEFAULT_SES, help="Session label (e.g., ses-01).")
    parser.add_argument("--roi-dir", type=Path, default=DEFAULT_ROI_DIR, help="Directory containing ROI NIfTIs.")
    parser.add_argument("--mask-path", type=Path, default=DEFAULT_MASK, help="Brain mask (for DamageScorer init).")
    parser.add_argument("--fname", type=str, default="regional_atrophy", help="Name for output csv.")
    args = parser.parse_args()

    base_dir = args.base_dir

    # Collect ROI masks
    roi_paths = sorted(p for p in args.roi_dir.rglob("*.nii*") if p.is_file())
    if not roi_paths:
        raise SystemExit(f"No ROI NIfTI files found under {args.roi_dir}")
    
    # Build ROI arrays and clean names
    roi_arrays = _load_roi_arrays(roi_paths)
    roi_df = pd.DataFrame({name: arr for name, arr in roi_arrays.items()})

    # Measure Atrophy in Each Composite Atrophy File
    composites = list(_find_composite_maps(base_dir, args.session))
    if not composites:
        raise SystemExit(f"No composite maps found under {base_dir} for session {args.session}")
    for comp_path in composites:
        sub, ses = _extract_sub_ses_from_path(comp_path)
        df = compute_roi_means(comp_path, roi_df)
        out_path = save_roi_csv(df, base_dir, sub, ses, args.fname)
        print(f"Saved ROI means for {sub}/{ses} to {out_path}")


if __name__ == "__main__":
    main()
