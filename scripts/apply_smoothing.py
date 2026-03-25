#!/usr/bin/env python3
import argparse
from pathlib import Path
import os
from nilearn.image import smooth_img


DEFAULT_BASE = Path("/root/data")
DEFAULT_SES = os.getenv("SESSION", "ses-01")
DEFAULT_GLOB = os.getenv("SEGMENTS", "*_composite.nii*")

def _split_nii(path: Path):
    name = path.name
    if name.endswith(".nii.gz"):
        return name[:-7], ".nii.gz"
    if name.endswith(".nii"):
        return name[:-4], ".nii"
    return path.stem, path.suffix


def main() -> int:
    parser = argparse.ArgumentParser(description="Smooth composite atrophy maps.")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--session", default=DEFAULT_SES)
    parser.add_argument("--fwhm", type=float, required=True)
    args = parser.parse_args()

    analysis_dirs = [
        "unthresholded_tissue_segment_z_scores",
        "thresholded_tissue_segment_z_scores",
        "unthresholded_tissue_segment_z_scores_native",
        "thresholded_tissue_segment_z_scores_native",
    ]
    suffix = f"_s{args.fwhm:g}"
    targets = []
    for analysis in analysis_dirs:
        pattern = f"*/{args.session}/{analysis}/{DEFAULT_GLOB}"
        targets.extend(args.base_dir.glob(pattern))

    if not targets:
        print(f"No composite maps found under {args.base_dir} for {args.session}.")
        return 0

    for src in targets:
        if src.name.startswith("._"):
            continue
        stem, ext = _split_nii(src)
        if stem.endswith(suffix):
            print(f"Skipping already-smoothed: {src}")
            continue
        out_path = src.with_name(f"{stem}{suffix}{ext}")
        smooth_img(str(src), fwhm=args.fwhm).to_filename(str(out_path))
        print(f"Smoothed: {src.name} -> {out_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
