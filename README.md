# Can Small LLMs Follow Instructions?

A systematic benchmark of open-source LLMs (0.6B–24B) for production structured output generation.

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

## Models tested

| Model | Parameters | Type | Phase 1 status | Phase 3 status |
|-------|-----------|------|----------------|----------------|
| Qwen3-0.6B | 0.6B | Dense | ✅ complete | ✅ complete |
| Qwen3-1.7B | 1.7B | Dense | ✅ complete | ⏳ pending |
| Qwen3-4B-Instruct | 4B | Dense | ✅ complete | ✅ complete |
| Qwen3-30B-A3B | 30B (3B active) | MoE | ✅ complete | ⏳ pending |
| Gemma 4 E2B-it | ~5B (2B active) | MoE | ✅ complete | ⏳ pending |
| Gemma 4 12B-it | ~25B (12B active) | MoE | ✅ complete | ⏳ pending |
| Gemma 3n 2B E2B | ~5B (2B active) | MoE | ✅ complete | ⏳ pending |
| Llama 3.2 1B-Instruct | 1B | Dense | ✅ complete | ✅ complete |
| Llama 3.2 3B-Instruct | 3B | Dense | ✅ complete | ✅ complete |
| Phi-4-mini | 3.8B | Dense | ✅ complete | ✅ complete |
| Mistral-Small-3.2 24B | 24B | Dense (reference) | ✅ complete | ⏳ pending |

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
```

For Phase 3 constrained decoding, install the framework extras:

```bash
pip install outlines xgrammar lm-format-enforcer
```

## Usage

```bash
# Run full unconstrained baseline (Phase 1)
python run_benchmark.py

# Run specific model
python run_benchmark.py --model qwen3-4b

# Run with constrained decoding (Phase 3)
python run_benchmark.py --constrained outlines
```

## Project Structure

```
.
├── README.md
├── requirements.txt
├── config/
│   └── models.yaml          # Model configurations
├── tasks/
│   ├── json_generation.py   # JSON generation tasks
│   ├── schema_adherence.py  # Schema compliance tasks
│   ├── function_calling.py  # Function calling format tasks
│   └── extraction.py        # Key-value extraction tasks
├── evaluation/
│   ├── json_validator.py    # JSON validity checking
│   ├── schema_checker.py    # Schema compliance checking
│   ├── content_accuracy.py  # Value-level correctness
│   └── metrics.py           # Metric calculations
├── runners/
│   ├── base_runner.py       # Base model runner
│   └── constrained.py       # Constrained decoding runner
├── analysis/
│   └── analyze_results.py   # Result analysis and visualization
├── notebooks/               # Per-model execution notebooks
│   └── NOTEBOOK_SPEC.md     # Standardized notebook structure
├── results/                 # Benchmark results (JSON/CSV)
└── run_benchmark.py         # Main entry point
```

## Citation

```bibtex
@article{small-llm-structured-2026,
  title={Can Small LLMs Follow Instructions? A Systematic Benchmark of Open-Source Models for Production Structured Output Generation},
  author={TODO},
  journal={arXiv preprint},
  year={2026}
}
```
