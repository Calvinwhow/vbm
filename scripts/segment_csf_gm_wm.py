import os
import shutil
import argparse
from pathlib import Path
import numpy as np
from nilearn.maskers import NiftiMasker
from nilearn.image import resample_to_img, math_img
from easyreg import segment_image_mni152
import nibabel as nib
from nibabel.processing import smooth_image
import ants

DIR = Path(__file__).resolve().parent.parent

def orchestrate_csf_mapping(
    raw_img_path: str,
    ref_template_path: str = None,
    ref_template_seg_path: str = None,
    output_prefix: str = None,
    threads: int = 11,
) -> dict:
    """
    Registers a T1 image to template space, segments into GM/WM/CSF, smooths the maps,
    and computes a deterministic atlas.

    Parameters
    ----------
    raw_img_path : str
        Path to the input T1 image.
    ref_template_path : str, optional
        Reference template image path.
    ref_template_seg_path : str, optional
        Reference template segmentation path.
    output_prefix : str, optional
        Output directory or file prefix.
    threads : int, default 11
        Number of threads to use.

    Returns
    -------
    dict
        Output file paths.
    """
    # Resolve template paths
    if ref_template_path is None:
        ref_template_path = str(DIR / "assets" / "MNI152_T1_2mm_brain.nii")
    if ref_template_seg_path is None:
        ref_template_seg_path == str(DIR / "assets" / "MNI152_T1_2mm_brain.nii.gz")
    mask = str(DIR / "assets" / "MNI152_T1_2mm_brain_mask.nii")

    print("Using reference template: ", ref_template_path)
    print("Using reference template segmentation: ", ref_template_seg_path)      

    # Determine output base
    raw = Path(raw_img_path)
    name_stem = raw.name
    if name_stem.endswith(".nii.gz"):
        name_stem = name_stem[: -len(".nii.gz")]
    elif name_stem.endswith(".nii"):
        name_stem = name_stem[: -len(".nii")]

    if output_prefix:
        outp = Path(output_prefix)
        if str(output_prefix).endswith(os.sep) or (outp.exists() and outp.is_dir()):
            out_dir, base_filename_prefix = outp, name_stem
        else:
            out_dir, base_filename_prefix = outp.parent, outp.name
    else:
        out_dir, base_filename_prefix = raw.parent, name_stem

    out_dir.mkdir(parents=True, exist_ok=True)
    base_path = str(out_dir / base_filename_prefix)

    # Define native segmentation path first
    native_seg_path = f"{base_path}_seg.nii.gz"
    post_seg_path = f"{base_path}_seg_mni152_posteriors.nii.gz"

    outputs = {
        "native_seg": native_seg_path,
        "registered": f"{base_path}_registered_to_ref.nii.gz",
        "field": f"{base_path}_fwd_field.nii.gz",
        "post": post_seg_path,
        "gm": f"{base_path}_smwp1_ref.nii.gz",
        "wm": f"{base_path}_smwp2_ref.nii.gz",
        "csf": f"{base_path}_smwp3_ref.nii.gz",
        "atlas": f"{base_path}_deterministic_atlas_ref.nii",
    }

    print(f"--- Orchestrating CSF Mapping ---")
    print(f"Input T1 Image: {raw_img_path}")
    print(f"Output base for files: {base_path}")
    print(f"Expected warped posteriors at: {outputs['post']}")

    segment_image_mni152(
        flo=str(raw),
        ref=ref_template_path,
        ref_seg=ref_template_seg_path,
        flo_seg=outputs["native_seg"],
        flo_reg=outputs["registered"],
        fwd_field=outputs["field"],
        threads=threads,
        post=True,
        autocrop=True
        )

    post_path = outputs["post"]
    if not Path(post_path).exists():
        raise FileNotFoundError(f"Missing expected warped posteriors file: {post_path}")
    
    warp_path   = outputs['field']                      # fwd warp .nii.gz from SyN
    jac_img_out = jacobian_determinant_ants(warp_path, ref_template_path, f"{base_path}_jacobian_determinant.nii.gz")
    # jacobian_determinant_from_warp(warp_path, f"{base_path}_jacobian_determinant.nii.gz")

    # Extract, smooth, and save tissue maps
    for tissue in ["gm", "wm", "csf"]:
        print(f"Processing {tissue.upper()} for CSF mapping...")
        
        basename = outputs[tissue]
        wpname = basename.replace('smwp', 'wp')
        mwpname = basename.replace('smwp', 'mwp')
        smwpname = basename.replace('smwp', 'smwp')

        # Extract tissue labels from posteriors and save the warped probability mpa
        img = extract_tissue_labels(post_path, tissue, mask)
        img.to_filename(wpname)
    
        # Modulate the tissue image using jacobian determinant
        jacobian_resampled = resample_to_img(nib.load(jac_img_out), img)
        modulated_img = math_img('img1 * img2', img1=img, img2=jacobian_resampled)
        modulated_img.to_filename(mwpname)

        # Smooth the modulated image
        smoothed_modulated_img = smooth_image(modulated_img, fwhm=(2, 2, 2))
        smoothed_modulated_img.to_filename(smwpname)

    print("Computing deterministic atlas for CSF mapping...")
    dummy_input = f"{base_path}_dummy_for_atlas.nii"
    compute_deterministic_atlas(dummy_input, outputs["gm"], outputs["wm"], outputs["csf"], mask)
    generated_atlas = dummy_input.replace(".nii", "_deterministic_atlas.nii")
    
    if Path(generated_atlas).exists():
        shutil.move(generated_atlas, outputs["atlas"])
        print(f"Deterministic atlas saved to: {outputs['atlas']}")
    else:
        print(f"Warning: {generated_atlas} not found; skipping move")

    print("--- CSF mapping complete ---")
    return outputs

