"""IO for atrophy z-scoring: find each subject's segment files, load NIfTIs and control stats, save maps BIDS-style beside the inputs."""
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import nibabel as nib
import numpy as np
import pandas as pd


### Finding files ###

def subject_session_key(path: Path) -> str:
    """'sub-01/ses-01' from the first subject and session folders in the path; falls back to the subject folder, then the whole path."""
    subject = next((part for part in path.parts if part.startswith(("sub-", "subject-", "subid-"))), None)
    session = next((part for part in path.parts if part.startswith("ses-")), None)
    if subject and session:
        return f"{subject}/{session}"
    return subject or str(path)

def find_segment_files(root: Path, pattern: str) -> Dict[str, Path]:
    """Files matching root/pattern, keyed by subject/session."""
    return {subject_session_key(Path(path)): Path(path) for path in sorted(glob(str(root / pattern)))}

def find_tissue_files(root: Path, gm_pattern: str, wm_pattern: str, csf_pattern: str) -> Dict[str, Dict[str, Path]]:
    """Segment files for each tissue, keyed by subject/session."""
    return {"grey_matter": find_segment_files(root, gm_pattern), "white_matter": find_segment_files(root, wm_pattern), "cerebrospinal_fluid": find_segment_files(root, csf_pattern)}

def subjects_with_all_tissues(tissue_files: Dict[str, Dict[str, Path]]) -> List[str]:
    """Sorted subject/session keys that have a GM, a WM and a CSF file."""
    return sorted(set.intersection(*(set(files) for files in tissue_files.values())))


### Loading ###

def load_nifti_vector(path: Path) -> np.ndarray:
    """A NIfTI flattened to one value per voxel."""
    return np.asarray(nib.load(str(path)).get_fdata()).flatten()

def load_tissue(files: Dict[str, Path], subjects: List[str]) -> pd.DataFrame:
    """Voxels x subjects for one tissue. Columns are the file paths, which later decide where outputs are saved."""
    return pd.DataFrame(np.stack([load_nifti_vector(files[subject]) for subject in subjects], axis=1), columns=[str(files[subject]) for subject in subjects])

def load_segments(tissue_files: Dict[str, Dict[str, Path]], subjects: List[str]) -> Dict[str, pd.DataFrame]:
    """Voxels x subjects for every tissue."""
    return {tissue: load_tissue(files, subjects) for tissue, files in tissue_files.items()}

def resolve_stat_path(stats_dir: Optional[Path], override: Optional[Path], name: str) -> Path:
    """The override if given, else stats_dir/<name>.nii, else stats_dir/<name>.nii.gz."""
    if override:
        return override
    if not stats_dir:
        raise SystemExit(f"Missing control stat {name}: provide --control-stats-dir or that stat's override flag.")
    for path in (stats_dir / f"{name}.nii", stats_dir / f"{name}.nii.gz"):
        if path.exists():
            return path
    raise SystemExit(f"Missing control stat file: {stats_dir / name}.nii or .nii.gz")

def load_stat(stats_dir: Optional[Path], overrides: Dict[str, Optional[Path]], name: str) -> np.ndarray:
    """One control stat as a voxel vector."""
    return load_nifti_vector(resolve_stat_path(stats_dir, overrides[name], name))

def load_control_stats(stats_dir: Optional[Path], overrides: Dict[str, Optional[Path]]) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Control (mean, std) voxel vectors per tissue, plus the composite's from the norm_mean / norm_std files."""
    file_stems = {"grey_matter": "grey_matter", "white_matter": "white_matter", "cerebrospinal_fluid": "cerebrospinal_fluid", "composite": "norm"}
    return {key: (load_stat(stats_dir, overrides, f"{stem}_mean"), load_stat(stats_dir, overrides, f"{stem}_std")) for key, stem in file_stems.items()}


### Saving ###

def strip_subject_prefix(folder: str) -> str:
    """'sub-01', 'subject-01' or 'subid-01' -> '01'; any other folder name is returned unchanged."""
    for prefix in ("subject-", "subid-", "sub-"):
        if folder.startswith(prefix):
            return folder[len(prefix):]
    return folder

def bids_output_path(root: Path, input_path: str, analysis: str, name: str) -> Path:
    """root/<subject>/<session>/<analysis>/sub-<id>_<session>_<name>.nii.gz, where <subject>/<session> are the input's first two folders under root."""
    subject_folder, session_folder = Path(input_path).relative_to(root).parts[:2]
    return root / subject_folder / session_folder / analysis / f"sub-{strip_subject_prefix(subject_folder)}_{session_folder}_{name}.nii.gz"

def save_nifti(values: np.ndarray, mask: nib.Nifti1Image, path: Path) -> None:
    """Reshape a voxel vector to the mask's grid and save it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(values.reshape(mask.shape), mask.affine), str(path))
    print(f"Saved: {path}")

def save_maps(maps: Dict[str, pd.DataFrame], root: Path, mask_path: Path, analysis: str) -> None:
    """Save every subject's map for every tissue/composite beside that subject's inputs."""
    mask = nib.load(str(mask_path))
    for name, frame in maps.items():
        for input_path in frame.columns:
            save_nifti(frame[input_path].values, mask, bids_output_path(root, input_path, analysis, name))
