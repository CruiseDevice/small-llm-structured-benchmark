# Phase 3: Semantic Evaluation Results

## The Two-Axis Metric

The central contribution of this paper is separating **structural correctness** (schema validity) from **semantic correctness** (content accuracy). Schema validity asks "is this valid JSON matching the schema?" Content accuracy asks "are the actual values correct?"

These are different questions, and CD affects them differently.

---

## Axis 1: Schema Validity Rate (Structural)

| Model | Native | Outlines | XGrammar |
|-------|--------|----------|----------|
| Llama-1B | 78.6% | **100%** | **100%** |
| Llama-3B | 78.6% | **100%** | **100%** |
| Qwen-0.6B | 92.9% | **100%** | **100%** |
| Qwen-4B | 100% | 100% | 100% |
| Phi-4-mini | 92.9% | **100%** | **100%** |

**CD eliminates all structural failures across all models.** Every model reaches 100% schema validity under both CD frameworks. The structural axis is solved.

---

## Axis 2: Content Accuracy (Semantic)

| Model | Native | Outlines | XGrammar |
|-------|--------|----------|----------|
| Llama-1B | 0.764 | 0.921 | **0.979** |
| Llama-3B | 0.770 | **0.991** | 0.984 |
| Qwen-0.6B | 0.894 | 0.921 | **0.936** |
| Qwen-4B | **0.993** | 0.992 | 0.993 |
| Phi-4-mini | 0.951 | **0.992** | 0.993 |

**CD improves semantic accuracy but does NOT flatten it to 100%.** The semantic gap persists, and it is scale-dependent:

| Model | Native → Best CD | Gap closed? |
|-------|------------------|-------------|
| Llama-1B | 0.764 → 0.979 | Mostly (but still lowest) |
| Llama-3B | 0.770 → 0.991 | Nearly fully |
| Qwen-0.6B | 0.894 → 0.936 | Partially (smallest improvement) |
| Qwen-4B | 0.993 → 0.993 | N/A (already near-perfect) |
| Phi-4-mini | 0.951 → 0.993 | Nearly fully |

---

## The `extract_receipt` Type Coercion Test

This is the cleanest case of CD providing **complete semantic rescue**:

| Model | Decoder | Schema Valid | Content Accuracy |
|-------|---------|-------------|-----------------|
| Qwen-0.6B | native | ❌ (prices as strings) | **0.417** |
| Qwen-0.6B | outlines | ✅ | **1.000** |
| Qwen-0.6B | xgrammar | ✅ | **1.000** |
| Phi-4-mini | native | ❌ (`$` prefix on prices) | **0.417** |
| Phi-4-mini | outlines | ✅ | **0.990** |
| Phi-4-mini | xgrammar | ✅ | **1.000** |

Type coercion is a **structural failure with semantic consequences**. CD fixes the type → the semantic content is automatically correct. This is the case where CD works perfectly.

---

## The `funcall_search_multi` Semantic Gap

This is the case where CD **cannot** help — the failure is not in the types but in the model's understanding of task intent:

| Model | Decoder | Schema Valid | Func Call Score | Both Calls Present? |
|-------|---------|-------------|----------------|---------------------|
| Llama-1B | native | ❌ | 0.000 | ❌ (JSON unparseable) |
| Llama-1B | outlines | ✅ | **0.200** | ❌ (only search_web) |
| Llama-1B | xgrammar | ✅ | **1.000** | ✅ |
| Llama-3B | native | ❌ | 0.000 | ❌ (JSON unparseable) |
| Llama-3B | outlines | ✅ | **1.000** | ✅ |
| Llama-3B | xgrammar | ✅ | **1.000** | ✅ |
| Qwen-0.6B | native | ✅ | **0.200** | ❌ (only search_web) |
| Qwen-0.6B | outlines | ✅ | **0.200** | ❌ (only search_web) |
| Qwen-0.6B | xgrammar | ✅ | **0.200** | ❌ (only search_web) |
| Qwen-4B | native | ✅ | **1.000** | ✅ |
| Phi-4-mini | native | ✅ | **1.000** | ✅ |

**Key observations:**

1. **Qwen-0.6B is the starkest illustration of the semantic gap.** It scores 0.200 on funcall_search_multi across ALL decoders — CD makes it schema-valid but cannot make it emit both calls. The model doesn't understand the multi-step intent, and token masking can't fix that.

2. **Llama-1B under XGrammar: structural completeness without semantic quality.** XGrammar scored 1.000 (both calls present with all params), but the email body is `"Here are the top 5 restaurants in NYC: \n- \n 1. \n 2. \n 3. \n 4. \n 5."` — the list structure is there but every restaurant name is empty. This is a **hollow semantic rescue**: XGrammar's token masking guides the model to produce structurally complete output (both calls, all required params), but the underlying content quality is still that of a 1B model. The function_call_score metric counts param presence, not content quality of param values — so this scores as 1.000 despite the hollow content. This is itself an important finding: even when CD appears to fully rescue a task by structural metrics, semantic inspection reveals the gap persists.

3. **The semantic gap is model-dependent.** Qwen-4B (4B dense) and Phi-4-mini (3.8B dense) handle this task perfectly natively. Llama-3B (3B dense) rescues it under CD. Llama-1B and Qwen-0.6B do not.

---

## `funcall_database_query` — Llama-3B's Missing `limit` Param

| Model | native | outlines | xgrammar |
|-------|--------|----------|----------|
| Llama-1B | 1.000 | 1.000 | 1.000 |
| Llama-3B | **0.875** | **0.875** | **0.875** |
| Qwen-0.6B | 1.000 | 1.000 | 1.000 |
| Qwen-4B | 1.000 | 1.000 | 1.000 |
| Phi-4-mini | 1.000 | 1.000 | 1.000 |

Llama-3B omits the `limit` parameter (3/4 expected params present → 0.875). The `limit` is embedded in the SQL query itself (`LIMIT 50`) but not passed as a separate argument. This is stable across all decoders — it's a model-level behavioral pattern, not a CD issue. CD can't add parameters the model never learned to emit.

The schema allows it because `arguments` uses `additionalProperties: true` and only `query` and `database` are `required` in the tool spec.

---

## Conclusion: The Two-Axis Story

**For the paper:**

> Constrained decoding eliminates all structural failures across all five models tested (schema validity: 78.6–92.9% → 100%). However, content accuracy — whether the generated values are semantically correct — reveals a persistent gap that CD cannot close:
>
> - **Type coercion failures** (Qwen-0.6B, Phi-4-mini on `extract_receipt`) are **fully rescuable**: CD forces numeric types, and the resulting values are semantically correct (content accuracy: 0.417 → 1.000).
> - **Instruction-semantic failures** (`funcall_search_multi`) are **CD-resistant**: Qwen-0.6B emits only one of two required function calls under all decoders (func score: 0.200 across native/outlines/xgrammar). The schema permits this (`minItems: 1`), so the output is schema-valid but semantically incomplete.
> - **The semantic gap is scale-dependent**: Larger models (Qwen-4B, Phi-4-mini) handle complex tasks natively. Llama-3B rescues most failures under CD. Llama-1B and Qwen-0.6B show persistent semantic gaps that CD cannot bridge.
>
> **Schema conformance is necessary but not sufficient for semantic correctness.** CD's reach ends exactly where schema conformance ends.

---

## Data Location

- Full semantic evaluation CSV: `results/v2/phase3/phase3_semantic_evaluation.csv`
- Raw Phase 3 outputs: `results/v2/phase3/phase3_<model>_raw_<timestamp>.json`
