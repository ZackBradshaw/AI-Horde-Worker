#!/bin/bash

# Set default values if not provided
model_name=${model_name:-"internlm/internlm2-chat-7b"}
lmdeploy_url=${lmdeploy_url:-"http://localhost:23333"}
max_new_tokens=${max_new_tokens:-2048}
max_input_length=${max_input_length:-4096}
max_media_size=${max_media_size:-20480000}
num_gpus=${num_gpus:-1}

# Print the entered values
echo "Model Name: $model_name"
echo "LMDeploy URL: $lmdeploy_url"
echo "Max New Tokens: $max_new_tokens"
echo "Max Input Length: $max_input_length"
echo "Max Media Size: $max_media_size"
echo "Number of GPUs: $num_gpus"

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

# Install required packages
pip install lmdeploy requests pyyaml loguru pillow

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

# Construct the command string for lmdeploy
command_string="python -m lmdeploy.serve.turbomind.deploy \
    --model-name $model_name \
    --server-port ${lmdeploy_url##*:} \
    --instance-num 32 \
    --tp $num_gpus"

echo "Starting LMDeploy server:"
echo "$command_string"

# Run the lmdeploy server with the specified model and configuration
eval "$command_string" &

# Wait for the server to start
sleep 10

# Start the multi-modal worker
python3 -c "
from worker.workers.multimodal import MultiModalWorker
from worker.bridge_data.multimodal import MultiModalBridgeData

bridge_data = MultiModalBridgeData()
bridge_data.model = '$model_name'
bridge_data.lmdeploy_url = '$lmdeploy_url'
bridge_data.max_new_tokens = $max_new_tokens
bridge_data.max_input_length = $max_input_length
bridge_data.max_media_size = $max_media_size

worker = MultiModalWorker(bridge_data)
worker.start()
"

# Keep the script running
wait