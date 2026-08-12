# Paper Writing Guide: Section-by-Section

## Paper metadata

- **Title**: "Constrained Decoding Eliminates Structural Failures in Small LLMs but Reveals a Scale-Dependent Semantic Gap"
- **Short title**: "Small LLM Structured Output: Structure vs Semantics under CD"
- **Format**: 8-page short paper (ACL/EMNLP workshop)
- **Target venue**: EMNLP/ACL workshop (find one with structured output / LLM evaluation focus)
- **arXiv first**: establish priority before workshop deadline

**Backup title option**: "Can Small LLMs Follow Instructions? A Systematic Benchmark of CD × Scale Interaction for Structured Output Generation"

---

## ABSTRACT (write last, ~150 words)

Formula: [Context] + [Problem] + [Method] + [Key finding] + [Implication]

Draft:
> Small open-source LLMs (0.6B–4B) are increasingly deployed for structured output generation (JSON, function calling), yet little is known about how constrained decoding (CD) interacts with model scale in this regime. We benchmark five models from three families across 14 structured-output tasks under three decoding conditions (native, Outlines, XGrammar). We find that CD eliminates all structural failures across all models (schema validity: 78.6–92.9% → 100%), but content accuracy reveals a persistent semantic gap that is scale-dependent: type coercion failures are fully CD-rescuable, while instruction-semantic failures (e.g., multi-step function calling) remain CD-resistant. Our two-axis evaluation—separating structural correctness from semantic correctness—shows that schema conformance is necessary but not sufficient for semantic correctness, and that CD's reach ends exactly where schema conformance ends.

---

## 1. INTRODUCTION (~1 page)

### Opening hook (1 paragraph)
- Small LLMs (0.6B–4B) are deployed in production for structured output: API responses, function calling, data extraction
- They run on edge devices and consumer GPUs — cost matters
- Constrained decoding (CD) frameworks promise to fix their formatting failures
- But does CD actually make their OUTPUT correct, or just well-FORMATTED?

### Problem statement (1 paragraph)
- Existing benchmarks (JSONSchemaBench) evaluate CD frameworks on a single large model
- No work studies how CD interacts with MODEL SCALE in the small-model regime
- The question matters: if CD rescues a 1B model, you don't need a 4B model

### Research question (1 paragraph, the thesis)
> Does constrained decoding flatten the small-model scaling curve for structured output? Specifically: can a constrained 1B model match an unconstrained 3B model? Or do failures persist because they are semantic rather than structural, and therefore unreachable by token masking?

### Contributions (bullet list, 3-4 items)
1. A controlled size-ladder benchmark (5 models, 3 families) × 14 tasks × 3 decoding conditions
2. A two-axis evaluation metric separating structural correctness (schema validity) from semantic correctness (content accuracy)
3. The finding that CD eliminates structural failures universally but the semantic gap is scale-dependent
4. Identification of CD-rescuable vs CD-resistant failure archetypes

### Paper roadmap (1 sentence)
- Section 2 surveys related work, Section 3 describes methodology, Section 4 presents results, Section 5 discusses limitations and implications.

---

## 2. RELATED WORK (~0.75 page)

### 2.1 Constrained Decoding Frameworks (1 paragraph)
- **Outlines**: FSM-based approach, compiles JSON schema to regular expression, masks tokens at each step (Willard & Bethard, 2023)
- **XGrammar**: Compiled grammar approach, efficient bitmask generation (Dong et al., 2024)
- **lm-format-enforcer**: regex-based (briefly mentioned, we dropped it since Outlines+XGrammar represent different technical approaches)

### 2.2 Structured Output Benchmarks (1-2 paragraphs)
- **JSONSchemaBench** (Garg et al., 2025): benchmarks 6 CD frameworks on a single 1B model — no size ladder, focuses on framework efficiency, not CD × scale interaction. KEY CONTRAST.
- **STED** framework: temperature × consistency on large models — no CD, no small models
- **Renze & Guven (2024)**: temperature × problem-solving accuracy — no structured output focus

### 2.3 Small Model Evaluation (1 paragraph)
- Growing interest in small model deployment (Phi-4, Gemma, Qwen3 families)
- Most evaluations focus on general benchmarks (MMLU, etc.), not production structured output
- Gap: no systematic study of how CD interacts with model scale for structured output

### The novelty statement (embed in 2.2 or as standalone paragraph)
| Work | CD? | Size ladder? | Focus |
|------|-----|-------------|-------|
| JSONSchemaBench | ✅ | ❌ (1 model) | Framework efficiency |
| STED | ❌ | ❌ | Temperature × consistency |
| Renze & Guven | ❌ | ❌ | Temperature × accuracy |
| **This work** | ✅ | ✅ (0.6B→4B) | CD × scale interaction |

---

## 3. METHODOLOGY (~1.5 pages)

