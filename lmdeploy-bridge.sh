#!/bin/bash

# Set default values if not provided
model_name=${model_name:-"internlm/internlm-xcomposer2d5-7b"}
max_new_tokens=${max_new_tokens:-2048}
max_input_length=${max_input_length:-4096}
max_media_size=${max_media_size:-96000}
num_gpus=${num_gpus:-1}

# Print the entered values
echo "Model Name: $model_name"
echo "Max New Tokens: $max_new_tokens"
echo "Max Input Length: $max_input_length"
echo "Max Media Size: $max_media_size"
echo "Number of GPUs: $num_gpus"

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
./runtime.sh python -s bridge_multimodal.py  "$@"

