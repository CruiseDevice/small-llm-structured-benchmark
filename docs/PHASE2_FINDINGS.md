# Phase 2: Temperature Robustness Probe — Findings

## Overview

Phase 2 tests whether small-model structured-output failures are **systematic** (stable across decoding conditions) or **stochastic** (artifacts of temperature sampling). Six models spanning four families and four parameter scales were evaluated on 14 structured-output tasks × 3 temperatures × 3 samples per condition (756 total evaluations).

**Result:** Failures are overwhelmingly systematic. Only one model (Llama-3.2-1B) exhibits true temperature-induced reliability collapse. The rest are stable or improve under sampling.

## Experimental Design

- **Temperatures:** [0.0, 0.3, 0.7]
- **Samples per condition:** 3
- **Tasks:** 14 (4 categories: JSON generation, schema adherence, function calling, extraction)
- **Decoding:** `do_sample = (temperature > 0.0)`, `top_p = 1.0`, `top_k = None`
- **Greedy baseline** at T=0.0 is deterministic (repeated runs produce identical output)

## Results: Schema Validity by Temperature

| Model | Params | Family | T=0.0 | T=0.3 | T=0.7 | Pattern |
|---|---|---|---|---|---|---|
| Qwen3-4B | 4B dense | Qwen | 100.0% | 100.0% | 100.0% | **Perfect control** — zero failures |
| Gemma-4-E2B | ~5B / 2B active | Google MoE | 100.0% | 97.6% | 97.6% | **Near-perfect** — 2 enum violations |
| Qwen3-0.6B | 0.6B | Qwen | 92.9% | 92.9% | 97.6% | **Stable / improves** with T |
| Phi-4-mini | 3.8B | Microsoft | 92.9% | 92.9% | 88.1% | **Stable** — one formatting bug |
| Llama-3.2-3B | 3B | Meta | 78.6% | 76.2% | 83.3% | **Improves** under sampling |
| Llama-3.2-1B | 1B | Meta | 78.6% | 78.6% | 69.0% | **Degrades** — only true collapse |

## Key Findings

### 1. Temperature does not create new failure types

Qwen3-4B and Gemma-4-E2B — the two control models — show zero or near-zero failures at all temperatures. This proves the failures observed in weaker models are **latent weaknesses exposed by the task**, not artifacts of stochastic decoding.

### 2. The Llama "scaling inversion" was a greedy-decoding artifact

In Phase 1 (greedy, single-shot), Llama-3.2-1B and Llama-3.2-3B both scored ~79%, suggesting no benefit from 1B→3B scaling. Phase 2 reveals this was misleading:

- **1B degrades** under sampling (78.6% → 69.0%)
- **3B improves** under sampling (78.6% → 83.3%)

Scale does matter. The Phase 1 tie was a coincidence of greedy decoding.

### 3. Failure modes are heterogeneous

Three distinct failure archetypes emerge:

| Archetype | Example | Affected models | CD rescue prediction | Phase 3 result |
|---|---|---|---|---|
| **Type coercion** | `"35"` instead of `35` for numeric fields; `"$20.49"` for prices | Qwen3-0.6B, Phi-4-mini, Llama-3.2-1B | **High** — CD enforces numeric token paths | ✅ Confirmed (Llama 1B/3B) |
| **Structural misplacement** | Missing required `metadata` field; hallucinated schema keywords (`maxItems`, `additionalProperties`) as data | Llama-3.2-1B, Llama-3.2-3B | **High** — CD forces correct structure | ✅ Confirmed (both rescued to 100%) |
| **Instruction-semantic** | Model attempts multi-call response but degenerates; or emits semicolon-separated objects instead of JSON array | Llama-3.2-1B, Llama-3.2-3B, (Phi-4-mini at T=0.7) | **Partial** — CD can force array syntax, but schema under-specifies intent (minItems=1 allows single call; string type allows hollow content) | ⚠️ CD produces schema-valid but semantically incomplete output |

