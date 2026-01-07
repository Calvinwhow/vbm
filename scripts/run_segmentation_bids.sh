#!/bin/bash
set -euo pipefail
# This script runs CAT12 standalone segmentation on a BIDS directory of NIfTI files mounted at /data.

# Set the path to the CAT12 standalone directory and MATLAB Runtime
CAT12_DIR=${CAT_PATH:-}
MATLAB_RUNTIME=${MCRROOT:-}

if [[ -z "$CAT12_DIR" || -z "$MATLAB_RUNTIME" ]]; then
  echo "CAT_PATH and MCRROOT must be set for CAT12 segmentation."
  exit 1
fi

# Define the base directory as the mounted /data directory
BASE_DIR="${DATA_DIR:-/root/data}"
FILE_TO_FIND="*T1*.nii*"

# Find all T1-weighted NIfTI files in the BIDS directory structure
T1_FILES=$(find "$BASE_DIR" -type f -name "$FILE_TO_FIND" | sort)

if [ -z "$T1_FILES" ]; then
  echo "No T1-weighted NIfTI files found in the BIDS directory."
  exit 1
fi

echo "Found the following T1-weighted NIfTI files:"
echo "$T1_FILES"

for T1_FILE in $T1_FILES; do
  # 1 - Get dir structures
  if [[ "$T1_FILE" =~ (.*\/sub-[^/]*/ses-[^/]*) ]]; then  # try to get session dir
    SUBJECT_DIR="${BASH_REMATCH[1]}"
  elif [[ "$T1_FILE" =~ (.*\/sub-[^/]*) ]]; then          # fall back to sub dir if no ses- dir
    SUBJECT_DIR="${BASH_REMATCH[1]}"
  else
    SUBJECT_DIR=$(dirname "$T1_FILE")                     # fall back to dirname of the T1.nii
  fi
  
  # 2 - Run the segmentation
  if find "$SUBJECT_DIR" -type f -name "mwp*.nii" -print -quit | grep . > /dev/null ; then
    echo "Segmentation already completed for: $T1_FILE. Skipping."
    continue
  else
    echo "Running CAT12 segmentation on: $T1_FILE"
    ${CAT_SCRIPTS}/cat_standalone.sh -b /root/scripts/cat_standalone_segment_calvin.m "$T1_FILE"
    echo "Segmentation completed for: $T1_FILE"
  fi

  # 3 - Move or delete new files from CAT12
  mkdir -p "$SUBJECT_DIR/mri"
  mkdir -p "$SUBJECT_DIR/report"
  mkdir -p "$SUBJECT_DIR/err"

  find "$SUBJECT_DIR" -maxdepth 1 -type f -name "mwp*.nii" -exec mv -n {} "$SUBJECT_DIR/mri/" \;
  find "$SUBJECT_DIR" -maxdepth 1 -type f -name "wm*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
  find "$SUBJECT_DIR" -maxdepth 1 -type f -name "p0*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;

  find "$SUBJECT_DIR" -maxdepth 1 -type f -name "*catreport*" -exec mv -n {} "$SUBJECT_DIR/report/" \;
  find "$SUBJECT_DIR" -maxdepth 1 -type f -name "*catlog*"    -exec mv -n {} "$SUBJECT_DIR/err/" \;

  echo "Finished organizing outputs for $SUBJECT_DIR"

done

echo "Processing complete for all T1-weighted files."
