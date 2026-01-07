#!/usr/bin/env python3
"""Resample CSF/GM/WM segmentation masks to the voxel grid of a reference NIfTI.

This utility is intended for step 4 of the EasyReg pipeline.  It takes a
segmentation image (e.g. *_swmp1_ref.nii.gz) and rewrites it, resampled to
match the voxel spacing, shape, and affine of the provided reference image.
Nearest-neighbour interpolation is used so that label indices remain intact.

The output filename is automatically derived:
  - “swmp” → “smwp”   (to match the downstream whitelist)
Examples
--------
$ python resample_csf_gm_wm.py \
    --i  subject_swmp1_ref.nii.gz \
    --ref ref.nii.gz

The result will be written in the same directory as:
    subject_smwp1.nii.gz
"""
from __future__ import annotations
import argparse
import os
import nibabel as nib
from nilearn.image import resample_to_img


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resample segmentation mask to reference resolution")
    p.add_argument("--i", "--input", required=True, dest="inp",
                   help="Input segmentation NIfTI (e.g. *_swmp1_ref.nii.gz)")
    p.add_argument("--ref", required=True,
                   help="Reference NIfTI defining target grid")
    return p.parse_args()


def derive_output_path(inp_path: str) -> str:
    '''Appends suffix to filename'''
    dirname, fname = os.path.split(inp_path)
    if fname.endswith(".nii.gz"):
        stem, ext = fname[:-7], ".nii.gz"
    elif fname.endswith(".nii"):
        stem, ext = fname[:-4], ".nii"
    else:
        stem, ext = os.path.splitext(fname)
    stem = stem + "_resamp"
    return os.path.join(dirname, f"{stem}{ext}")


def main() -> None:
    args = parse_args()
    inp_img = nib.load(args.inp)
    ref_img = nib.load(args.ref)

    # Nearest-neighbour preserves integer tissue labels
    resampled = resample_to_img(inp_img, ref_img, interpolation="nearest")
    out_path = derive_output_path(args.inp)
    nib.save(resampled, out_path)
    print(f"\u2713 Resampled -> {out_path}")


if __name__ == "__main__":
    main()
