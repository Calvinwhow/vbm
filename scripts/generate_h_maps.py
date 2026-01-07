#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import numpy as np
import nibabel as nib
from glob import glob
from pathlib import Path

EASYREG_DIR = Path(__file__).resolve().parent.parent
MASK_PATH   = os.path.join(EASYREG_DIR, "assets", "MNI152_T1_2mm_brain_mask.nii")
_mask_bool = nib.load(MASK_PATH).get_fdata() > 0           # (voxels,) or (x,y,z)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resample segmentation mask to reference resolution")
    p.add_argument("--i", "--input", required=True,
                   help="Input segmentation NIfTI (e.g. *_swmp1_ref.nii.gz)")
    p.add_argument("--o", "--out", required=True,
                   help="Filename to save as (e.g. swmp1-zscore.nii.gz")
    return p.parse_args()

def load_stats() -> float:
    """Load the mean value for the stats."""
    mean = os.path.join(EASYREG_DIR, 'assets', 'l2_norm_mean.nii')
    std = os.path.join(EASYREG_DIR, 'assets', 'l2_norm_std.nii')
    return nib.load(mean), nib.load(std)

def load_images(path: str) -> np.ndarray:
    img_files = sorted(glob(path))
    imgs = [nib.load(f) for f in img_files]
    imgs = [img.get_fdata(dtype=np.float32) for img in imgs]  # Convert to numpy arrays
    tensor = np.stack(imgs, axis=0)  # shape: (N, X, Y, Z)
    return tensor

def norm_images(img_arr) -> np.ndarray:
    '''Get L2 norm of the images along the first axis (segments axis).'''
    return np.linalg.norm(img_arr, axis=0, keepdims=False)

def z_score(img, mean, std, e=1e-6) -> np.ndarray:
    '''Compute the z-score of the array.'''
    num = img - mean
    den = std + e
    z   = num / den
    z  *= _mask_bool.astype(z.dtype)
    return z

def main() -> None:
    """Main function to compute and save the z-scored image using provided arguments."""
    args = parse_args()
    arr = load_images(args.i)
    norm = norm_images(arr)
    mean, std = load_stats()
    z_arr = z_score(norm, mean.get_fdata(), std.get_fdata())
    z_img = nib.Nifti1Image(z_arr, affine=mean.affine, header=mean.header)
    nib.save(z_img, args.o)

if __name__ == "__main__":
    main()
