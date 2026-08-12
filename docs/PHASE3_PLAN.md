# Phase 3: Constrained Decoding × Scale Interaction Plan

## Research question

> Does constrained decoding flatten the small-model scaling curve?
>
> Specifically, can a constrained 1B model match an unconstrained 3B model? Or do failures persist because they are semantic (wrong values, hallucinated fields) rather than structural, and therefore unreachable by token masking?

This question is only answerable with a controlled size ladder and shared tasks. Prior work (JSONSchemaBench) benchmarks frameworks on a fixed large-ish model; we benchmark **model scale** under a fixed constrained-decoding condition.

---

## Why this is defensible

| Work | Constrained decoding? | Controlled size ladder? | Focus |
|------|----------------------|------------------------|-------|
| JSONSchemaBench (2501.10868v3) | ✅ 6 frameworks | ❌ one 1B model, no ladder | Framework coverage & efficiency |
| STED (2512.23712v1) | ❌ | ❌ | Temperature × consistency metric on large models |
| Renze & Guven 2024 | ❌ | ❌ | Temperature × problem-solving accuracy |
| **This work** | ✅ | ✅ 0.6B→24B within families | How CD interacts with **scale** |

The novelty is not "we added constrained decoding." The novelty is **the interaction term**: constrained decoding × model scale.

---

## Decoding conditions

Run every (model, task) under three conditions:

| Condition | Decoder | How it works |
|-----------|---------|-------------|
| `native` | Unconstrained greedy (`temperature=0.0`, `do_sample=False`) | Reproduces Phase 1 baseline; no logits processor |
| `outlines` | Outlines `generate.json()` | FSM-based regex approach; wraps the HF model; manages tokenization internally |
| `xgrammar` | XGrammar `LogitsProcessor` | Compiled grammar approach; injects a logits processor into `model.generate()` |

All conditions use **greedy decoding** (`temperature=0.0`, `do_sample=False`) so results are deterministic and directly comparable to Phase 1.

`lm-format-enforcer` is dropped — two frameworks (Outlines + XGrammar) already represent fundamentally different technical approaches (regex/FSM vs compiled grammar), which is enough to claim framework-independence.

---

## Models to test

5 models from the Phase 2 subset — selected because they have **characterized failure modes** from Phase 2 (type coercion, structural misplacement, instruction-semantic), not as a subset of convenience:

| Model | Family | Expected role in analysis |
|-------|--------|---------------------------|
| Llama 3.2 1B | Llama | **Critical test**: scaling inversion under CD — semantic gap ✅ Done |
| Llama 3.2 3B | Llama | **Critical test**: does 3B close the semantic gap under CD? ✅ Done |
| Qwen3-4B | Qwen | **Perfect control** — native already 100%; measures pure CD overhead ✅ Done |
| Qwen3-0.6B | Qwen | Type-coercion rescue test (`extract_receipt` string prices) ✅ Done |
| Phi-4-mini | Phi | Formatting-preservation test (`$20.49`) ✅ Done |

Optional 6th model (MoE × CD interaction):
- **Gemma-4-E2B** — MoE architecture interaction with constrained decoding

**Future work:** extend to the full 11-model Phase-1 set for a complete CD×scale curve across all families (including Mistral-24B reference and Gemma 12B dense).

Total Phase 3 runs: 5 models × 14 tasks × 3 decoders = **210 runs** (252 with optional Gemma).

---

## Hypotheses and findings

### H1: CD rescues structural failures ✅ CONFIRMED
Both Llama models went from 78.6% → 100% schema validity under both CD frameworks.

| Model | Native | Outlines | XGrammar |
|---|---|---|---|
| Llama 3.2 1B | 78.6% (11/14) | **100%** (14/14) | **100%** (14/14) |
| Llama 3.2 3B | 78.6% (11/14) | **100%** (14/14) | **100%** (14/14) |

All previously-failing tasks rescued: `json_complex_api`, `schema_database_record`, `schema_config_file`, `funcall_search_multi`.

### H2: CD enforces schema-as-written; schemas under-express intent ⚠️ NUANCED

The original hypothesis was "CD does not rescue semantic failures." The reality is sharper:

