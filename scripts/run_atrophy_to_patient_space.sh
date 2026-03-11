#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=${DATA_DIR:-/root/data}
SESSION=${SESSION:-ses-01}
THREADS=${THREADS:-1}
ATROPHY_PATTERNS=(
  "*_composite.nii*"
  "*_composite_s*.nii*"
)

echo "Scanning ${DATA_DIR} for ${SESSION} sessions..."

# Loop over session directories
find "${DATA_DIR}" -type d -path "*/${SESSION}" | while read -r SES_DIR; do
  echo "Processing ${SES_DIR}"
  ATROPHY_DIR="${SES_DIR}/unthresholded_tissue_segment_z_scores"
  MRI_DIR="${SES_DIR}/mri"
  OUT_DIR="${SES_DIR}/unthresholded_tissue_segment_z_scores_native"
  mkdir -p "${OUT_DIR}"

  # 1) Check for mandatory files
  atrophy_files=()
  for pattern in "${ATROPHY_PATTERNS[@]}"; do
    while IFS= read -r f; do
      [[ -n "${f}" ]] && atrophy_files+=("${f}")
    done < <(find "${ATROPHY_DIR}" -type f -name "${pattern}" 2>/dev/null || true)
  done
  iwarp_file=$(find "${MRI_DIR}" -type f -name "iy*.nii*" 2>/dev/null | head -n 1 || true)
  if [[ "${#atrophy_files[@]}" -eq 0 || -z "${iwarp_file}" ]]; then
    echo "Skipping ${SES_DIR} (missing atrophy or inverse warp)"
    continue
  fi

  for atrophy_file in "${atrophy_files[@]}"; do
    ATROPHY_BASE="$(basename "${atrophy_file}")"
    ATROPHY_BASE="${ATROPHY_BASE%.nii.gz}"
    ATROPHY_BASE="${ATROPHY_BASE%.nii}"

    # 2) Clean up the atrophy
    echo "  Masking atrophy file: ${atrophy_file##*/}"
    if ! python /root/scripts/clean_atrophy.py \
      --i "${atrophy_file}" \
      --m "/root/assets/MNI152_T1_2mm_brain_mask.nii" \
      --o "${OUT_DIR}/${ATROPHY_BASE}_cleaned.nii.gz" \
      --l "false"; then
      echo "ERROR: cleaning atrophy for ${ATROPHY_BASE}; skipping to next."
      continue
    fi

    # 3) Run python warp
    echo "  Warping atrophy: ${ATROPHY_BASE}"
    echo "  with ${iwarp_file##*/}"
    if ! python /root/scripts/apply_warp_python.py \
      --i       "${OUT_DIR}/${ATROPHY_BASE}_cleaned.nii.gz" \
      --o       "${OUT_DIR}/${ATROPHY_BASE}_cleaned_native.nii.gz" \
      --field   "${iwarp_file}"; then
      echo "ERROR: apply_warp_python.py for ${ATROPHY_BASE}; skipping to next."
      continue
    fi

    # 4) Clean up
    rm "${OUT_DIR}/${ATROPHY_BASE}_cleaned.nii.gz"
  done
done
echo "All atrophy warps completed"
