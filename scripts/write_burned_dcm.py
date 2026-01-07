#!/usr/bin/env python3
from __future__ import annotations
import argparse
from nii_to_dcm import NiftiToDicomV2

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resample segmentation mask to reference resolution")
    p.add_argument("--i", "--input", required=True,
                   help="Burned in nifti (e.g. T1_burned.nii.gz)")
    p.add_argument("--b", "--base", required=False,
                   help="Original nifti before burning (e.g. T1.nii.gz)")
    p.add_argument("--d", "--dicom", required=False,
                   help="Original dicom to use for metadata fields (e.g. T1.dcm)")
    p.add_argument("--o", "--out", required=True,
                   help="Directory to save to.")
    return p.parse_args()

def handle_args(args) -> argparse.Namespace:
    if (not args.d) or (args.d.lower() == "none"): # catches None and "" or "none"
        args.d = None
    return args

def main() -> None:
    """Main function to compute and save the z-scored image using provided arguments."""
    args = parse_args()
    args = handle_args(args)
    
    # NiftiToDicom(nii_path=args.i, output_dir=args.o).convert()
    NiftiToDicomV2(nii_path=args.i, output_dir=args.o, orig_img_path=args.b, example_dcm_path=args.d).convert()

if __name__ == "__main__":
    main()
