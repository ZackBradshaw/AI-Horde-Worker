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
done

# Determine the correct environment file
CONDA_ENVIRONMENT_FILE=/usr/local/bin/environment.yaml
if [ "$scribe" = true ]; then
    CONDA_ENVIRONMENT_FILE=/usr/local/bin/environment_scribe.yaml
fi

# Install micromamba
echo "Installing micromamba..."
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)

# Source the shell configuration file to activate micromamba
echo "Sourcing .bashrc to activate micromamba..."
source "$HOME/.bashrc"

# Check if conda environment exists and create it if it does not
if [ ! -f "$HOME/micromamba/envs/ldm/bin/python" ]; then
    echo "Creating conda environment from ${CONDA_ENVIRONMENT_FILE}..."
    if $HOME/.local/bin/micromamba create --no-shortcuts -r "$HOME/micromamba" -n ldm -f "${CONDA_ENVIRONMENT_FILE}" -y; then
        echo "Conda environment created successfully."
    else
        echo "Error: Failed to create conda environment."
        exit 1
    fi
fi

# Debug: list available versions of cudatoolkit
echo "Checking available versions of cudatoolkit..."
$HOME/.local/bin/micromamba search cudatoolkit

# Always ensure the environment is up-to-date
echo "Updating conda environment from ${CONDA_ENVIRONMENT_FILE}..."
if $HOME/.local/bin/micromamba create --no-shortcuts -r "$HOME/micromamba" -n ldm -f "${CONDA_ENVIRONMENT_FILE}" -y; then
    echo "Conda environment updated successfully."
else
    echo "Error: Failed to update conda environment."
    exit 1
fi

echo "Runtime environment setup completed successfully."

