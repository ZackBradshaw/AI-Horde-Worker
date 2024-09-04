#!/bin/bash

ignore_hordelib=false
scribe=true

# Parse command line arguments
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --hordelib)
    hordelib=true
    shift # past argument
    ;;
    --scribe)
    scribe=true
    shift
    ;;
    *)    # unknown option
    echo "Unknown option: $key"
    exit 1
    ;;
esac
shift # past argument or value
done

CONDA_ENVIRONMENT_FILE=environment.yaml
if [ "$scribe" = true ]; then
    CONDA_ENVIRONMENT_FILE=environment_scribe.yaml
fi

# Check if conda environment exists, if not create it
if ! conda env list | grep -q "^linux "; then
    conda env create -f ${CONDA_ENVIRONMENT_FILE}
else
    conda env update -f ${CONDA_ENVIRONMENT_FILE}
fi

# Activate the conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate linux

# Install required packages
if [ "$hordelib" = true ]; then
    pip uninstall -y hordelib horde_model_reference
    pip install hordelib horde_model_reference
elif [ "$scribe" = true ]; then
    pip install -r requirements-scribe.txt
else
    pip uninstall -y nataili
    pip install -r requirements.txt
fi

# Install lmdeploy and other necessary packages
pip install lmdeploy requests pyyaml loguru pillow decord

# Set environment variables for CUDA
export PATH=/usr/local/cuda-11.5/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.5/lib64:$LD_LIBRARY_PATH

# Start the multi-modal worker
echo "Starting multi-modal worker..."
python3 bridge_multimodal.py "$@"