**CD guarantees conformance to the schema as written. It cannot recover semantic content the schema never captured.** On `funcall_search_multi`, the schema says `minItems: 1` (allowing a single call) and `body: {type: string}` (allowing empty/hollow content). So:

- Outlines emitting only 1 call → **passes** (minItems=1 satisfied)
- XGrammar emitting `"1. 2. 3. 4. 5."` as email body → **passes** (valid string)

Both are schema-valid but semantically incomplete. The limitation is not in the model or the CD framework — it's in the schema's under-specification of intent.

#### The `funcall_search_multi` three-way comparison (Llama-3.2-1B)

| Decoder | What happened | Semantic quality |
|---|---|---|
| **native** | Model emitted both calls with correct fields, attempted a real email body, then degenerated into infinite empty list items (`"1. \n 2. \n 3. \n..."`) consuming the full 512-token budget. JSON left unclosed → unparseable. | Ambitious but failed mid-generation — understood task structure, failed on content |
| **outlines** | Emitted only ONE call (`search_web`). Dropped `send_email` entirely. | Minimal / incomplete — schema permits this (minItems=1) |
| **xgrammar** | Emitted both calls, but body is `"Here are the top 5 restaurants in NYC: 1. 2. 3. 4. 5."` — list structure with no restaurant names | Structurally complete, semantically hollow — schema permits this (empty string is valid) |

The native failure is **not garbage** — it is a structurally coherent response that degenerated during content generation. This is the cleanest illustration of the structural-vs-semantic split: the model understood the task perfectly and failed on content.

#### Scale-dependent semantic quality under CD

The semantic quality of CD output is itself scale-dependent:

| Model | Outlines output on `funcall_search_multi` | XGrammar output |
|---|---|---|
| **Llama-1B** | 1 call only (missing send_email) | 2 calls, body: `"1. 2. 3. 4. 5."` (empty) |
| **Llama-3B** | **2 calls** with real content: `"See the results below: [insert results]"` | **2 calls** with real content: `"Best restaurants in NYC"` |

CD eliminates structural failures equally across scales. Semantic completeness under CD is scale-dependent.

### H3: CD flattens the schema-validity curve but not the semantic curve ✅ CONFIRMED

Schema validity: both 1B and 3B reach 100% under CD.
Semantic quality: 1B produces hollow/missing content; 3B produces real content. The gap persists.

### Phi-4-mini — formatting rescue and the funcall_search_multi exception
| Decoder | Schema Valid | Avg Compile (ms) | Avg Latency (ms) | Avg tok/s | Tokens/response |
|---------|--------------|------------------|------------------|-----------|-----------------|
| native  | 92.9% (13/14) | 0.0             | 2619.9           | 34.4      | 90.8            |
| outlines| 100% (14/14) | 4863.4           | 2224.8           | 31.0      | 68.5            |
| xgrammar| 100% (14/14) | 8.4              | 2624.9           | 33.1      | 87.1            |

- **CD rescues `$`-prefix formatting**: `extract_receipt` failed natively (prices with `$` prefix: `"$4.98"`, `"$20.49"` instead of numbers). Both CD frameworks forced numeric tokens → `$` stripped, values correct → 100% schema valid. This is the same type-coercion archetype as Qwen3-0.6B, now confirmed cross-family.
- **Phi-4-mini is the `funcall_search_multi` exception**: Unlike Llama-1B/3B and Qwen-0.6B (which emit only 1 call or hollow content), Phi-4-mini emits **both calls with real content** natively AND under all CD conditions. The email body reads `"Here are the best restaurants in NYC: [List of restaurants]"` — a placeholder, but both calls are structurally present. This suggests the `funcall_search_multi` semantic gap is **not universal across all small models** — it's architecture/training-dependent.
- **Outlines compile time worst on Phi tokenizer**: peaks at 19.5s on `funcall_search_multi` (vs 13s on Qwen-0.6B, 7.5s on Llama). The Phi tokenizer's structure creates the heaviest FSM compilation cost across all 5 models tested.
- **XGrammar**: negligible overhead (~8ms compile), throughput preserved (~33 tok/s vs 34.4 native, ~4% drop).
- For the paper: *"The `$`-prefix formatting bug in Phi-4-mini is the same structural archetype as Qwen-0.6B's string-coercion — both are type-constraint failures fully rescued by CD. However, Phi-4-mini's success on `funcall_search_multi` (where Llama and Qwen-0.6B fail semantically) shows that the CD-resistant semantic gap is model-dependent, not universal."*

