import argparse
import os
import numpy as np
import nibabel as nib
from scipy.ndimage import map_coordinates


class ImageLoader:
    def __init__(self, path: str):
        self.path = path
        self.img = nib.load(path)
        self.data = self.img.get_fdata()
        self.affine = self.img.affine
        self.shape = self.data.shape[:3]

    def world_bounds(self):
        ijk = np.array([
            [0, 0, 0, 1],
            [self.shape[0]-1, self.shape[1]-1, self.shape[2]-1, 1]
        ]).T
        xyz = self.affine @ ijk
        return xyz[:3, :]


class WarpField:
    """
    Handles CAT12/SPM deformation fields.

    Guarantees:
    - self.field has shape (X, Y, Z, 3)
    - values are absolute world coordinates (mm)
    """
    def __init__(self, path: str):
        self.path = path
        self.img = nib.load(path)
        raw = self.img.get_fdata()

        # Normalize shape
        raw = np.squeeze(raw)

        if raw.ndim != 4 or raw.shape[-1] != 3:
            raise ValueError(
                f"Warp field must be (X,Y,Z,3). Got {raw.shape}"
            )

        self.field = raw
        self.affine = self.img.affine
        self.shape = raw.shape[:3]

    def get_world_coords(self):
        return (
            self.field[..., 0],
            self.field[..., 1],
            self.field[..., 2],
        )


class WarpApplier:
    """
    Applies a WarpField to an ImageLoader source image
    using pull-based resampling.
    """
    def __init__(self, source: ImageLoader, warp: WarpField):
        self.source = source
        self.warp = warp
        self.inv_source_affine = np.linalg.inv(source.affine)

    def world_to_source_voxels(self, xw, yw, zw):
        world = np.vstack([
            xw.ravel(),
            yw.ravel(),
            zw.ravel(),
            np.ones(xw.size)
        ])
        vox = self.inv_source_affine @ world
        return (
            vox[0].reshape(xw.shape),
            vox[1].reshape(xw.shape),
            vox[2].reshape(xw.shape),
        )

    def apply(
        self,
        out_path: str,
        out_affine: np.ndarray | None = None,
        interp: str = "linear",
        cval: float = 0.0,
    ):
        order = 0 if interp == "nearest" else 1

        xw, yw, zw = self.warp.get_world_coords()
        xi, yi, zi = self.world_to_source_voxels(xw, yw, zw)

        warped = map_coordinates(
            self.source.data,
            [xi, yi, zi],
            order=order,
            mode="constant",
            cval=cval,
        )

        if out_affine is None:
            out_affine = self.warp.affine

        nib.save(
            nib.Nifti1Image(warped.astype(np.float32), out_affine),
            out_path,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply a deformation field to an image."
    )
    parser.add_argument("--i", required=True, help="Input image to warp.")
    parser.add_argument("--o", required=True, help="Output warped image.")
    parser.add_argument("--field", required=True, help="Warp field (iy*.nii).")
    parser.add_argument(
        "--interp",
        choices=["linear", "nearest"],
        default="linear",
        help="Interpolation method.",
    )
    parser.add_argument(
        "--cval",
        type=float,
        default=0.0,
        help="Constant fill value for out-of-bounds.",
    )
    return parser

def run_pipeline(args: argparse.Namespace) -> None:
    """Orchestrates the classes and pipeline"""
    source = ImageLoader(args.i)
    warp = WarpField(args.field)
    applier = WarpApplier(source, warp)
    applier.apply(
        out_path=args.o,
        interp=args.interp,
        cval=args.cval,
    )
    

if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args)