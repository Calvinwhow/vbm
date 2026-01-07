#!/usr/bin/env bash
# Documentation:
# This code allows users to specify a target and a field within THIS FILE.
# 
# Instructions:
# Provide JUST the filenames below. 

# ---USER INPUT REQUIRED---
TARGET_NAME="sub-TeKe_cerebrospinal_fluid_generated_nifti_masked.nii.gz"
FIELD_NAME="teke_bak.nii.gz"
# ---END USER INPUT--------

# Paths
set -euo pipefail
ROOT=/root/data

# Extract base names without extensions
TARGET_BASE=$(basename "${TARGET_NAME}" | sed 's/\.\(nii\|gz\)//g')
FIELD_BASE=$(basename "${FIELD_NAME}" | sed 's/\.\(nii\|gz\)//g')

# File Inputs and File Outputs
TARGET=$ROOT/${TARGET_NAME}
FIELD=$ROOT/${FIELD_NAME}
OUTNAME="$ROOT/${TARGET_BASE}_wrp_${FIELD_BASE}.nii.gz"

THREADS=${THREADS:- -1}
echo "TARGET:     $TARGET"
echo "OUTNAME:    $OUTNAME"
echo "FIELD:      $FIELD"
echo "Threads:    $THREADS"
echo

easywarp-mri \
  --i       $TARGET \
  --o       $OUTNAME \
  --field   $FIELD \
  --threads "$THREADS" \
  --nearest