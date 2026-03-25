#!/bin/bash
set -euo pipefail
# This script runs CAT12 standalone segmentation on a BIDS directory of NIfTI files mounted at /data.
T1_FILE=${1:?usage: $0 /path/to/T1.nii.gz}
# Set the path to the CAT12 standalone directory and MATLAB Runtime
CAT12_DIR=${CAT_PATH:-}
MATLAB_RUNTIME=${MCRROOT:-}

# 1 - Get dir structures
T1_DIR=$(dirname "$T1_FILE")
SUBJECT_DIR=$(dirname "$T1_DIR")

echo SUBJECT DIR=$SUBJECT_DIR

# 2 - Run the segmentation
if find "$SUBJECT_DIR" -type f -iname "*mwp*" -print -quit 2>/dev/null | grep . > /dev/null ; then
  echo "Segmentation already completed for: $T1_FILE. Skipping."
else
  echo "Running CAT12 segmentation on: $T1_FILE"
  ${CAT_SCRIPTS}/cat_standalone.sh -b /root/scripts/cat_standalone_segment_calvin.m "$T1_FILE"
  echo "Segmentation completed for: $T1_FILE"
fi

# 3 - Move or delete new files from CAT12
mkdir -p "$SUBJECT_DIR/mri"
mkdir -p "$SUBJECT_DIR/report"
mkdir -p "$SUBJECT_DIR/err"
mkdir -p "$SUBJECT_DIR/cat12"

echo "$T1_DIR"

find "$T1_DIR" -maxdepth 2 -type f -name "mwp*.nii" -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "wm*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "p0*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "wp0*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "iy_*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "y_*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "rp*_rigid.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "wj*.nii"  -exec mv -n {} "$SUBJECT_DIR/mri/" \;

find "$T1_DIR" -maxdepth 2 -type f -name "*catreport*" -exec mv -n {} "$SUBJECT_DIR/report/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "*catlog*"    -exec mv -n {} "$SUBJECT_DIR/err/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "cat*.mat"  -exec mv -n {} "$SUBJECT_DIR/cat12/" \;
find "$T1_DIR" -maxdepth 2 -type f -name "cat*.xml"  -exec mv -n {} "$SUBJECT_DIR/cat12/" \;

rmdir "$T1_DIR/mri" 2>/dev/null || true
rmdir "$T1_DIR/report" 2>/dev/null || true
rmdir "$T1_DIR/err" 2>/dev/null || true
rmdir "$T1_DIR/cat12" 2>/dev/null || true

echo "Finished organizing outputs for $SUBJECT_DIR"