### 4. MoE achieves near-perfect with ~2B active params

Gemma-4-E2B (MoE, ~2B active parameters) matches or exceeds Qwen3-4B (4B dense). Its only failures are two instances of using `OPTIONS` as an HTTP method — a plausible domain value not in the schema enum. This confirms that **Mixture-of-Experts architecture decouples total parameter count from active-parameter capability** for structured output.

### 5. `funcall_search_multi` is the hardest task across all models

This task requires the model to emit a JSON array of two function-call objects. Llama models at all temperatures produce semicolon-separated objects (`{...}; {...}`) instead of a JSON array. Phi-4-mini succeeds at T≤0.3 but breaks at T=0.7 (uses Python `+` string concatenation inside JSON). Only Qwen3-4B and Gemma-4-E2B handle it perfectly.

## Per-Model Failure Details

### Qwen3-0.6B (low-end control)
- `extract_receipt`: type coercion — prices as strings (`"20.49"`) instead of numbers
- `json_complex_api`: type coercion on `per_page` field (`"3"` vs `3`)
- Both failures improve at higher T; T=0.7 actually scores 97.6%

### Qwen3-4B (high-end control)
- **Zero failures.** 126/126 schema-valid across all conditions.

### Gemma-4-E2B (MoE control)
- `schema_config_file` at T=0.3 and T=0.7: uses `OPTIONS` as HTTP method (valid in practice, not in schema enum)
- T=0.0: 42/42 perfect

### Llama-3.2-1B (true collapse)
- Persistent failures (all temperatures):
  - `json_complex_api`: missing top-level `metadata` (0/9)
  - `schema_database_record`: hallucinates schema keywords as data (0/9)
  - `funcall_search_multi`: emits semicolon-separated objects, not array (0/9)
- Temperature-induced failures (T=0.7 only):
  - `json_simple_person`: age `"35"` instead of `35`
  - `schema_config_file`: empty string violates enum
  - `extract_api_log`: output becomes array, scale errors

### Llama-3.2-3B (improver)
- `funcall_search_multi`: identical failure to 1B (0/9 across all temperatures)
- `schema_database_record`: fails at T=0.0/T=0.3 (pattern mismatch on ID), but **passes at T=0.7**
- `schema_config_file`: fails at T≤0.3 (adds `"type": "object"` as data), **passes at T=0.7**
- `json_complex_api`: passes at T=0.0, partial failure at T>0.0 (nests metadata incorrectly)

### Phi-4-mini (stable, one bug)
- `extract_receipt`: preserves `$` prefix in prices (`"$20.49"`) — systematic, all temperatures
- `funcall_search_multi` at T=0.7: uses Python `+` operator inside JSON string values

## Implications for Phase 3 (Constrained Decoding) — Updated with Phase 3 Results

Phase 2 established which failures are **structural** (CD-addressable) vs **semantic** (CD-resistant). Phase 3 confirmed the split:

1. **CD fully rescues type coercions and structural misplacements** — all Llama native failures eliminated under both Outlines and XGrammar (78.6% → 100%)
2. **CD enforces schema-as-written, but schemas under-express intent** — on `funcall_search_multi`, the schema permits `minItems=1` and unconstrained string bodies, so CD produces schema-valid but semantically hollow output
3. **Semantic quality under CD is scale-dependent** — Llama-1B under CD emits missing/empty content; Llama-3B under CD emits complete content with real values
4. **CD has zero structural benefit on already-perfect models** (Qwen3-4B native = 100% — pending Phase 3 confirmation)

The Phase 3 finding: **Constrained decoding flattens the schema-validity curve across scales, but the semantic-quality gap between scales persists. Schema conformance is necessary but not sufficient for semantic correctness.**

## Data Location

All Phase 2 raw data archived in `results/v2/phase2/`:
- CSV summaries: `phase2_<model>.csv`
- Raw JSON (with full responses): `phase2_<model>_raw_<timestamp>.json`
