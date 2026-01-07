#!/usr/bin/env python3
"""
Explanation for Z-scoring Pipeline for VBM Analysis
This script implements a voxel-based morphometry (VBM) z-scoring pipeline that calculates
tissue atrophy scores by comparing experimental subjects against a control distribution.
Quick Start:
    python run_z_scoring.py \\
        --experiments-root /path/to/experimental/segments \\
        --controls-root /path/to/control/segments
Key Parameters:
Input Data:
    --experiments-root (required): Path to experimental subject tissue segments (MWP files)
    --controls-root (optional): Path to control subject tissue segments. Required unless
                                pre-calculated statistics are provided.
Control Statistics:
    --control-stats-dir: Directory containing pre-calculated normative distributions
                        (grey_matter_mean.nii, grey_matter_std.nii, etc.)
    --gm-mean, --gm-std, --wm-mean, --wm-std, --csf-mean, --csf-std,
    --composite-mean, --composite-std: Individual override paths for specific statistics
File Matching Patterns:
    --controls-gm-pattern, --controls-wm-pattern, --controls-csf-pattern: Glob patterns
                                                                           for control files
    --experiments-gm-pattern, --experiments-wm-pattern, --experiments-csf-pattern: Glob
                                                                                    patterns for experimental files
Subject ID Processing:
    --pre-subject-str: String prefix to remove from column names (default: "")
    --post-subject-str: String suffix to remove from column names (default: "_mwp")
Output Options:
    --session: Session label for BIDS output (default: "ses-01")
    --mask-path: Reference mask for NIfTI output (default: root/assets/MNI152_T1_2mm_brain_mask.nii)
    --unthresholded-analysis: Output folder name for z-scores (default: unthresholded_tissue_segment_z_scores)
    --thresholded-analysis: Output folder name for thresholded z-scores (default: thresholded_tissue_segment_z_scores)
    --dry-run: Preview output paths without writing files
Outputs:
    Z-scored NIfTI files for grey matter, white matter, CSF, and composite atrophy measures
    saved in BIDS format under the specified analysis directories.
"""
from __future__ import annotations
import os
import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

import nibabel as nib
from calvin_utils.file_utils.import_functions import GiiNiiFileImport
from calvin_utils.nifti_utils.matrix_utilities import import_nifti_to_numpy_array
from calvin_utils.vbm_utils.composite_atrophy_mapper import generate_norm, generate_norm_map, generate_tensor, prepocess_dict
from calvin_utils.vbm_utils.loading import import_segments
from calvin_utils.vbm_utils.processing import get_tiv, process_atrophy, process_tissue, save_nifti_to_bids

DEFAULT_MASK = Path("/root/assets/MNI152_T1_2mm_brain_mask.nii")

def load_segments(label: str, base_dir: Path, gm_pattern: str, wm_pattern: str, csf_pattern: str) -> Dict[str, "pd.DataFrame"]:
    """
    Loads in each patient's MWP file into a dataframe, 
    
    :param label: Corresponds to whether experimental or control patients are being loaded. For logging only. 
    :param base_dir: The root to start globbing from.
    :param gm_pattern: File match for grey matter. 
    :param wm_pattern: File match for white matter. 
    :param csf_pattern: File match for CSF. 
    :return: Dictionary with a K:V pair for each MWP segment, where keys are dataframes for the corresponding segment
    """
    print(f"Loading {label} segments from {base_dir} ...")
    segments = import_segments(base_dir=str(base_dir), gm_pattern=gm_pattern, wm_pattern=wm_pattern, csf_pattern=csf_pattern, full_path=True)
    return segments

