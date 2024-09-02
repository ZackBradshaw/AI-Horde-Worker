#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print each command before executing it (for debugging)
set -x

echo "Starting update-runtime.sh..."

ignore_hordelib=false
hordelib=false
scribe=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --hordelib)
        hordelib=true
        shift
        ;;
        --scribe)
        scribe=true
        shift
        ;;
        *)
        echo "Unknown option: $key"
        exit 1
        ;;
    esac
done

# Determine the correct environment file
CONDA_ENVIRONMENT_FILE="$HOME/.lib/horde/worker/environment.yaml"
if [ "$scribe" = true ]; then
    CONDA_ENVIRONMENT_FILE="$HOME/.lib/horde/worker/environment_scribe.yaml"
fi

# Create a basic environment file if it doesn't exist
if [ ! -f "$CONDA_ENVIRONMENT_FILE" ]; then
    echo "Environment file not found. Creating a basic one..."
    cat << EOF > "$CONDA_ENVIRONMENT_FILE"
name: ldm
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.8
  - pip
  - pip:
    - lmdeploy
    - requests
    - pyyaml
    - loguru
    - pillow
    - decord
EOF
fi

# Install micromamba
echo "Installing micromamba..."
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)

# Source the shell configuration file to activate micromamba
echo "Sourcing .bashrc to activate micromamba..."
source "$HOME/.bashrc"

# Function to create conda environment
create_conda_env() {
    echo "Creating conda environment from ${CONDA_ENVIRONMENT_FILE}..."
    if $HOME/.local/bin/micromamba create --no-shortcuts -r "$HOME/micromamba" -n ldm -f "${CONDA_ENVIRONMENT_FILE}" -y; then
        echo "Conda environment created successfully."
    else
        echo "Error: Failed to create conda environment with cudatoolkit. Trying without..."
        # Remove cudatoolkit from the environment file
        sed -i '/cudatoolkit/d' "${CONDA_ENVIRONMENT_FILE}"
        if $HOME/.local/bin/micromamba create --no-shortcuts -r "$HOME/micromamba" -n ldm -f "${CONDA_ENVIRONMENT_FILE}" -y; then
            echo "Conda environment created successfully without cudatoolkit."
        else
            echo "Error: Failed to create conda environment. Exiting."
            exit 1
        fi
    fi
}

# Check if conda environment exists and create it if it does not
if [ ! -f "$HOME/micromamba/envs/ldm/bin/python" ]; then
    create_conda_env
fi

# Debug: list available versions of cudatoolkit
echo "Checking available versions of cudatoolkit..."
$HOME/.local/bin/micromamba search cudatoolkit

# Always ensure the environment is up-to-date
echo "Updating conda environment from ${CONDA_ENVIRONMENT_FILE}..."
if ! $HOME/.local/bin/micromamba update --no-shortcuts -r "$HOME/micromamba" -n ldm -f "${CONDA_ENVIRONMENT_FILE}" -y; then
    echo "Error: Failed to update conda environment. Trying to recreate..."
    $HOME/.local/bin/micromamba remove -r "$HOME/micromamba" -n ldm --all -y
    create_conda_env
fi

echo "Runtime environment setup completed successfully."

