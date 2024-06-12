# Use the Ubuntu 22.04 base image
FROM ubuntu:22.04

# Update the package list and install dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    vim \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh \
    && /opt/conda/bin/conda init

# Set path to conda
ENV PATH=/opt/conda/bin:$PATH

RUN curl https://ollama.ai/install.sh | sh

# Create a working directory
WORKDIR /workspace

RUN conda create -n aios python=3.11 -y \
    && /bin/bash -c "source /opt/conda/bin/activate aios" \
    && git clone https://github.com/dongyuanjushi/AIOS.git \
    && cd AIOS

# Set the default command to run when starting the container
CMD ["/bin/bash"]
