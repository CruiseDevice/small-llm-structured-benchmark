# Can Small LLMs Follow Instructions?

A systematic benchmark of open-source LLMs (0.6B–24B) for production structured output generation.

> **This repository is the code and task suite accompanying the paper
> "Can Small LLMs Follow Instructions? A Systematic Benchmark of Open-Source
> Models for Production Structured Output Generation" (Chavan, 2026).**
> The frozen state matching the submitted paper is tagged `v1.0`.

## What this benchmarks

- JSON generation from natural language prompts
- JSON Schema adherence under greedy and sampled decoding
- Function calling / tool use format
- Key-value extraction into structured format
- How **constrained decoding interacts with model scale** in the small-model regime

## Core research question

Existing benchmarks evaluate constrained-decoding frameworks on large models, and small-model studies report only unconstrained greedy-decoding numbers. We ask:

> **Does constrained decoding flatten the small-model scaling curve?**
>
> In particular, can a constrained 1B model match an unconstrained 3B model? Or do failures persist because they are semantic (wrong values, hallucinated fields) rather than structural, and therefore unreachable by token masking?

This question is only answerable with a controlled size ladder (e.g., Qwen 0.6B→4B, Llama 1B→3B, Gemma E2B→12B) and a shared task set — the two ingredients no prior work combines.

## How the benchmark is organized

The experiment is **notebook-driven**. Each model has one self-contained notebook
per phase: it embeds the 14-task suite inline, loads the model, runs the conditions
for that phase, scores the outputs, and writes the per-model CSV (plus a raw-output
JSON dump) into `results/`. Notebooks were executed on rented cloud GPUs using the
Docker image in this repo. Paper figures are rebuilt from the result CSVs by the
scripts in `scripts/`, each with pinned assertions against the published values.

## Repository layout

```
├── tasks/task_definitions.py    # The 14-task suite (canonical copy; also embedded
│                                #   inline in each notebook)
├── notebooks/                   # Execution notebooks, one per model per phase
│   ├── phase1/                  # 11 models × 14 tasks × 1 greedy sample
│   ├── phase2/                  # 6 models × 14 tasks × 3 temps × 3 samples
│   ├── phase3/                  # 5 models × 14 tasks × 3 decoding conditions
│   └── NOTEBOOK_SPEC.md         # Standardized notebook structure
├── evaluation/evaluator.py      # Reference implementation of the scoring semantics
│                                #   (validity, schema compliance, content accuracy);
│                                #   notebooks embed equivalent scoring inline
├── results/v2/                  # Per-model CSVs + raw generation JSONs per phase,
│                                #   plus the phase-3 semantic evaluation outputs
├── scripts/                     # Figure regeneration scripts (one per paper figure)
├── config/models.yaml           # Model configurations
├── Dockerfile                   # CUDA 12.4 image used for the cloud runs
├── build-image.sh               # Build & push the image
├── docs/                        # Working research notes from the experimental
│                                #   phases (kept for provenance, not maintained docs)
├── archive/                     # Superseded first-pass (v1) notebooks and results
└── paper_overleaf/              # LaTeX source of the paper
```

## Models tested

| Model | Parameters | Type |
|-------|-----------|------|
| Qwen3-0.6B | 0.6B | Dense |
| Qwen3-1.7B | 1.7B | Dense |
| Qwen3-4B-Instruct | 4B | Dense |
| Qwen3-30B-A3B | 30B (3B active) | MoE |
| Gemma 4 E2B-it | ~5B (2B active) | MoE |
| Gemma 4 12B-it | ~25B (12B active) | MoE |
| Gemma 3n 2B E2B | ~5B (2B active) | MoE |
| Llama 3.2 1B-Instruct | 1B | Dense |
| Llama 3.2 3B-Instruct | 3B | Dense |
| Phi-4-mini | 3.8B | Dense |
| Mistral-Small-3.2 24B | 24B | Dense (reference) |

## Phases

| Phase | Goal | Design |
|-------|------|--------|
| **Phase 1** | Baseline accuracy under ideal conditions | 14 tasks × 1 greedy sample per model |
| **Phase 2** | Robustness probe: are failures deterministic or sampling-induced? | 6 models × 14 tasks × 3 temperatures × 3 samples |
| **Phase 3** | Main contribution: constrained decoding × scale interaction | 5 models (Phase 2 subset with characterized failures) × 14 tasks × 3 decoding conditions |

## Metrics

- **Format Validity Rate**: % of outputs that are valid JSON
- **Schema Compliance Rate**: % of outputs matching the required schema
- **Content Accuracy**: correctness of extracted/generated values
- **Latency**: time to first token and total generation time
- **Token Efficiency**: output token count vs expected
- **Constrained-decoding overhead**: relative latency and token cost of each decoder

## Setup

```bash
pip install -r requirements.txt

# Phase 3 constrained decoding additionally requires:
pip install outlines xgrammar
```

## Usage

Run a model's notebook for the phase you want (see `notebooks/NOTEBOOK_SPEC.md`
for the standardized cell structure). Each notebook writes its results into
`results/v2/phase*/`.

To reproduce on a cloud GPU, build the image first:

```bash
./build-image.sh        # or: docker buildx build --platform linux/amd64 -t <user>/small-llm-benchmark .
```

To rebuild the paper figures from the committed results:

```bash
python scripts/regenerate_schema_validity.py    # Fig 1
python scripts/regenerate_content_accuracy.py   # Fig 2
python scripts/regenerate_heatmap.py            # Fig 3
python scripts/regenerate_overhead.py           # Fig 4
```

## Citation

```bibtex
@article{chavan2026smallllm,
  title={Can Small LLMs Follow Instructions? A Systematic Benchmark of Open-Source Models for Production Structured Output Generation},
  author={Chavan, Akash},
  journal={arXiv preprint arXiv:2610.XXXXX},
  year={2026}
}
```
