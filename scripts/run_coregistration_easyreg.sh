#!/usr/bin/env bash
# Register every *.nii / *.nii.gz in /root/data (except derivatives) to ref.[nii|nii.gz]
# then warp each image exactly into the reference grid.

# Args
# No args required. 

set -euo pipefail

ROOT=/root/data                          # single root: raw data + /derivatives live here
mkdir -p "${ROOT}/derivatives"

REF_IMG="/root/assets/MNI152_T1_2mm_brain.nii"
REF_SEG="/root/easyreg/assets/MNI152_T1_2mm_brain_seg.nii.gz"
# -------------------------------------------------------------------------

THREADS=${THREADS:--1}

echo "Reference image:  ${REF_IMG}"
echo "Segmentation:     ${REF_SEG}"
echo "Threads:          ${THREADS}"
echo

shopt -s nullglob
for flo in "${ROOT}"/*.nii*; do
  [[ $flo == "${ROOT}/derivatives/"* ]] && continue   # skip derivative files
  [[ ! -f $flo ]] && continue                         # no match

  # strip one (or two) extensions: .nii OR .nii.gz
  base=$(basename "${flo}")
  base=${base%.nii}
  base=${base%.gz}

  echo "=========  ${base}  ========="

  easyreg-mri \
    --flo       "${flo}" \
    --ref       "${REF_IMG}" \
    --ref_seg   "${REF_SEG}" \
    --flo_seg   "${ROOT}/derivatives/${base}_seg.nii.gz" \
    --fwd_field "${ROOT}/derivatives/${base}_fwd.nii.gz" \
    --bak_field "${ROOT}/derivatives/${base}_bak.nii.gz" \
    --threads   "${THREADS}"
    
  easywarp-mri \
    --i       "${flo}" \
    --o       "${ROOT}/derivatives/${base}_warped.nii.gz" \
    --field   "${ROOT}/derivatives/${base}_fwd.nii.gz" \
    --threads "$THREADS" \
    --nearest
done
