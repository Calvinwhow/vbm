#!/usr/bin/env python3
from __future__ import annotations
import argparse
import numpy as np
import nibabel as nib

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Atrophy cleaning reference")
    p.add_argument("--i", "--input", required=True,
                   help="Input template-space NIfTI (e.g. Atrophy.nii.gz)")
    p.add_argument("--m", "--mask", required=True,
                   help="Mask for template-spcce NIfTI (e.g. MNI152.nii.gz)")
    p.add_argument("--o", "--out", required=True,
                   help="Filename to save as (e.g. Atrophy_cleaned.nii.gz")
    return p.parse_args()

def load_images(path: str) -> np.ndarray:
    img = nib.load(path)
    arr = img.get_fdata(dtype=np.float32) # Convert to numpy arrays
    return arr, img.affine, img.header

def get_mask(trg_arr):
    '''Create mask by some threshold value'''
    return trg_arr > 0

def clean_values(flo_arr, mask, method='sum'):
    '''Cleans the values within the nifti'''
    flo_arr[flo_arr < 2] = 0 # sets range minimum to 2 
    flo_arr[flo_arr > 5] = 5 # sets range maximum to 5
    flo_arr[~mask] = 0 # sets values outside the mask to 0
    return flo_arr 

def main() -> None:
    """Main function to clean up atrophy for presentation in DICOMS."""
    args = parse_args()
    flo_arr, flo_affine, flo_hdr = load_images(args.i)
    trg_arr, _, _ = load_images(args.m)
    mask_indices = get_mask(trg_arr)
    clean_arr = clean_values(flo_arr, mask_indices, args.m)
    clean_img = nib.Nifti1Image(clean_arr, affine=flo_affine, header=flo_hdr)
    nib.save(clean_img, args.o)

if __name__ == "__main__":
    main()
