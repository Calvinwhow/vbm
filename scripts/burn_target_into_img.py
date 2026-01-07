#!/usr/bin/env python3
from __future__ import annotations
import argparse
import numpy as np
import nibabel as nib

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resample segmentation mask to reference resolution")
    p.add_argument("--i", "--input", required=True,
                   help="Input patient-space NIfTI (e.g. T1.nii.gz)")
    p.add_argument("--t", "--target", required=True,
                   help="Target NIfTI to burn into patient-space NIfTI (e.g. Target.nii.gz)")
    p.add_argument("--o", "--out", required=True,
                   help="Filename to save as (e.g. T1_burned.nii.gz")
    p.add_argument("--m", "--method", required=True,
                   help="Burn in method to use (e.g. max or sum")
    p.add_argument("--thresh", required=False,
                   help="Threshold for burning in (e.g. 2.0).")
    return p.parse_args()

def load_images(path: str) -> np.ndarray:
    img = nib.load(path)
    arr = img.get_fdata(dtype=np.float32) # Convert to numpy arrays
    return arr, img.affine, img.header

def get_mask(trg_arr, t):
    '''Create mask by some threshold value'''
    if t is None: 
        t = 0.0
    return trg_arr > float(t)

def burn_in(flo_arr, trg_arr, mask, method='sum'):
    '''
    method: mathematical operation to burn values in
        options: max | sum 
    '''
    if method=='max':
        flo_arr[mask] = np.nanmax(flo_arr)  # Set target values to max of patient-space image
    elif method=='sum':
        flo_arr[mask] = flo_arr[mask] + trg_arr[mask]
    else:
        raise ValueError("method must be 'max' or 'sum'")
    return flo_arr 

def main() -> None:
    """Main function to compute and save the z-scored image using provided arguments."""
    args = parse_args()
    flo_arr, flo_affine, flo_hdr = load_images(args.i)
    trg_arr, _, _ = load_images(args.t)
    mask = get_mask(trg_arr, args.thresh)
    brn_arr = burn_in(flo_arr, trg_arr, mask, args.m)
    brn_img = nib.Nifti1Image(brn_arr, affine=flo_affine, header=flo_hdr)
    nib.save(brn_img, args.o)

if __name__ == "__main__":
    main()
