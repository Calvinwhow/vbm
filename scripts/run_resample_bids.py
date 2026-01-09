#!/usr/bin/env python3
"""Batch resample NIfTI files to the default atlas grid."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import nibabel as nib
from nilearn.image import resample_to_img


DEFAULT_MASK = Path("/root/assets/MNI152_T1_2mm_brain_mask.nii")


def derive_output_path(inp_path: Path) -> Path:
    """Create an output filename with _resamp suffix, preserving .nii/.nii.gz."""
    stem = inp_path.name
    if stem.endswith(".nii.gz"):
        stem = stem[:-7]
        ext = ".nii.gz"
    elif stem.endswith(".nii"):
        stem = stem[:-4]
        ext = ".nii"
    else:
        ext = inp_path.suffix
        stem = stem[: -len(ext)] if ext else stem
    return inp_path.with_name(f"{stem}_resamp{ext}")


def iter_inputs(base: Path, patterns: Iterable[str]) -> Iterable[Path]:
    """Yield input files matching the provided glob patterns under base."""
    for pattern in patterns:
        yield from base.rglob(pattern)


def resample_file(inp_path: Path, ref_path: Path, interpolation: str, overwrite: bool) -> Path | None:
    """Resample one NIfTI to the reference grid."""
    out_path = derive_output_path(inp_path)
    if out_path.exists() and not overwrite:
        print(f"Skipping (exists): {out_path}")
        return None
    if "resamp" in str(inp_path):
        print(f"Skipping (exists): {out_path}")
        return None

    inp_img = nib.load(str(inp_path))
    ref_img = nib.load(str(ref_path))
    resampled = resample_to_img(inp_img, ref_img, interpolation=interpolation, force_resample=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(resampled, str(out_path))
    print(f"Resampled {inp_path} -> {out_path}")
    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resample NIfTI files to a target mask grid.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help="Root directory to search for input NIfTIs (e.g., /root/data).",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        default=[],
        help="Glob pattern(s) (relative) to match files under base-dir. Can be passed multiple times.",
    )
    parser.add_argument(
        "--ref-mask",
        type=Path,
        default=DEFAULT_MASK,
        help=f"Reference mask / grid to resample onto (default: {DEFAULT_MASK}).",
    )
    parser.add_argument(
        "--interpolation",
        choices=["continuous", "nearest"],
        default="nearest",
        help="Interpolation mode passed to nilearn.resample_to_img.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite outputs if they already exist.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.ref_mask.exists():
        raise SystemExit(f"Reference mask not found: {args.ref_mask}")
    if not args.base_dir.exists():
        raise SystemExit(f"Base directory not found: {args.base_dir}")

    patterns: List[str] = args.patterns or ["**/*.nii", "**/*.nii.gz"]
    matched = list(iter_inputs(args.base_dir, patterns))
    if not matched:
        raise SystemExit(f"No inputs matched patterns {patterns} under {args.base_dir}")

    for inp in matched:
        resample_file(inp, args.ref_mask, args.interpolation, args.overwrite)


if __name__ == "__main__":
    main()