### Qwen3-0.6B — type-coercion rescue on the smallest model
| Decoder | Schema Valid | Avg Compile (ms) | Avg Latency (ms) | Avg tok/s | Tokens/response |
|---------|--------------|------------------|------------------|-----------|-----------------|
| native  | 92.9% (13/14) | 0.0             | 2992.7           | 31.3      | 94.6            |
| outlines| 100% (14/14) | 3031.7           | 2407.0           | 28.5      | 65.7            |
| xgrammar| 100% (14/14) | 7.0              | 2719.4           | 30.8      | 83.9            |

- **CD rescues type coercion**: `extract_receipt` failed natively (prices as strings `"4.98"`, `"20.49"` instead of numbers `4.98`, `20.49`). Both CD frameworks forced numeric tokens → 100% schema valid.
- **Semantic quality preserved on rescued task**: CD output on `extract_receipt` is not just schema-valid but semantically correct — same store name, same item names, same prices (now as numbers), same total. This is a **full rescue**, not a hollow one.
- **`funcall_search_multi` semantic gap confirmed again**: All three decoders emit only 1 call (`search_web`), missing `send_email` entirely. The schema permits this (`minItems: 1`). This is the same CD-resistant semantic failure seen in Llama-1B.
- **Outlines compile time on Qwen tokenizer**: peaks at 13s on `funcall_search_multi` and 6.4s on other function-calling tasks — significantly worse than Llama's 7.5s peak. The Qwen tokenizer's larger vocabulary likely inflates FSM compilation cost.
- **XGrammar**: negligible overhead (~7ms compile), throughput preserved (~30.8 vs 31.3 tok/s, ~2% drop).
- For the paper: *"Type coercion failures in small models are fully structural and fully CD-rescuable — CD forces numeric token paths, producing semantically correct output. This is the cleanest case of CD providing complete rescue, not just structural conformance."*

### Qwen3-4B — pure CD overhead on a model that doesn't need it
| Decoder | Schema Valid | Avg Compile (ms) | Avg Latency (ms) | Avg tok/s | Tokens/response |
|---------|--------------|------------------|------------------|-----------|-----------------|
| native  | 100%         | 0.0              | 4624.4           | 18.1      | 84.1            |
| outlines| 100%         | 2662.0           | 4161.0           | 17.8      | 72.0            |
| xgrammar| 100%         | 5.5              | 4303.0           | 19.6      | 84.1            |

- CD has **zero structural benefit** on this model — schema validity stays at 100% across all decoders.
- **Outlines** adds ~2.7s average compile time (peaks at 10.2s on `funcall_search_multi` and 5.5s on `funcall_database_query`), but generates fewer tokens (~14% less), which partially offsets the compile cost in end-to-end wall time.
- **XGrammar** adds negligible compile overhead (~5.5ms) and actually produces slightly higher throughput (19.6 tok/s vs 18.1 tok/s native). The latency bump relative to native is likely compilation warmup + longer decoding path, but throughput is preserved.
- For the paper: CD overhead on already-perfect models is dominated by framework compilation time, not generation throughput. XGrammar is essentially free; Outlines is costlier but not prohibitive.

---

## Integration into `run_single_task`

The cleanest approach is to extend the runner, not rewrite it:

```python
def run_single_task(task, run_num=1, temperature=0.0, decoder="native"):
    """
    Run a single benchmark task.
    
    Args:
        task: task dict from task_definitions
        run_num: sample index within this condition
        temperature: sampling temperature (0.0 = greedy)
        decoder: one of "native", "outlines", "xgrammar", "lmfe"
    """
    ...
    if decoder == "native":
        outputs = model.generate(**inputs, **generate_kwargs)
    elif decoder == "outlines":
        # Use outlines.generate.json(model, tokenizer, schema=task["schema"])
        # or outlines.generate.format(model, tokenizer, pydantic_model=...)
    elif decoder == "xgrammar":
        # Use xgrammar.GrammarCompiler + xgrammar.LogitsProcessor
    elif decoder == "lmfe":
        # Use lmformatenforcer.JsonSchemaParser + generate kwargs
    ...
    result = {
        ...
        "decoder": decoder,
        ...
    }
```

