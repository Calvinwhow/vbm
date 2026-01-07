#!/bin/bash
# This script runs CAT12 standalone segmentation on a BIDS directory of NIfTI files mounted at /data.

# Set the path to the CAT12 standalone directory and MATLAB Runtime
CAT12_DIR=$CAT_PATH
MATLAB_RUNTIME=$MCRROOT

# Define the base directory as the mounted /data directory
BASE_DIR="/data"
FILE_TO_FIND="*T1*.nii*"

# Find all T1-weighted NIfTI files in the BIDS directory structure
T1_FILES=$(find "$BASE_DIR" -type f -name "$FILE_TO_FIND" | sort)

if [ -z "$T1_FILES" ]; then
  echo "No T1-weighted NIfTI files found in the BIDS directory."
  exit 1
fi

echo "Found the following T1-weighted NIfTI files:"
echo "$T1_FILES"

# Get the directory structure
for T1_FILE in $T1_FILES; do
  if [[ "$T1_FILE" =~ (.*\/sub-[^/]*/ses-[^/]*) ]]; then  # try to get session dir
    SUBJECT_DIR="${BASH_REMATCH[1]}"
  elif [[ "$T1_FILE" =~ (.*\/sub-[^/]*) ]]; then          # fall back to sub dir if no ses- dir
    SUBJECT_DIR="${BASH_REMATCH[1]}"
  else
    SUBJECT_DIR=$(dirname "$T1_FILE")                     # fall back to dirname of the T1.nii
  fi

  # Run CAT12 standalone smoothing on the segmented output files
  MWP_FILES=$(find "$SUBJECT_DIR" -type f -name "mwp*.nii")
  for MWP_FILE in $MWP_FILES; do
    SMOOTHED_FILE="$SUBJECT_DIR/s$(basename "$MWP_FILE")"
    if [ -f "$SMOOTHED_FILE" ]; then
      echo "Smoothing already completed for: $MWP_FILE. Skipping."
    else
      echo "Running CAT12 smoothing on: $MWP_FILE"
      cat_standalone.sh -b /root/scripts/cat_standalone_smooth_calvin.m "$MWP_FILE"
    fi
  done
done

echo "Processing complete for all T1-weighted files."