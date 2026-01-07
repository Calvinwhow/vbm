#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import numpy as np
import nibabel as nib
from pathlib import Path

EASYREG_DIR = Path(__file__).resolve().parent.parent
MASK_PATH   = os.path.join(EASYREG_DIR, "assets", "MNI152_T1_2mm_brain_mask.nii")
_mask_bool = nib.load(MASK_PATH).get_fdata() > 0           # (voxels,) or (x,y,z)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resample segmentation mask to reference resolution")
    p.add_argument("--i", "--input", required=True,
                   help="Input segmentation NIfTI (e.g. *_swmp1_ref.nii.gz)")
    p.add_argument("--t", "--tag", required=True,
                   help="Tag of the segment (e.g. swmp1")
    p.add_argument("--o", "--out", required=True,
                   help="Filename to save as (e.g. swmp1-zscore.nii.gz")
    return p.parse_args()

def load_stats(tag: str) -> float:
    """Load the mean value for the specified tag."""
    if tag == 'smwp1':
        mean = os.path.join(EASYREG_DIR, 'assets', 'cerebrospinal_fluid_mean.nii')
        std = os.path.join(EASYREG_DIR, 'assets', 'cerebrospinal_fluid_std.nii')
    elif tag == 'smwp2':
        mean = os.path.join(EASYREG_DIR, 'assets', 'grey_matter_mean.nii')
        std = os.path.join(EASYREG_DIR, 'assets', 'grey_matter_std.nii')
    elif tag == 'smwp3':
        mean = os.path.join(EASYREG_DIR, 'assets', 'white_matter_mean.nii')
        std = os.path.join(EASYREG_DIR, 'assets', 'white_matter_std.nii')
    else:
        raise ValueError(f"Unknown tag: {tag}")
    
    return nib.load(mean), nib.load(std)

def z_score(img: nib.Nifti1Image, mean: nib.Nifti1Image, std:  nib.Nifti1Image, e: float = 1e-6) -> nib.Nifti1Image:
    """Z-score `img` using pre-computed `mean` and `std`, then zero everything outside the MNI brain mask."""
    num = img.get_fdata(dtype=np.float32) - mean.get_fdata(dtype=np.float32)
    den = std.get_fdata(dtype=np.float32)
    z = num / (den + e)
    z *= _mask_bool.astype(z.dtype)
    return nib.Nifti1Image(z, img.affine, img.header)

def main() -> None:
    """Main function to compute and save the z-scored image using provided arguments."""
    args = parse_args()
    img = nib.load(args.i)
    mean, std = load_stats(args.t)
    z_img = z_score(img, mean, std)
    nib.save(z_img, args.o)

if __name__ == "__main__":
    main()