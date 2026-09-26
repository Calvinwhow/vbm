#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

# --- USER INPUT ---
USER_ID="rm026"
USER_EMAIL="rmacfadyen@bwh.harvard.edu"
BIDS_DIR="/data/nimlab/USERS/Atrophy_Howard/schmahmann_validation_dataset/"   # root containing sub-* folders
SESSION="ses*"                                       # glob, matched inside the container
T1_DIR="anat"                                        # glob, matched inside the container
T1_FILE_BASENAME="t1"                                # matched case-insensitively (T1w, t1mri, ...)
DRY_RUN=false                                       # true = print the job script, submit nothing
CTRL_DIST="ctrl_dist"
ATROPHY_ONLY=false

# --- ENVIRONMENT SETUP ---
current_time=$(date '+%Y-%m-%d_%H-%M-%S')
SIF_PATH="/data/nimlab/USERS/ahg26/Collaborators/Calvin/Software/vbm/vbm_pipeline.sif"
LOG_DIR="/PHShome/rm026/cerebellum_project/schmahmann_validation_atrophy/logs/batch-${current_time}"

# Patched copy of the container's /root/scripts/run_pipeline.sh. The version
# baked into the SIF uses case-sensitive `find -path "*T1*"`, which misses the
# lowercase filenames (t1.nii.gz) in this cohort. The patched copy uses -ipath.
# Bind-mounted over the original because the SIF is read-only.
PATCHED_PIPELINE="/data/nimlab/USERS/ahg26/vbm_pipeline/patched/run_pipeline.sh"

# Reference copy of the container's CAT12 tree.
#
# The SIF ships spm12_mcr/ extracted in May 2021 but spm12.ctf dated Jan 2023.
# At runtime the MATLAB Compiler Runtime judges the extraction stale and tries
# to re-extract it in place under /opt -- which is read-only in a SIF. It fails,
# then exits 0 without running the job, so every wrapper reads success and the
# output directories come out empty. Under Docker this never surfaced because
# the container filesystem was writable.
#
# Each job therefore copies this tree to node-local scratch and bind-mounts the
# copy read-write, giving the MCR somewhere to extract. Per-job rather than
# shared: concurrent extractions into one directory corrupt it.
MCR_SOURCE="/data/nimlab/USERS/ahg26/vbm_pipeline/cat12_writable"

# Fail at submission time rather than producing N jobs that each die identically.
BIDS_DIR="${BIDS_DIR%/}"
if [[ ! -r "$SIF_PATH" ]]; then
    echo "ERROR: SIF not readable: '${SIF_PATH}'" >&2
    exit 1
fi
if [[ ! -d "$BIDS_DIR" ]]; then
    echo "ERROR: BIDS directory not found: '${BIDS_DIR}'" >&2
    exit 1
fi
if [[ ! -r "$PATCHED_PIPELINE" ]]; then
    echo "ERROR: patched pipeline not readable: '${PATCHED_PIPELINE}'" >&2
    exit 1
fi
if ! grep -q -- '-ipath' "$PATCHED_PIPELINE"; then
    echo "ERROR: '${PATCHED_PIPELINE}' does not contain the -ipath fix." >&2
    exit 1
fi
if [[ ! -d "$MCR_SOURCE/spm12_mcr" ]]; then
    echo "ERROR: CAT12 reference tree not found: '${MCR_SOURCE}'" >&2
    exit 1
fi
mkdir -p "$LOG_DIR"

