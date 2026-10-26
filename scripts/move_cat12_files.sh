# --- User Arguments --- #
ROOT="/Volumes/NIMLAB/dl_archive/Atrophy_Howard/01o_XiaoControls_Atrophy/BIDS"

# --- DO NOT TOUCH --- #
TRGTS=("label" "err" "mri" "report")
SUBJECTS=("$ROOT"/*)

for sub in "${SUBJECTS[@]}"; do
    echo "Found subject directory $sub"
    for target in "${TRGTS[@]}"; do
        BASE="${sub}/ses-01/anat/${target}"
        DEST="${sub}/ses-01/${target}"
        echo $BASE
        if [ -d "$BASE" ]; then # Folder exists
            echo "Directory $BASE exists. Moving to $DEST"
            mv "$BASE" "$DEST"
        fi
    done
done