### 3.1 Models (0.5 page, with table)
| Model | Family | Parameters | Type | Role in study |
|-------|--------|-----------|------|---------------|
| Qwen3-0.6B | Qwen | 0.6B dense | Dense | Smallest; type coercion failures |
| Llama-3.2-1B | Meta | 1.0B dense | Dense | Structural + semantic failures |
| Llama-3.2-3B | Meta | 3.0B dense | Dense | Scale comparison within Llama |
| Phi-4-mini | Microsoft | 3.8B dense | Dense | Formatting failures; cross-family |
| Qwen3-4B | Qwen | 4.0B dense | Dense | Perfect control (native 100%) |

- Rationale: Phase 2 subset with characterized failure modes (not convenience sample)
- All run in bfloat16 on RTX 4090
- Greedy decoding (temperature=0.0, do_sample=False) for determinism

### 3.2 Tasks (0.5 page, with table)
| Category | Tasks | Difficulty range |
|----------|-------|-----------------|
| JSON generation | 5 (person, product, nested, array, complex API) | easy → hard |
| Schema adherence | 3 (weather, database record, config file) | easy → hard |
| Function calling | 3 (single call, multi-call, database query) | easy → hard |
| Extraction | 3 (business card, receipt, API log) | easy → hard |

- 14 tasks total, designed to span difficulty and failure types
- Each task has: prompt, JSON schema, and (for extraction/function-calling) expected values for content accuracy

### 3.3 Decoding Conditions (0.25 page)
| Condition | Decoder | Description |
|-----------|---------|-------------|
| native | Unconstrained greedy | Baseline; no logits processor |
| outlines | Outlines v1 Generator | FSM-based regex; wraps HF model |
| xgrammar | XGrammar LogitsProcessor | Compiled grammar; logits processor |

- All conditions use greedy decoding (temperature=0.0)
- lm-format-enforcer dropped (Outlines + XGrammar represent fundamentally different approaches)

### 3.4 Evaluation Metrics (0.25 page — the two-axis contribution)
**Axis 1 — Structural correctness:**
- JSON validity: can the output be parsed as JSON?
- Schema validity: does the parsed output validate against the JSON schema? (using `jsonschema` Draft 2020-12)

**Axis 2 — Semantic correctness:**
- Content accuracy: for extraction tasks, how many field values match expected? (0.0–1.0)
- Function call score: for function calling, are the correct functions selected (50%) and required parameters present (50%)? (0.0–1.0)

The separation of these two axes is itself a contribution — prior work reports only schema validity.

---

## 4. RESULTS (~2.5 pages — the heart of the paper)

### 4.1 Baseline Failures Are Systematic (~0.5 page)
**Data source: Phase 1 + Phase 2**

- Phase 1 establishes baseline schema validity: Qwen-4B 100%, Qwen-0.6B 93%, Llama 1B/3B 79%
- Phase 2 temperature probe (3 temps × 3 samples) confirms failures are deterministic under greedy decoding
- Three failure archetypes identified:

| Archetype | Example | Models affected |
|-----------|---------|----------------|
| Type coercion | `"4.98"` instead of `4.98` | Qwen-0.6B, Phi-4-mini |
| Structural misplacement | Missing `metadata` field | Llama-1B/3B |
| Instruction-semantic | Missing function call | Llama-1B/3B, Qwen-0.6B |

**Key point for paper**: these archetypes predict CD-rescuability. Type coercion → rescuable. Instruction-semantic → resistant.

### 4.2 CD Eliminates Structural Failures (~0.75 page)
**Data source: Phase 3 schema validity results**

**Figure 1**: Scaling curve — schema validity vs active parameters
- X-axis: model size (log scale)
- Y-axis: schema validity %
- Three lines: native (dipping curve), outlines (flat at 100%), xgrammar (flat at 100%)
- Caption: "CD flattens the structural scaling curve to 100% across all models"

**Table**: Schema validity by model × decoder
| Model | Native | Outlines | XGrammar |
|-------|--------|----------|----------|
| Llama-1B | 78.6% | 100% | 100% |
| Llama-3B | 78.6% | 100% | 100% |
| Qwen-0.6B | 92.9% | 100% | 100% |
| Qwen-4B | 100% | 100% | 100% |
| Phi-4-mini | 92.9% | 100% | 100% |

**CD overhead paragraph**: XGrammar adds negligible overhead (~4-8ms compile, ~2-4% throughput drop). Outlines adds significant per-schema compilation cost (~1.5-5s avg, up to 19.5s peak on complex schemas with Phi tokenizer).

### 4.3 The Semantic Gap Persists (~1.25 page — THE key section)
**Data source: Phase 3 semantic evaluation**

**Figure 2**: Scaling curve — content accuracy vs active parameters
- Same axes as Figure 1 but Y = content accuracy
- Native line dips; CD lines improve but do NOT flatten to 1.0
- Caption: "CD improves content accuracy but the semantic gap persists and is scale-dependent"

