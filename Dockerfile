FROM ubuntu:20.04

# Install necessary packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    bzip2 \
    wget \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /usr/local/bin /tmp

# Copy environment.yaml to the image
COPY environment.yaml /usr/local/bin/

# Copy your update-runtime.sh script to the image
COPY update-runtime.sh /usr/local/bin/

# Make sure update-runtime.sh is executable
RUN chmod +x /usr/local/bin/update-runtime.sh

# Use bash shell for compatibility
SHELL ["/bin/bash", "-c"]

# Run the update-runtime script
RUN /usr/local/bin/update-runtime.sh

# Clean up
RUN /root/.local/bin/micromamba run -r /root/micromamba -n ldm python -s -m pip cache purge