def run_pipeline(args: argparse.Namespace) -> None:
    """
    Orchestrator
    
    :param args: Args passed from the command line. 
    """
    # Prep
    use_precalc_stats = any(
        [
            args.control_stats_dir,
            args.gm_mean,
            args.gm_std,
            args.wm_mean,
            args.wm_std,
            args.csf_mean,
            args.csf_std,
            args.composite_mean,
            args.composite_std,
        ]
    )
    if not use_precalc_stats and not args.controls_root:
        raise SystemExit("Provide either a control directory or pre-calculated control stats.")

    # Imports
    ctrl_segments = None
    if not use_precalc_stats:
        ctrl_segments = load_segments(
            label="control",
            base_dir=args.controls_root,
            gm_pattern=args.controls_gm_pattern,
            wm_pattern=args.controls_wm_pattern,
            csf_pattern=args.controls_csf_pattern
        )

    expt_segments = load_segments(
        label="experimental",
        base_dir=args.experiments_root,
        gm_pattern=args.experiments_gm_pattern,
        wm_pattern=args.experiments_wm_pattern,
        csf_pattern=args.experiments_csf_pattern
    )

    # Atrophy Calculation
    if use_precalc_stats:
        stats = load_control_stats(args)
        atrophy, atrophy_thresholded = compute_z_with_precalc_stats(expt_segments, stats)
        composite = compute_composite_with_precalc_stats(atrophy, stats)
    else:
        atrophy, atrophy_thresholded, _ = process_atrophy(expt_segments, ctrl_segments)
        z_ctrl, _, _ = process_atrophy(data_dict=ctrl_segments, ctrl_dict=ctrl_segments)
        composite, _, _ = generate_norm_map(pt_dict=atrophy, ctrl_dict=z_ctrl)
    atrophy["composite"] = composite
    atrophy_thresholded["composite"] = composite.where(composite > 0, 0)

    # Save outputs
    save_df_to_nifti_bids(
        atrophy,
        root=args.experiments_root,
        mask_path=args.mask_path,
        analysis="unthresholded_tissue_segment_z_scores",
        ses=args.session,
    )
    save_df_to_nifti_bids(
        atrophy_thresholded,
        root=args.experiments_root,
        mask_path=args.mask_path,
        analysis="thresholded_tissue_segment_z_scores",
        ses=args.session,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Z-scoring pipeline from notebook 02A.")
    # Args for Globbing out Individual Tissue Segments
    parser.add_argument("--controls-root", type=Path, required=False, 
                        help="Base path (glob allowed) to control tissue segments (e.g. /.../BIDS/sub-*/*/mri).")
    parser.add_argument("--experiments-root", type=Path, required=True,
        help="Base path (glob allowed) to experimental tissue segments.")
    
    # Args for Precalculated Normative Distributions. Overrides use of control segments
    parser.add_argument("--control-stats-dir", type=Path, default=None,
        help="Directory containing pre-calculated control means/stds (expects <tissue>_mean.nii, <tissue>_std.nii, norm_mean.nii, norm_std.nii).")
    # Additional optional inputs to directly overried the generic precalculated files. Defaults to None. 
    parser.add_argument("--gm-mean", type=Path, default=None, 
                        help="Optional override path for grey matter mean NIfTI.")
    parser.add_argument("--gm-std", type=Path, default=None, 
                        help="Optional override path for grey matter std NIfTI.")
    parser.add_argument("--wm-mean", type=Path, default=None, 
                        help="Optional override path for white matter mean NIfTI.")
    parser.add_argument("--wm-std", type=Path, default=None, 
                        help="Optional override path for white matter std NIfTI.")
    parser.add_argument("--csf-mean", type=Path, default=None, 
                        help="Optional override path for CSF mean NIfTI.")
    parser.add_argument("--csf-std", type=Path, default=None, 
                        help="Optional override path for CSF std NIfTI.")
    parser.add_argument("--composite-mean", type=Path, default=None, 
                        help="Optional override path for composite norm mean NIfTI.")
    parser.add_argument("--composite-std", type=Path, default=None, 
                        help="Optional override path for composite norm std NIfTI.")

    # Args for Globbing out MWP files
    parser.add_argument("--controls-gm-pattern", default="*/*/anat/mri/mwp1*", 
                        help="Glob for control grey matter files.")
    parser.add_argument("--controls-wm-pattern", default="*/*/anat/mri/mwp2*", 
                        help="Glob for control white matter files.")
    parser.add_argument("--controls-csf-pattern", default="*/*/anat/mri/mwp3*", 
                        help="Glob for control CSF files.")
    parser.add_argument("--experiments-gm-pattern", default="*/*/anat/mri/mwp1*", 
                        help="Glob for experimental grey matter files.")
    parser.add_argument("--experiments-wm-pattern", default="*/*/anat/mri/mwp2*", 
                        help="Glob for experimental white matter files.")
    parser.add_argument("--experiments-csf-pattern", default="*/*/anat/mri/mwp3*", 
                        help="Glob for experimental CSF files.")

    # Args for extracting subject ID 
    parser.add_argument("--pre-subject-str", type=str, default="",
        help="String to drop before the subject ID in column names (passed to splice_colnames).")
    parser.add_argument("--post-subject-str", type=str, default="_mwp",
        help="String to drop after the subject ID in column names (passed to splice_colnames).")
   
    # Other Args
    parser.add_argument("--session", type=str, default="ses-01",
        help="Session label used when writing BIDS output (e.g. ses-01).")
    parser.add_argument("--mask-path", type=Path, default=DEFAULT_MASK,
        help=f"Reference mask for saving NIfTI outputs (default: {DEFAULT_MASK}).")
    return parser

def _resolve_stat_path(base: Path | None, override: Path | None, name: str) -> Path:
    """
    Resolve a control statistic path using an optional override or the provided base directory.
    
    :param base: Base to control statistics directory
    :param override: Optional explicit path override
    :param name: Filename for the corresponding statistic in the base directory
    :return: Path to the file to be imported
    """
    if override:
        return override
    if not base:
        raise SystemExit(f"Missing path for {name}. Provide --control-stats-dir or explicit --{name.replace('_', '-')}.")
    return base / f"{name}.nii"

def save_df_to_nifti_bids(dataframes_dict, root, mask_path, analysis='tissue_segment_z_scores', ses='ses-01'):
    """
    Saves NIFTI images to a BIDS-compliant directory structure.

    Parameters:
        dataframes_dict (dict[str, pd.DataFrame]): Dictionary mapping tissue types to DataFrames containing subject data.
        root (path): Base directory for BIDS structure.
        mask_path (str): Path to the mask file
        analysis (str, optional): Analysis folder name. Defaults to 'tissue_segment_z_scores'.
        ses (str, optional): Session identifier (e.g., 'ses-01'). Defaults to 'ses-01'.
    """
    def _extract_subid(root: Path, subj_path: str):
        """Use the first folder after root as the subject ID (strip a leading sub- if present)."""
        root = Path(root)
        subj_path = Path(subj_path)
        # Normalize to absolute under root; fail loudly if not possible.
        if not subj_path.is_absolute():
            subj_path = root / subj_path
        try:
            relative = subj_path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{subj_path} is not under root {root}; ensure columns include paths relative to {root}") from exc
        if len(relative.parts) < 2:
            raise ValueError(f"Expected subject/session folders under {root}, got: {relative}")

        first = str(relative.parts[0])
        # Strip common subject prefixes; fall back to the raw folder name.
        for prefix in ("subject-", "subid-", "sub-"):
            if first.startswith(prefix):
                subid = first[len(prefix):]
                break
        else:
            subid = first
        sesfolder = relative.parts[1]
        return subid, relative.parts[0], sesfolder
        
    def _construct_bids_path(root: Path, subfolder: Path, sesfolder: Path, subid: str, analysis: str, tissue_type: str):
        output_name = f'sub-{subid}_{sesfolder}_{tissue_type}.nii.gz'
        return os.path.join(root, subfolder, sesfolder, analysis, output_name)
    
    def _make_nifti(arr):
        mask_img = nib.load(str(mask_path))
        mask_data = mask_img.get_fdata()
        arr = arr.reshape(mask_data.shape)
        return nib.Nifti1Image(arr, mask_img.affine)

    def _save_nifti(img, out_path):
        if Path(out_path).exists():
            print(f"Skipping. File already exists: {out_path}")
            return
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        nib.save(img, out_path)
    
    for tissue_type, dataframe in dataframes_dict.items():
        for col in dataframe.columns:
            subid, subfolder, sesfolder = _extract_subid(root, col)             # expects each column to be a full path to the file
            out_path = _construct_bids_path(root, subfolder, sesfolder, subid, analysis, tissue_type)
            nii_img = _make_nifti(dataframe[col].values)
            _save_nifti(nii_img, out_path)

def _load_flattened_nifti(path: Path) -> np.ndarray:
    """
    Simple import to load a nifti directly into a flattened numpy array
    
    :param path: Path to the nifti
    :return: np array containing the flattened nifti
    """
    arr = import_nifti_to_numpy_array(str(path))
    if arr is None:
        raise SystemExit(f"Could not read NIfTI: {path}")
    return np.asarray(arr).flatten()


def load_control_stats(args: argparse.Namespace):
    """
    Loads in the precalculated normative files representing the control distribution.
    
    :param args: Args from the command line.
    :return: A dictionary with keys for each segment, and a tuple holding (mean, stdev) files
    """
    stats = {}
    stats["grey_matter"] = (
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.gm_mean, "grey_matter_mean")),
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.gm_std, "grey_matter_std")),
    )
    stats["white_matter"] = (
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.wm_mean, "white_matter_mean")),
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.wm_std, "white_matter_std")),
    )
    stats["cerebrospinal_fluid"] = (
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.csf_mean, "cerebrospinal_fluid_mean")),
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.csf_std, "cerebrospinal_fluid_std")),
    )
    stats["composite"] = (
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.composite_mean, "l2_norm_mean")),
        _load_flattened_nifti(_resolve_stat_path(args.control_stats_dir, args.composite_std, "l2_norm_std")),
    )
    return stats


