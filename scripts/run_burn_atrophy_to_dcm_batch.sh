#!/usr/bin/env bash
set -euo pipefail

# Discover composite atrophy maps and burn each into native space.

DATA_DIR=${DATA_DIR:-/root/data}
SESSION=${SESSION:-ses-01}
SCRIPT_DIR=${SCRIPT_DIR:-/root/scripts}

echo "Searching for composite atrophy maps under ${DATA_DIR} for ${SESSION}..."
atrophy_files=$(find "${DATA_DIR}" -type f -path "*/${SESSION}/thresholded_tissue_segment_z_scores/*_composite.nii*" | sort || true)

if [[ -z "${atrophy_files}" ]]; then
  echo "No composite atrophy maps found to burn into native space."
  exit 1
fi

while IFS= read -r atrophy_path; do
  rel_path=${atrophy_path#"${DATA_DIR}/"}
  echo "Burning atrophy map: ${rel_path}"
  bash "${SCRIPT_DIR}/run_burn_atrophy_to_dcm.sh" "${rel_path}"
done <<< "${atrophy_files}"
