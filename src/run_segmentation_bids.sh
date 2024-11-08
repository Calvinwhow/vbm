#!/bin/bash
# This script runs CAT12 standalone segmentation on a BIDS directory of NIfTI files mounted at /data.

# Set the path to the CAT12 standalone directory and MATLAB Runtime
CAT12_DIR=$CAT_PATH
MATLAB_RUNTIME=$MCRROOT

# Define the base directory as the mounted /data directory
BASE_DIR="/data"
FILE_TO_FIND="*T1w.nii*"

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
  MRI_DIR="$SUBJECT_DIR/mri"
  
  # 2) Run the segmentation
  if ls "$SUBJECT_DIR"/mwp*.nii 1> /dev/null 2>&1; then
    echo "Segmentation already completed for: $T1_FILE. Skipping."
  else
    # Run the segmentation
    echo "Running CAT12 segmentation on: $T1_FILE"
    cat_standalone.sh -b /scripts/cat_standalone_segment_calvin.m "$T1_FILE"
    echo "Segmentation completed for: $T1_FILE"
  fi

  # 3) Run CAT12 standalone smoothing on the segmented output files
  MWP_FILES=$(ls "$SUBJECT_DIR"/mwp*.nii)
  for MWP_FILE in $MWP_FILES; do
    SMOOTHED_FILE="$SUBJECT_DIR/s$(basename "$MWP_FILE")"
    if [ -f "$SMOOTHED_FILE" ]; then
      echo "Smoothing already completed for: $MWP_FILE. Skipping."
    else
      echo "Running CAT12 smoothing on: $MWP_FILE"
      cat_standalone.sh -b /scripts/cat_standalone_smooth_calvin.m "$MWP_FILE"
    fi
  done
done

echo "Processing complete for all T1-weighted files."