**Table**: Content accuracy by model × decoder
| Model | Native | Outlines | XGrammar |
|-------|--------|----------|----------|
| Llama-1B | 0.764 | 0.921 | 0.979 |
| Llama-3B | 0.770 | 0.991 | 0.984 |
| Qwen-0.6B | 0.894 | 0.921 | 0.936 |
| Qwen-4B | 0.993 | 0.992 | 0.993 |
| Phi-4-mini | 0.951 | 0.992 | 0.993 |

**Subsection: Type coercion is fully rescuable** (~0.4 page)
- `extract_receipt` case study
- Qwen-0.6B: 0.417 → 1.000 (native → CD)
- Phi-4-mini: 0.417 → 1.000 (`$` prefix stripped)
- The structural fix (force numeric tokens) automatically produces semantically correct values
- This is the cleanest case of CD working perfectly

**Subsection: Instruction-semantic failures are CD-resistant** (~0.4 page)
- `funcall_search_multi` case study — the multi-function-call task
- Qwen-0.6B: scores 0.200 across ALL decoders (emits only 1 of 2 calls)
- The schema permits this (`minItems: 1`), so CD produces schema-valid but semantically incomplete output
- Token masking cannot inject task understanding

**Subsection: The "hollow rescue" phenomenon** (~0.2 page)
- Llama-1B under XGrammar: both calls present, all params present → func_score = 1.000
- But email body content is `"1. 2. 3. 4. 5."` — no actual restaurant names
- Structural metrics hide this gap; only semantic inspection reveals it
- Lesson: even param-level metrics can overcount semantic rescue

**Figure 3** (if space): Per-task heatmap showing which tasks are CD-rescuable vs CD-resistant

---

## 5. DISCUSSION (~0.5 page)

### Limitations
- 5 models (all dense; no MoE tested under CD — noted as future work)
- Synthetic task set (14 hand-designed tasks; real-world schema evaluation is future work)
- Single-run per condition (justified by greedy determinism, but limited statistical power)
- Content accuracy metric is coarse (field-level match, not semantic similarity)

### Implications for practitioners
1. If your failure is type coercion → use XGrammar (near-zero overhead, complete rescue)
2. If your failure is instruction-semantic → CD won't help; you need a bigger model or better prompting
3. The cheapest path to reliable structured output: XGrammar + a 3-4B model (Qwen-4B, Phi-4-mini)
4. Don't rely on schema validity alone as your success metric — measure content accuracy

### Implications for CD framework designers
- The schema-as-written is the ceiling of CD's power. Schemas that under-express intent (e.g., `minItems: 1` when 2 calls are needed) create CD-resistant semantic failures
- Richer constraint languages could help (e.g., semantic constraints, not just structural ones)

---

## 6. CONCLUSION (~0.25 page)

Restate: CD eliminates structural failures across all tested small LLMs, but semantic correctness depends on the failure type and model scale. Schema conformance is necessary but not sufficient.

Future work: extend to full 11-model set (including MoE), real-world schemas, and richer semantic evaluation (LLM-as-judge for content quality).

---

## Figures checklist

- [ ] Figure 1: Schema validity scaling curve (native vs outlines vs xgrammar)
- [ ] Figure 2: Content accuracy scaling curve (native vs outlines vs xgrammar)
- [ ] Figure 3: Per-task rescue heatmap (optional, if space)
- [ ] Figure 4: CD overhead comparison (optional, if space)

## Tables checklist

- [ ] Table 1: Models (5 models, family, params, role)
- [ ] Table 2: Tasks (14 tasks, category, difficulty)
- [ ] Table 3: Schema validity × model × decoder
- [ ] Table 4: Content accuracy × model × decoder
- [ ] Table 5: CD overhead (compile time, throughput)

## References to find (~15-20)

Must cite:
- [ ] JSONSchemaBench (Garg et al., 2025) — arXiv 2501.10868
- [ ] Outlines (Willard & Bethard, 2023)
- [ ] XGrammar (Dong et al., 2024)
- [ ] STED framework
- [ ] Renze & Guven (2024) — temperature
- [ ] JSON Schema specification (Draft 2020-12)
- [ ] Qwen3 technical report
- [ ] Llama 3.2 technical report
- [ ] Phi-4 technical report
- [ ] jsonschema Python library
- [ ] HuggingFace transformers

---

## Writing order (recommended)

1. **Section 3 (Methodology)** — easiest, you're describing what you built
2. **Section 4 (Results)** — you have all the data, just describe it
3. **Section 2 (Related Work)** — requires literature search
4. **Section 1 (Introduction)** — needs to frame the whole paper
5. **Section 5 (Discussion)** — needs results to be done first
6. **Section 6 (Conclusion)** — one paragraph
7. **Abstract** — write last, distill the best version
