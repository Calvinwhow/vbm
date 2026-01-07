### GET DEPENDENCIES ###
FROM --platform=linux/amd64 calvinwhow/vbm:latest AS cat12
FROM --platform=linux/amd64 calvinwhow/er:latest AS easyreg
FROM --platform=linux/amd64 python:3.10.8-slim

# Get matlab, easyreg, and python with associated deps
COPY --from=cat12 /opt /opt
RUN apt-get update \
 && apt-get -y install wget nano unzip libxext6 libxt6 moreutils dos2unix \
 && apt-get clean 

COPY --from=easyreg /root /root

### CHECK DEPENDENCIES ###
# Run install checks (filesystem, matlab, SPM, CAT12, Python, )
RUN echo "=== Checking filesystem layout ===" && \
    ls -lah /opt && \
    ls -lah /opt/mcr && \
    ls -lah /opt/spm

RUN echo "=== Checking MATLAB MCR env ===" && \
    test -d /opt/mcr/v93 && \
    echo "MCRROOT=/opt/mcr/v93"

RUN echo "=== Checking SPM binary ===" && \
    test -x /opt/spm/run_spm12.sh 
    # /opt/spm/run_spm12.sh /opt/mcr/v93 --version

RUN echo "=== Checking CAT12 toolbox ===" && \
    test -d /opt/spm/spm12_mcr/home/gaser/gaser/spm/spm12/toolbox/cat12 && \
    ls -lah /opt/spm/spm12_mcr/home/gaser/gaser/spm/spm12/toolbox/cat12

RUN echo "=== Checking Python ===" && \
    which python && \
    python --version && \
    which pip && \
    pip --version

### NEUROIMAGING IMAGE ### 
ENV MCRROOT=/opt/mcr/v93
ENV CAT_PATH=/opt/spm/spm12_mcr/home/gaser/gaser/spm/spm12/toolbox/cat12
ENV PYTHONPATH="/root/scripts:/root/easyreg"
ENV SCRIPT_DIR=/root/scripts
ENV CAT_SCRIPTS=/opt/CAT12.8.2_R2017b_MCR_Linux/standalone
ENV DATA_DIR=/root/data
ENV SESSION=ses-01

COPY ./scripts /root/scripts
COPY ./assets /root/assets
COPY requirements.txt /root/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r /root/requirements.txt && \
    rm -rf /root/requirements.txt
RUN git clone https://github.com/Calvinwhow/calvin_utils.git /root/calvin_utils && \
    pip install -e /root/calvin_utils --no-deps

WORKDIR /root

CMD [ "/root/scripts/run_pipeline.sh" ]
