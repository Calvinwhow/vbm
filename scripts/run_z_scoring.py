#!/usr/bin/env python3
"""
Atrophy z-scores per voxel for grey matter, white matter, CSF and a composite, for every subject, against a control distribution.

Convention: positive z = atrophy in every tissue (less GM / WM, more CSF than controls).

main() runs: 1) argparse  2) IO: find and load  3) preprocess  4) process  5) postprocess  6) IO: save

Control distribution, one of:
    --control-stats-dir   precomputed <tissue>_mean / <tissue>_std and norm_mean / norm_std NIfTIs (.nii or .nii.gz); single files can be overridden (--gm-mean, ...)
    --controls-root       control segment files; the same stats are computed from them

Outputs, written beside each subject's inputs:
    <root>/<sub>/<ses>/unthresholded_tissue_segment_z_scores/sub-<id>_<ses>_<map>.nii.gz
    <root>/<sub>/<ses>/thresholded_tissue_segment_z_scores/sub-<id>_<ses>_<map>.nii.gz
    <map> is grey_matter, white_matter, cerebrospinal_fluid or composite.

Called by scripts/run_pipeline.sh (docker-compose) and notebooks/02_atrophy_quick.ipynb.
"""
import argparse
from pathlib import Path
from typing import Dict, List, Optional

from atrophy_io import find_tissue_files, subjects_with_all_tissues, load_segments, load_control_stats, save_maps
from atrophy_preprocess import preprocess_segments
from atrophy_process import atrophy_zscores, control_stats_from_scans
from atrophy_postprocess import threshold_maps


### 1) argparse ###

def parse_bool(value: str) -> bool:
    """'true' / 'false' in any case; anything else is an error."""
    if value.lower() not in ("true", "false"):
        raise argparse.ArgumentTypeError(f"Expected true or false, got: {value}")
    return value.lower() == "true"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Atrophy z-scores (GM, WM, CSF, composite) against a control distribution.")
    parser.add_argument("--experiments-root", type=Path, required=True, help="Root folder shared by all patients. Patterns are relative to it, and outputs are written under it.")
    parser.add_argument("--experiments-gm-pattern", default="*/*/anat/mri/mwp1*", help="Glob under --experiments-root for patient grey matter files.")
    parser.add_argument("--experiments-wm-pattern", default="*/*/anat/mri/mwp2*", help="Glob under --experiments-root for patient white matter files.")
    parser.add_argument("--experiments-csf-pattern", default="*/*/anat/mri/mwp3*", help="Glob under --experiments-root for patient CSF files.")
    parser.add_argument("--control-stats-dir", type=Path, default=None, help="Folder of precomputed control stats: <tissue>_mean, <tissue>_std, norm_mean, norm_std (.nii or .nii.gz). With --atrophy-only true, <folder>_atrophy_only is used unless the name already contains _atrophy_only.")
    parser.add_argument("--gm-mean", type=Path, default=None, help="Override file for grey_matter_mean.")
    parser.add_argument("--gm-std", type=Path, default=None, help="Override file for grey_matter_std.")
    parser.add_argument("--wm-mean", type=Path, default=None, help="Override file for white_matter_mean.")
    parser.add_argument("--wm-std", type=Path, default=None, help="Override file for white_matter_std.")
    parser.add_argument("--csf-mean", type=Path, default=None, help="Override file for cerebrospinal_fluid_mean.")
    parser.add_argument("--csf-std", type=Path, default=None, help="Override file for cerebrospinal_fluid_std.")
    parser.add_argument("--composite-mean", type=Path, default=None, help="Override file for norm_mean.")
    parser.add_argument("--composite-std", type=Path, default=None, help="Override file for norm_std.")
    parser.add_argument("--controls-root", type=Path, default=None, help="Root folder of control segments. Used only when no precomputed control stats are given.")
    parser.add_argument("--controls-gm-pattern", default="*/*/anat/mri/mwp1*", help="Glob under --controls-root for control grey matter files.")
    parser.add_argument("--controls-wm-pattern", default="*/*/anat/mri/mwp2*", help="Glob under --controls-root for control white matter files.")
    parser.add_argument("--controls-csf-pattern", default="*/*/anat/mri/mwp3*", help="Glob under --controls-root for control CSF files.")
    parser.add_argument("--mask-path", type=Path, default=Path("/root/assets/MNI152_T1_2mm_brain_mask.nii"), help="Reference NIfTI whose grid and affine the outputs use.")
    parser.add_argument("--session", type=str, default="ses-01", help="Not used: output session folders come from each input's path.")
    parser.add_argument("--atrophy-only", type=parse_bool, required=True, help="true: the composite counts only atrophic z-scores. false: it counts deviations in both directions.")
    return parser


