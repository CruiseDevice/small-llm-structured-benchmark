# =============================================================================
# Benchmark Docker Image for RunPod / Vast.ai
# Compatible with NVIDIA drivers >= 525.x (CUDA 12.4+)
#
# Build & push:
#   docker buildx build --platform linux/amd64 -t youruser/small-llm-benchmark .
#   docker push youruser/small-llm-benchmark
#
# Or just: ./build-image.sh
# =============================================================================

FROM --platform=linux/amd64 pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget vim nano htop tree \
    && rm -rf /var/lib/apt/lists/*

# ─── Layer 1: Core ML packages ────────────────────────────────────────────
RUN pip install --no-cache-dir \
    "transformers>=5.5.0,<6.0.0" \
    "accelerate>=0.27.0" \
    "sentencepiece>=0.2.0" \
    "protobuf>=4.25.0"

# ─── Layer 2: Flash Attention 2 (pre-compiled via nvcc from devel image) ──
RUN pip install --no-cache-dir "flash-attn>=2.5.0" --no-build-isolation

# ─── Layer 3: Constrained decoding & validation ───────────────────────────
RUN pip install --no-cache-dir \
    "outlines>=0.0.34" \
    "lm-format-enforcer>=0.10.0" \
    "jsonschema>=4.21.0" \
    "rfc3339-validator>=0.1.4"

# ─── Layer 4: Data science & analysis ─────────────────────────────────────
RUN pip install --no-cache-dir \
    "pandas>=2.1.0" \
    "matplotlib>=3.8.0" \
    "seaborn>=0.13.0" \
    "scikit-learn>=1.4.0" \
    "datasets>=2.18.0" \
    "pyyaml>=6.0" \
    "tqdm>=4.66.0"

# ─── Jupyter ──────────────────────────────────────────────────────────────
RUN pip install --no-cache-dir jupyterlab ipywidgets

# ─── HuggingFace cache ────────────────────────────────────────────────────
ENV HF_HOME=/workspace/.cache/huggingface
ENV TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers

WORKDIR /workspace

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