Keep the existing validation logic unchanged. CD frameworks should guarantee schema validity, but we still measure it independently as a sanity check.

---

## Result tables and figures

### Main result table
Per-model schema-valid rate across decoders, plus absolute and relative gain.

### Scaling-curve figure
Plot schema-valid rate vs. active parameters for:
- native only
- best CD decoder per model
- showing whether CD narrows the gap between small and large models

### Per-task rescue matrix
Heatmap: rows = tasks, columns = (model, decoder), color = schema-valid rate. Reveals which tasks are CD-rescuable vs. semantic-failure tasks.

### Overhead table
Compile time, TTFT, TPOT, total latency per decoder, averaged across models.

---

## Dependencies

```bash
pip install outlines xgrammar
```

**Install order (important):**
1. `pip install xgrammar` (smaller dependency footprint, less likely to conflict)
2. `pip install outlines` (larger dependency set — may pin specific versions of pydantic, transformers)

Check compatibility after install:
```python
import outlines; print(f"outlines {outlines.__version__}")
import xgrammar; print(f"xgrammar {xgrammar.__version__}")
import transformers; print(f"transformers {transformers.__version__}")
import torch; print(f"torch {torch.__version__}")
```

If Outlines conflicts with your transformers version, try:
```bash
pip install outlines --no-deps  # then manually install missing deps
```

**Integration is in NOTEBOOK_SPEC.md Cell 10** — the code is a drop-in extension of the existing `run_single_task` pattern.

---

### Execution status

#### Completed (5/5 models) ✅ PHASE 3 COMPLETE
- ✅ **Llama 3.2 1B** — 78.6% → 100% under both frameworks. Semantic gap on `funcall_search_multi` (1B produces hollow content under CD)
- ✅ **Llama 3.2 3B** — 78.6% → 100% under both frameworks. Semantic quality better than 1B (both calls with real content)
- ✅ **Qwen3-4B** — Pure overhead control. Native already 100%; CD adds no structural benefit. XGrammar overhead negligible (~5.5ms compile). Outlines overhead significant (~2.7s avg compile, up to 10.2s peak)
- ✅ **Qwen3-0.6B** — Type-coercion rescue. Native 92.9% → 100% under both frameworks. CD rescues `extract_receipt` string→number coercion. Outlines compile time peaks at 13s on `funcall_search_multi` (Qwen tokenizer overhead).
- ✅ **Phi-4-mini** — Formatting rescue. Native 92.9% → 100% under both frameworks. CD rescues `extract_receipt` `$`-prefix stripping. Notably, Phi-4-mini handles `funcall_search_multi` correctly natively AND under CD (only model besides Qwen3-4B to do so). Outlines compile time peaks at 19.5s on `funcall_search_multi` (worst across all models).

#### Optional (not run)
- **Gemma-4-E2B** — MoE interaction with CD

#### Post-experiment analysis
After all Phase 3 runs: compute `content_accuracy` and `function_call_score` on saved raw JSON outputs using `evaluation/evaluator.py`. This separates structural rescue (schema-valid) from semantic rescue (content-correct) — the key two-axis metric for the paper.

---

## Relationship to Phase 2

Phase 2 (temperature probe) answers: *Are Phase-1 failures stable under sampling?*
- Answer: Yes. Only Llama-1B shows meaningful degradation (−9.5pp). Most failures are systematic across temperatures.

Phase 3 answers: *Can constrained decoding fix the systematic failures we found?*
- Answer (schema): Yes — CD raises all models to 100% schema validity.
- Answer (semantic): Partially — CD enforces schema-as-written, but schemas under-express intent. Semantic quality under CD is scale-dependent.

Together they form a coherent story:
1. Here are the baseline failures (Phase 1).
2. They are systematic, not sampling artifacts (Phase 2).
3. CD eliminates structural failures but reveals that schema conformance ≠ semantic correctness; the gap is scale-dependent (Phase 3 — main contribution).