### 2) IO: find and load ###

def require_mask(mask_path: Path) -> None:
    if not mask_path.exists():
        raise SystemExit(f"Mask not found: {mask_path}")

def require_subjects(subjects: List[str], label: str) -> List[str]:
    if not subjects:
        raise SystemExit(f"No overlapping {label} subjects found across GM/WM/CSF patterns.")
    return subjects

def stat_overrides(args: argparse.Namespace) -> Dict[str, Optional[Path]]:
    """Override files from the command line, keyed by the control stat they replace."""
    return {"grey_matter_mean": args.gm_mean, "grey_matter_std": args.gm_std, "white_matter_mean": args.wm_mean, "white_matter_std": args.wm_std, "cerebrospinal_fluid_mean": args.csf_mean, "cerebrospinal_fluid_std": args.csf_std, "norm_mean": args.composite_mean, "norm_std": args.composite_std}

def preprocessed_controls(args: argparse.Namespace) -> dict:
    """Control segments found, loaded and preprocessed exactly like the patients."""
    control_files = find_tissue_files(args.controls_root, args.controls_gm_pattern, args.controls_wm_pattern, args.controls_csf_pattern)
    subjects = require_subjects(subjects_with_all_tissues(control_files), "control")
    return preprocess_segments(load_segments(control_files, subjects))

def matching_control_stats_dir(stats_dir: Optional[Path], atrophy_only: bool) -> Optional[Path]:
    """With atrophy_only, the '<name>_atrophy_only' sibling of the given control stats folder, unless its name already contains '_atrophy_only'."""
    if stats_dir and atrophy_only and "_atrophy_only" not in stats_dir.name:
        print(f"atrophy_only: using {stats_dir.name}_atrophy_only instead of {stats_dir.name}")
        return stats_dir.with_name(f"{stats_dir.name}_atrophy_only")
    return stats_dir

def get_control_stats(args: argparse.Namespace) -> dict:
    """Precomputed stats if any stat folder or file is given; otherwise stats computed from --controls-root."""
    overrides = stat_overrides(args)
    if args.control_stats_dir or any(overrides.values()):
        return load_control_stats(matching_control_stats_dir(args.control_stats_dir, args.atrophy_only), overrides)
    if args.controls_root:
        return control_stats_from_scans(preprocessed_controls(args), args.atrophy_only)
    raise SystemExit("Provide either a control directory or pre-calculated control stats.")

def batches(subjects: List[str], batch_size: int = 100) -> List[List[str]]:
    """Consecutive chunks of at most batch_size subjects, so memory stays bounded."""
    return [subjects[start:start + batch_size] for start in range(0, len(subjects), batch_size)]


### Main ###

def main() -> None:
    # 1) argparse
    args = build_parser().parse_args()
    require_mask(args.mask_path)

    # 2) IO: find patients and control stats
    patient_files = find_tissue_files(args.experiments_root, args.experiments_gm_pattern, args.experiments_wm_pattern, args.experiments_csf_pattern)
    subjects = require_subjects(subjects_with_all_tissues(patient_files), "experimental")
    control_stats = get_control_stats(args)

    for batch in batches(subjects):
        # 2) IO: load
        segments = load_segments(patient_files, batch)

        # 3) preprocess
        preprocessed = preprocess_segments(segments)

        # 4) process
        zscores = atrophy_zscores(preprocessed, control_stats, args.atrophy_only)

        # 5) postprocess
        thresholded = threshold_maps(zscores)

        # 6) IO: save
        save_maps(zscores, args.experiments_root, args.mask_path, "unthresholded_tissue_segment_z_scores")
        save_maps(thresholded, args.experiments_root, args.mask_path, "thresholded_tissue_segment_z_scores")


if __name__ == "__main__":
    main()
