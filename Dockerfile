FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git wget curl vim tmux python3 python3-pip

WORKDIR /workspace

RUN curl https://ollama.ai/install.sh | sh

RUN git clone https://github.com/agiresearch/AIOS.git \
    && cd AIOS \
    && pip install -r requirements.txt

# Set the default command to run when starting the container
CMD ["/bin/bash"]
