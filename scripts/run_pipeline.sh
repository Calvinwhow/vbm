#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting neuroimaging pipeline ==="

THREADS=${THREADS:-1}
ORGANIZE_SEGMENTATION=${ORGANIZE_SEGMENTATION:-true}
RUN_STEP_2_2=false

export THREADS

echo "DATA_DIR=$DATA_DIR"
echo "SCRIPT_DIR=$SCRIPT_DIR"
echo "SESSION=$SESSION"
echo "THREADS=$THREADS"

echo "=== Validating input T1 images ==="
T1_FILES=$(find "${DATA_DIR}" -type f -path "*/${SESSION}/anat/*T1*.nii*" | sort || true)
if [[ -z "${T1_FILES}" ]]; then
  echo "No T1-weighted NIfTI files found under ${DATA_DIR}/**/${SESSION}/anat. Ensure Step 0 placed files (e.g., ${DATA_DIR}/subject-01/${SESSION}/anat/*T1*.nii*)."
  exit 1
fi
echo "${T1_FILES}"

echo "=== Step 1: CAT12 segmentation ==="
bash "${SCRIPT_DIR}/run_segmentation_bids.sh"

echo "=== Step 1.1: Resampling CAT12 Segments ==="
python "${SCRIPT_DIR}/run_resample_bids.py" \
    --base-dir               "${DATA_DIR}" \
    --pattern                 "*mri/mwp*"

echo "=== Step 2.1: Atrophy Derivation ==="
python "${SCRIPT_DIR}/run_z_scoring.py" \
    --experiments-root        "${DATA_DIR}" \
    --experiments-gm-pattern  "*/*/mri/mwp1*resamp*" \
    --experiments-wm-pattern  "*/*/mri/mwp2*resamp*" \
    --experiments-csf-pattern "*/*/mri/mwp3*resamp*" \
    --control-stats-dir       "/root/assets/ctrl_dist" \
    --mask-path               "/root/assets/MNI152_T1_2mm_brain_mask.nii" \
    --session                 "${SESSION}"

echo "=== Step 2.2: Atrophy to Patient Space ==="
if [[ "${RUN_STEP_2_2}" == "true" ]]; then
  bash "${SCRIPT_DIR}/run_burn_atrophy_to_dcm_batch.sh"
else
  echo "Skipping Step 2.2 (RUN_STEP_2_2=false)"
fi

echo "=== Step 3.1: Regional Atrophy Measurements ==="
python "${SCRIPT_DIR}/measure_regional_atrophy.py" \
    --base-dir "${DATA_DIR}" \
    --session  "${SESSION}" \
    --roi-dir  "/root/assets/rois/anatomic_coarse" \
    --mask-path "/root/assets/MNI152_T1_2mm_brain_mask.nii" \
    --fname "regional_atrophy_coarse"
python "${SCRIPT_DIR}/measure_regional_atrophy.py" \
    --base-dir "${DATA_DIR}" \
    --session  "${SESSION}" \
    --roi-dir  "/root/assets/rois/aal_fine" \
    --mask-path "/root/assets/MNI152_T1_2mm_brain_mask.nii"\
    --fname "regional_atrophy_fine"
python "${SCRIPT_DIR}/measure_regional_atrophy.py" \
    --base-dir "${DATA_DIR}" \
    --session  "${SESSION}" \
    --roi-dir  "/root/assets/rois/jhu_81" \
    --mask-path "/root/assets/MNI152_T1_2mm_brain_mask.nii"\
    --fname "tract_atrophy"
python "${SCRIPT_DIR}/measure_regional_atrophy.py" \
    --base-dir "${DATA_DIR}" \
    --session  "${SESSION}" \
    --roi-dir  "/root/assets/rois/yeo_7" \
    --mask-path "/root/assets/MNI152_T1_2mm_brain_mask.nii"\
    --fname "network_atrophy"

echo "=== Step 3.2: Disease Classification ==="
python "${SCRIPT_DIR}/classify_disease.py" \
    --base-dir "${DATA_DIR}" \
    --session  "${SESSION}" \
    --archetype-dir "/root/assets/archetypes" \
    --mask-path "/root/assets/MNI152_T1_2mm_brain_mask.nii"

echo "=== Pipeline completed successfully ==="
