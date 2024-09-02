#!/bin/bash

# Set default values if not provided
export model_name=${model_name:-"internlm/internlm-xcomposer2d5-7b"}
export max_new_tokens=${max_new_tokens:-2048}
export max_input_length=${max_input_length:-4096}
export max_media_size=${max_media_size:-96000}
export num_gpus=${num_gpus:-1}

# Print the entered values
echo "Model Name: $model_name"
echo "Max New Tokens: $max_new_tokens"
echo "Max Input Length: $max_input_length"
echo "Max Media Size: $max_media_size"
echo "Number of GPUs: $num_gpus"

# Ensure the runtime environment is set up
if [ ! -f "conda/envs/linux/bin/python" ]; then
    echo "Setting up runtime environment..."
    ./update-runtime.sh
    if [ $? -ne 0 ]; then
        echo "Failed to set up runtime environment. Exiting."
        exit 1
    fi
fi

# Use the existing runtime to install packages
echo "Installing required packages..."
./runtime.sh pip install -U pip
./runtime.sh pip install -e .
./runtime.sh pip install lmdeploy requests pyyaml loguru pillow decord

# Set environment variables
export HORDE_URL="https://stablehorde.net"
export HORDE_API_KEY="your_api_key_here"
export HORDE_WORKER_NAME="MultiModal_Worker_${RANDOM}"
export HORDE_MAX_POWER=8
export HORDE_MAX_THREADS=1
export HORDE_QUEUE_SIZE=0
export HORDE_ALLOW_UNSAFE_IP="true"
export REQUIRE_UPFRONT_KUDOS="false"
export STATS_OUTPUT_FREQUENCY=30
export DISABLE_TERMINAL_UI="false"

# Start the multi-modal worker
echo "Starting multi-modal worker..."
./runtime.sh python -s bridge_multimodal.py "$@"