def _extract_tissue_labels(path: str, label_indices: list, mask: str):
    """Helper to load SynthSeg posteriors and return combined probability map for CSF mapping."""
    if not Path(mask).exists():
        raise FileNotFoundError(f"Mask not found: {mask}")
    masker = NiftiMasker(mask_img=mask, standardize=False, memory_level=1, verbose=0)
    data = masker.fit_transform(path)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    valid = [i for i in label_indices if i < data.shape[0]]
    if not valid:
        return masker.inverse_transform(np.zeros(data.shape[1]))
    if len(valid) < len(label_indices):
        print(f"Warning: some indices out of bounds. Using {valid}")
    selected = data[valid, :]
    prob_map = np.nan_to_num(selected).max(axis=0)
    return masker.inverse_transform(prob_map)


def extract_tissue_labels(path: str, tissue: str, mask: str):
    """Load SynthSeg posteriors and return a CSF probability map."""
    if tissue.lower() == "csf":
        return _extract_tissue_labels(path, [3, 4, 11, 12, 16, 21, 22], mask)
    elif tissue.lower() == "gm":
        return _extract_tissue_labels(path, [2, 6, 7, 8, 9, 10, 14, 15, 17, 20, 24, 25, 26, 27, 28, 29, 30, 31], mask)
    elif tissue.lower() == "wm":
        return _extract_tissue_labels(path, [1, 5, 13, 18, 19, 23, 32], mask)
    else:
        raise ValueError(f"Unknown tissue type: {tissue}. Use 'csf', 'gm', or 'wm'.")


def compute_deterministic_atlas(dummy_raw_img_path: str, gm_img_path: str, wm_img_path: str, csf_img_path: str, mask: str):
    """
    Label each voxel by the tissue class with highest probability (1=GM, 2=WM, 3=CSF) for CSF mapping.
    `dummy_raw_img_path` forms the output filename.
    """
    masker = NiftiMasker(mask_img=mask, standardize=False, memory_level=1, verbose=0)
    gm = np.squeeze(masker.fit_transform(gm_img_path))
    wm = np.squeeze(masker.fit_transform(wm_img_path))
    csf =np.squeeze(masker.fit_transform(csf_img_path))
    gm = gm.reshape(-1, 1) if gm.ndim == 1 else gm
    wm = wm.reshape(-1, 1) if wm.ndim == 1 else wm
    csf = csf.reshape(-1, 1) if csf.ndim == 1 else csf
    atlas = np.argmax(np.concatenate([gm, wm, csf], axis=1), axis=1) + 1
    atlas_2d = atlas[np.newaxis, :]
    out = dummy_raw_img_path.replace(".nii", "_deterministic_atlas.nii")
    masker.inverse_transform(atlas_2d).to_filename(out)
    print(f"Atlas saved to: {out}")

def jacobian_determinant_from_warp(warp_path: str, out_path: str) -> None:
    """Approximate the Jacobian determinant of forward-warp field."""
    img      = nib.load(warp_path)
    warp     = img.get_fdata(dtype=np.float32)          # shape (X,Y,Z,3)
    affine   = img.affine
    Avox     = img.affine[:3, :3]
    dxyz     = img.header.get_zooms()[:3]
    
    dx, dy, dz = img.header.get_zooms()[:3]             # voxel spacing (mm)
    ux, uy, uz = np.moveaxis(warp, -1, 0)               # three (X,Y,Z) arrays

    g  = [np.gradient(c, *([1]*3), edge_order=2) for c in (ux, uy, uz)]
    g = np.empty(warp.shape[:-1] + (3, 3), dtype=np.float32)    #  Shape: (X,Y,Z,3,3)
    G = np.empty(warp.shape[:-1] + (3,3), dtype=np.float64)
    G[...,0,0], G[...,0,1], G[...,0,2] = g[0]          # dux/d(i,j,k)
    G[...,1,0], G[...,1,1], G[...,1,2] = g[1]
    G[...,2,0], G[...,2,1], G[...,2,2] = g[2]

    AinvT = np.linalg.inv(Avox).T                      # fast reuse
    for i in range(3):
        G[...,i,:] = G[...,i,:] @ AinvT                # rotate to world
    G /= np.array(dxyz)                                # scale

    J = np.eye(3) + G                                  # I + ∂u/∂x
    detJ = np.linalg.det(J)

    nib.save(nib.Nifti1Image(detJ.astype(np.float32), img.affine), out_path)
    return out_path

def jacobian_determinant_ants(warp_path: str, ref_path: str, out_path: str) -> None:
    warp = ants.image_read(str(warp_path))
    domain = ants.image_read(str(ref_path))
    log_jac = ants.create_jacobian_determinant_image(domain, warp, do_log=True, geom=False)
    ants.image_write(log_jac, str(out_path))
    return out_path

def main():
    """CLI for segmentation and CSF mapping."""
    parser = argparse.ArgumentParser(
        description="Segment T1, generate tissue maps, and CSF mapping."
    )
    parser.add_argument(
        "--i", help="Path to input T1 image (NIFTI)."
        )
    parser.add_argument(
        "--ref", help="Custom reference template path.", default=None
    )
    parser.add_argument(
        "--ref_seg", help="Custom template segmentation path.", default=None
    )
    parser.add_argument(
        "--output_prefix", help="Output prefix or directory.", default=None
    )
    parser.add_argument(
        "--threads", type=int, help="Threads for processing.", default=11
    )
    args = parser.parse_args()
    orchestrate_csf_mapping(
        raw_img_path=args.i,
        ref_template_path=args.ref,
        ref_template_seg_path=args.ref_seg,
        output_prefix=args.output_prefix,
        threads=args.threads,
    )


if __name__ == "__main__":
    main()