# --- JOB SCRIPT ---
# Quoted heredoc: nothing below expands here. Every variable is resolved either
# by the job shell at runtime (values arrive via sbatch --export) or by the
# container shell (the single-quoted block passed to bash -c).
SBATCH_SCRIPT=$(cat <<'EOF'
#!/usr/bin/env bash
#SBATCH -p normal,long
#SBATCH -c 4
#SBATCH --mem=40000
#SBATCH --mail-type=END
set -euo pipefail

module load singularity

# Node-local scratch: a private CAT12 tree for the MCR to extract into, and a
# private HOME for MATLAB to initialise in. Both must be writable; with neither,
# the runtime fails and still exits 0.
# JOB_TMP="/tmp/vbm_${SLURM_JOB_ID}"
JOB_TMP="/PHShome/rm026/cerebellum_project/schmahmann_validation_atrophy/tmp/vbm_${SLURM_JOB_ID}"
mkdir -p "${JOB_TMP}/cat12" "${JOB_TMP}/home"
trap 'rm -rf "${JOB_TMP}"' EXIT
cp -a "${MCR_SOURCE}/." "${JOB_TMP}/cat12/"

CONTAINER_BIDS_DIR="/root/data"
CONTAINER_SUBJECT_DIR="${CONTAINER_BIDS_DIR}/${SUBJECT_ID}"

# --home replaces --no-home: MATLAB needs a writable home, but it must not be
# the host $HOME, whose profile would clobber the container's PATH.
singularity exec \
    --cleanenv \
    --home "${JOB_TMP}/home" \
    --env TMPDIR="${JOB_TMP}/home" \
    --bind "${SUBJECT_DIR}:${CONTAINER_SUBJECT_DIR}" \
    --bind "${PATCHED_PIPELINE}:/root/scripts/run_pipeline.sh" \
    --bind "${JOB_TMP}/cat12:/opt/CAT12.8.2_R2017b_MCR_Linux" \
    --env BIDS_DIR="${CONTAINER_BIDS_DIR}" \
    --env SUBJECT_ID="${SUBJECT_ID}" \
    --env SESSION="${SESSION}" \
    --env T1_DIR="${T1_DIR}" \
    --env T1_FILE_BASENAME="${T1_FILE_BASENAME}" \
    "${SIF_PATH}" \
    /bin/bash -c '
        set -euo pipefail

        echo "Subject dir (in container): ${BIDS_DIR}/${SUBJECT_ID}"
        echo "Search pattern: ${SESSION}/${T1_DIR}/*${T1_FILE_BASENAME}*.nii[.gz]"

        # ! -name "._*": macOS writes AppleDouble sidecar files (._t1.nii.gz)
        # when copying to a non-HFS filesystem. They are metadata, not scans,
        # and would otherwise match the T1 pattern.
        # -iname: BIDS canonical naming capitalises T1w; the configured basename
        # may not match its case.

        mapfile -t T1_MATCHES < <(
            find "${BIDS_DIR}/${SUBJECT_ID}" -type f \
                ! -name "._*" \
                \( -iname "*${T1_FILE_BASENAME}*.nii" -o -iname "*${T1_FILE_BASENAME}*.nii.gz" \) \
                -path "*/${SESSION}/${T1_DIR}/*" \
                | sort
        )
        
        # Exactly one T1 is required: zero means the subject is unusable, more
        # than one means the selection would be arbitrary and irreproducible.
        # NOTE: run_pipeline.sh does not consume this argument -- it re-scans
        # DATA_DIR itself and loops over every match. This check therefore acts
        # as a pre-flight gate, not as file selection.


        # if [[ ${#T1_MATCHES[@]} -ne 1 ]]; then
        #     echo "ERROR: expected exactly 1 T1 for ${SUBJECT_ID}, found ${#T1_MATCHES[@]}" >&2
        #     printf "  %s\n" "${T1_MATCHES[@]}" >&2
        #     exit 1
        # fi

        T1W_FILE="${T1_MATCHES[0]}"
        echo "Using T1 file: ${T1W_FILE}"

        bash /root/scripts/run_pipeline.sh "${T1W_FILE}"
    '
EOF
)

# --- SUBMISSION ---
SUBJECT_DIRECTORIES=("$BIDS_DIR"/sub-*/)   # sub-* only: skips derivatives/, code/, sourcedata/
if [[ ${#SUBJECT_DIRECTORIES[@]} -eq 0 ]]; then
    echo "ERROR: No sub-* directories found in: $BIDS_DIR" >&2
    exit 1
fi

for SUBJECT_DIR in "${SUBJECT_DIRECTORIES[@]}"; do

    SUBJECT_DIR="${SUBJECT_DIR%/}"
    SUBJECT_ID="$(basename "$SUBJECT_DIR")"

    SESSION_DIRECTORIES=("$BIDS_DIR"/"${SUBJECT_ID}"/ses-*/) 

    ### IDENTIFY EVERY SESSION DIRECTORY AND LAUNCH A PROCESS FOR IT ###
    # if [[ ${#SESSION_DIRECTORIES[@]} -eq 1 ]]; then     # SKIP IF DONE <----hardcode. remove if ever used agian
    #     echo "Skipping ${SUBJECT_ID}, which should have already run" >&2
    #     continue 
    # fi
    # Else, iterate over them and launch each.
    for SESSION_DIR in "${SESSION_DIRECTORIES[@]}"; do
        echo "SESSION IDENTIFIED: $SESSION_DIR"
        SESSION="$(basename "$SESSION_DIR")"

        if  test -d ${SESSION_DIR}/"mri"; then     # SKIP IF DONE <----hardcode. remove if ever used agian
            echo "Skipping ${SESSION_DIR}, which already ran" >&2
            continue 
        fi

        if [[ "$DRY_RUN" == true ]]; then
            echo "--- DRY RUN: ${SUBJECT_ID} ---"
            echo "SUBJECT_DIR=${SUBJECT_DIR}"
            echo "SES_DIR=${SESSION_DIR}"
            echo "SESSION=${SESSION}"
            echo "T1_DIR=${T1_DIR}"
            echo "CTRL_DIST=${CTRL_DIST}"
            echo "ATROPHY_ONLY=${ATROPHY_ONLY}"
            printf '%s\n' "$SBATCH_SCRIPT"
            echo "------------------------------"
        else
            printf '%s\n' "$SBATCH_SCRIPT" | sbatch \
                -J "hcp_${SUBJECT_ID}" \
                -o "${LOG_DIR}/slurm.${SUBJECT_ID}.%j.out" \
                -e "${LOG_DIR}/slurm.${SUBJECT_ID}.%j.err" \
                --mail-user="${USER_EMAIL}" \
                --export="ALL,SUBJECT_DIR=${SUBJECT_DIR},SUBJECT_ID=${SUBJECT_ID},SESSION=${SESSION},T1_DIR=${T1_DIR},T1_FILE_BASENAME=${T1_FILE_BASENAME},CTRL_DIST=${CTRL_DIST},ATROPHY_ONLY=${ATROPHY_ONLY},SIF_PATH=${SIF_PATH},PATCHED_PIPELINE=${PATCHED_PIPELINE},MCR_SOURCE=${MCR_SOURCE}"
            echo "Submitted ${SUBJECT_ID}"
        fi
    done
done

echo "Finished batch-${current_time}"
