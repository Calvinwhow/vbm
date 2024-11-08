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
  REPORT_DIR="$SUBJECT_DIR/report"
  
  # 2) Run the segmentation
  echo "Running CAT12 segmentation on: $T1_FILE"
  cat_standalone.sh -b /opt/spm/standalone/cat_standalone_segment_calvin.m "$T1_FILE"
  if ! ls "$MRI_DIR"/*mwp*.nii 1> /dev/null 2>&1; then # check for output
    echo "No output files found for: $T1_FILE after waiting. Skipping."
    continue   # If no output files are found, skip this subject
  fi
  echo "Segmentation completed for: $T1_FILE"

  # 3) Run CAT12 standalone smoothing on the segmented output files
  MWP_FILES=$(ls "$MRI_DIR"/*mwp*.nii)
  for MWP_FILE in $MWP_FILES; do
    echo "Running CAT12 smoothing on: $MWP_FILE"
    cat_standalone.sh -b /opt/spm/standalone/cat_standalone_smooth_calvin.m "$MWP_FILE"
    SMOOTHED_FILE="$MRI_DIR/s2$(basename "$MWP_FILE")"
    if [ ! -f "$SMOOTHED_FILE" ]; then
        echo "Smoothing failed: Expected smoothed file not found for: $MWP_FILE"
        continue
    fi
  done

  # 4) Extract TIV for each file from the 'report/' folder
  XML_REPORT=$(ls "$REPORT_DIR"/cat_*.xml 2> /dev/null)
  if [ -n "$XML_REPORT" ]; then
    echo "Extracting TIV from: $XML_REPORT"
    cat_standalone.sh -b /opt/spm/standalone/cat_standalone_get_TIV_calvin.m "$XML_REPORT"

    # Check for the presence of the TIV output file
    TIV_FILE="$REPORT_DIR/TIV.txt"
    if [ ! -f "$TIV_FILE" ]; then
      echo "TIV extraction failed: Expected TIV file not found for: $XML_REPORT"
        continue
    fi
    echo "TIV extraction successful: $TIV_FILE"
done

echo "Processing complete for all T1-weighted files."