def compute_z_with_precalc_stats(expt_segments: Dict[str, "pd.DataFrame"], stats: dict):
    """Calculate patient z-scores using precomputed control mean/std arrays."""
    pt_tiv = get_tiv(expt_segments)
    zscore_dict = {}
    zscore_mask_dict = {}
    for tissue, df in expt_segments.items():
        mean, std = stats[tissue]
        processed = process_tissue(df, pt_tiv)
        z_arr = (processed.values - mean[:, np.newaxis]) / std[:, np.newaxis]
        z_df = pd.DataFrame(z_arr, index=processed.index, columns=processed.columns)
        if tissue == "cerebrospinal_fluid":
            sig_mask = z_df.where(z_df > 2, 0)
        else:
            sig_mask = z_df.where(z_df < -2, 0)
        zscore_dict[tissue] = z_df
        zscore_mask_dict[tissue] = sig_mask
    return zscore_dict, zscore_mask_dict


def compute_composite_with_precalc_stats(zscore_dict: Dict[str, "pd.DataFrame"], stats: dict) -> "pd.DataFrame":
    """Compute composite Z (H-score) using precomputed control norm mean/std."""
    comp_mean, comp_std = stats["composite"]
    pt_dict_processed = prepocess_dict(zscore_dict)                    # Drops WM and sign-flips CSF. Thus, <0 is atrophy.
    pt_tensor = generate_tensor(pt_dict_processed)                     # Stacks
    pt_norm = generate_norm(pt_tensor, atrophy_only=False)              # Will only consider negative values (atrophy) 
    z = (pt_norm - comp_mean[:, np.newaxis]) / comp_std[:, np.newaxis]
    first_key = next(iter(zscore_dict))
    return pd.DataFrame(z, columns=zscore_dict[first_key].columns, index=zscore_dict[first_key].index)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.mask_path.exists():
        raise SystemExit(f"Mask not found: {args.mask_path}")

    run_pipeline(args)


if __name__ == "__main__":
    main()
