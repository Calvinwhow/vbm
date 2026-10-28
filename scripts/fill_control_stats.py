"""
Fill holes in a control-distribution folder: in-mask voxels where the control std is 0 or not finite, because no control had any signal there.

    <name>_std  holes -> the largest valid std in that map.
    <name>_mean holes -> filled inward from their borders, one voxel layer at a time: each hole voxel touching valid voxels (26-neighbourhood) takes their average, then counts as valid for the next layer.

Files are overwritten in place. Running it again changes nothing, because a filled folder has no holes.

Notebook (after the stats are saved, e.g. in 04a):  fill_control_dist(out_dir, mask)
Command line:  python fill_control_stats.py <dist_dir> --mask-path <mask.nii>
"""
import argparse
from pathlib import Path
from typing import List, Tuple

import nibabel as nib
import numpy as np
from scipy import ndimage


### IO ###

def load_nifti(path: Path) -> Tuple[nib.Nifti1Image, np.ndarray]:
    img = nib.load(str(path))
    return img, img.get_fdata()

def save_like(data: np.ndarray, template: nib.Nifti1Image, path: Path) -> None:
    """Save data with the template's affine and header (same grid and dtype)."""
    nib.save(nib.Nifti1Image(data, template.affine, template.header), str(path))
    print(f"Saved: {path}")

def mean_std_pairs(dist_dir: Path) -> List[Tuple[Path, Path]]:
    """Every <name>_mean file in the folder, paired with its <name>_std file."""
    return [(mean_path, mean_path.with_name(mean_path.name.replace("_mean.", "_std."))) for mean_path in sorted(dist_dir.glob("*_mean.nii*"))]


### Process ###

def find_holes(std: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """In-mask voxels whose std is 0, negative or not finite."""
    return mask & ~(np.isfinite(std) & (std > 0))

def fill_std(std: np.ndarray, holes: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Holes get the largest valid std inside the mask."""
    return np.where(holes, std[mask & ~holes].max(), std)

def neighbour_sum(values: np.ndarray) -> np.ndarray:
    """Sum over each voxel's 3x3x3 neighbourhood (itself included); outside the volume counts as 0."""
    return ndimage.convolve(values, np.ones((3, 3, 3)), mode="constant", cval=0.0)

def fill_mean(mean: np.ndarray, holes: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Fill holes inward from their borders, one layer per pass, each voxel taking the average of its valid in-mask neighbours."""
    filled, remaining = mean.copy(), holes.copy()
    while remaining.any():
        valid = mask & ~remaining & np.isfinite(filled)
        counts = neighbour_sum(valid.astype(float))
        sums = neighbour_sum(np.where(valid, filled, 0.0))
        layer = remaining & (counts > 0)
        if not layer.any():
            raise ValueError(f"{remaining.sum()} hole voxels have no valid voxel to fill from.")
        filled[layer] = sums[layer] / counts[layer]
        remaining &= ~layer
    return filled

def fill_pair(mean_path: Path, std_path: Path, mask: np.ndarray) -> None:
    """Fill one mean/std pair in place, using the holes of the std map for both."""
    mean_img, mean = load_nifti(mean_path)
    std_img, std = load_nifti(std_path)
    holes = find_holes(std, mask)
    print(f"{std_path.name}: {holes.sum()} hole voxels in the mask")
    save_like(fill_mean(mean, holes, mask), mean_img, mean_path)
    save_like(fill_std(std, holes, mask), std_img, std_path)

def fill_control_dist(dist_dir: str, mask_path: str) -> None:
    """Fill every <name>_mean / <name>_std pair in a control-distribution folder."""
    mask = nib.load(str(mask_path)).get_fdata() > 0
    for mean_path, std_path in mean_std_pairs(Path(dist_dir)):
        fill_pair(mean_path, std_path, mask)


### Main ###

def main() -> None:
    parser = argparse.ArgumentParser(description="Fill holes in a control-distribution folder's _mean and _std maps, in place.")
    parser.add_argument("dist_dir", type=Path, help="Folder holding <name>_mean / <name>_std NIfTIs (e.g. assets/ctrl_dist_young_atrophy_only).")
    parser.add_argument("--mask-path", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "MNI152_T1_2mm_brain_mask.nii", help="Brain mask; only holes inside it are filled.")
    args = parser.parse_args()
    fill_control_dist(args.dist_dir, args.mask_path)


if __name__ == "__main__":
    main()
