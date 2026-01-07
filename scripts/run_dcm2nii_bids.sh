#!/bin/bash
# This script runs CAT12 standalone segmentation on a BIDS directory of NIfTI files mounted at /data.

# Set the path to the CAT12 standalone directory and MATLAB Runtime
CAT12_DIR=$CAT_PATH
MATLAB_RUNTIME=$MCRROOT

# Define the base directory as the mounted /data directory
BASE_DIR="/data"
FILE_TO_FIND="*.dcm*"

# Find all T1-weighted NIfTI files in the BIDS directory structure
T1_FILES=$(find "$BASE_DIR" -type f -name "$FILE_TO_FIND" | sort)

if [ -z "$T1_FILES" ]; then
  echo "No T1-weighted NIfTI files found in the BIDS directory."
  exit 1
fi

echo "Found the following T1-weighted NIfTI files:"
echo "$T1_FILES"

# 1) Run CAT12 standalone segmentation on each T1-weighted file
for T1_FILE in $T1_FILES; do
  SUBJECT_DIR=$(dirname "$T1_FILE")
  T1_BASENAME=$(basename "$T1_FILE")
  NEW_DIR="$SUBJECT_DIR/dcm2nii"
  mkdir -p "$NEW_DIR"
  cp "$T1_FILE" "$NEW_DIR/"
  
  # 2) Run dicom to nii conversion
  if ls "$NEW_DIR"/*.nii 1> /dev/null 2>&1; then
    echo "Dicom to nii already completed for: $T1_FILE. Skipping."
  else
    echo "Running CAT12 dicom to nifti conversion on: $T1_FILE"
    cat_standalone.sh -b /root/scripts/cat_standalone_dicom2nii.m "$NEW_DIR/$T1_BASENAME"
  fi
  done
done
