#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------
# Script to process MRI images using EasyReg pipeline.
# 
# Usage:
#   /root/scripts/run_burn_atrophy_to_dcm.sh relative/path/to/target.nii
#
# The first argument selects the script to use. 
#   Should always be run_burn_atrophy_to_dcm.sh
# The second argument states where to find the atrophy file relative to the patient's directory. 
#   Pass the target atrophy file's relative path (from the mounted patient's directory) as the argument.
#   No preceding slashes. example: ses-01/unthresholded_tissue_segment_z_scores/sub-0002_cerebrospinal_fluid.nii
#
# Notes:
# This script expects a patient's directory to be mounted to /root/data (using the -v in docker-compose)
# This means it will only do a single patient's atrophy at a time. It ONLY OVERLAYS the positive values
# -----------------------------------------------------------------

## -- Set Variables ---------------------------------------------------
ROOT=${DATA_DIR:-/root/data}
REF_IMG="/root/assets/MNI152_T1_2mm_brain.nii"
REF_SEG="/root/assets/mni152_mricron_seg.nii.gz"

## -- Checks and Printous ---------------------------------------------
INPUT="${1:-}"
if [[ -z "$INPUT" ]]; then
  echo "Error: No target image (TRGT) specified."
  exit 1
fi

TRGT="${ROOT}/${INPUT}"
if [[ ! -f "$TRGT" ]]; then
  echo "Error: Target image file '$TRGT' does not exist."
  exit 1
fi

SUBJECT_SES_DIR="$(dirname "$(dirname "${TRGT}")")"
DERIV="${SUBJECT_SES_DIR}/derivatives"
mkdir -p "${DERIV}"

THREADS=${THREADS:- -1}
echo "Reference:     $REF_IMG"
echo "Segmentation:  $REF_SEG"
echo "Threads:       $THREADS"
echo "Target:        $TRGT"
echo "Subject/session: ${SUBJECT_SES_DIR#${ROOT}/}"
echo "Burning target into native images in: $DERIV"

## -- Main Code -------------------------------------------------------
shopt -s nullglob

flos=("${SUBJECT_SES_DIR}/anat/"*T1*.nii*)
# flos=("${SUBJECT_SES_DIR}/anat/T1.nii"*) commented out to avoid matching deformation fields (iy_T1, y_T1), 
# probability maps (mwp*T1, rp*T1), and other CAT12 outputs
if [[ ${#flos[@]} -eq 0 ]]; then
  echo "No T1 images found under ${SUBJECT_SES_DIR}/anat for burning."
  exit 1
fi

for flo in "${flos[@]}"; do
  trgt_base=$(basename "${TRGT}")
  trgt_base=${trgt_base%.nii.gz}
  trgt_base=${trgt_base%.nii}       # trgt_base is the atrophy file to be warped onto the floating image
  flo_base=$(basename "${flo}")     # This is the image in patient space. 
  flo_base=${flo_base%.nii}; flo_base=${flo_base%.gz}

  echo "Float:  ${flo_base}"
  echo "Target: ${trgt_base}"

  # 1) registration – writes forward field (fwd)
  python /root/easyreg/mri_easyreg.py \
    --flo       "${flo}" \
    --ref       "${REF_IMG}" \
    --ref_seg   "${REF_SEG}" \
    --flo_seg   "${DERIV}/${flo_base}_seg.nii.gz" \
    --fwd_field "${DERIV}/${flo_base}_fwd.nii.gz" \
    --bak_field "${DERIV}/${flo_base}_bak.nii.gz" \
    --threads   "${THREADS}"

  # 1.5) clean up the atrophy
  python /root/scripts/clean_atrophy.py \
    --i "${TRGT}" \
    --m "/root/assets/MNI152_T1_2mm_brain_mask.nii" \
    --o "${DERIV}/${trgt_base}_cleaned.nii.gz"
  
  ## 2) warp target to native space
  python /root/easyreg/mri_easywarp.py \
    --i       "${DERIV}/${trgt_base}_cleaned.nii.gz" \
    --o       "${DERIV}/${trgt_base}_native.nii.gz" \
    --field   "${DERIV}/${flo_base}_bak.nii.gz" \
    --threads "${THREADS}"

  ## 3) burn target into the native image
  python /root/scripts/burn_target_into_img.py \
    --i       "${flo}" \
    --t       "${DERIV}/${trgt_base}_native.nii.gz" \
    --o       "${DERIV}/${flo_base}_burned_in_${trgt_base}.nii.gz" \
    --m       "sum" \
    --thresh  "2.0"   # any values over 2 are considered atrophic

  ## 4) Convert the burned image to DCM
  python /root/scripts/write_burned_dcm.py \
    --i       "${DERIV}/${flo_base}_burned_in_${trgt_base}.nii.gz"  \
    --o       "${DERIV}/${flo_base}_burned_in_${trgt_base}_dicom" \
    --b       "${flo}" 
    
done

## final message
echo "All subjects processed and excess files removed."
