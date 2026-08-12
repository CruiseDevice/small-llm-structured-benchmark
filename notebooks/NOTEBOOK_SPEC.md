# Notebook Specification v2
# Standardized structure for every model benchmark notebook
# Each model gets its own notebook following this exact structure.

## File Naming Convention
```
notebooks/{model_name}.ipynb
```
Examples: `qwen3-0.6b.ipynb`, `llama-3.2-1b.ipynb`, `gemma-4-e2b.ipynb`

---

## Cell Structure (Every Notebook Must Have These Cells In This Order)

### Cell 1: Metadata (Markdown)
```markdown
# {Model Name} - Structured Output Benchmark v2
- **Model**: {HuggingFace ID}
- **Parameters**: {total}B ({dense or MoE with X active})
- **Hardware**: {GPU used, e.g., RTX 4090 / RTX 6000 Ada}
- **Phase 1**: 14 tasks × 1 greedy sample (temperature = 0.0)
- **Phase 2** (probe): 14 tasks × 3 temperatures × 3 stochastic samples (only for failing/control models)
- **Phase 3**: 14 tasks × 3 decoding conditions (native, Outlines, XGrammar) at greedy decoding
- **Special handling**: {any model-specific notes}
```

### Cell 2: Setup
```python
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import torch
import json
import time
import re
from datetime import datetime

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
```

### Cell 3: Load Model
```python
from transformers import AutoTokenizer, AutoModelForCausalLM  # or AutoProcessor for Gemma

MODEL_NAME = "{HuggingFace ID}"

# Load tokenizer/processor
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
# OR for Gemma:
# processor = AutoProcessor.from_pretrained(MODEL_NAME)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

print(f"Model: {MODEL_NAME}")
print(f"Device: {model.device}")
print(f"Dtype: {model.dtype}")
if torch.cuda.is_available():
    print(f"GPU memory used: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
```

### Cell 4: Task Definitions
Copy the ENTIRE content of `tasks/task_definitions.py` inline.
This makes the notebook self-contained — no imports from external files.

```python
# (paste all task definitions here — SIMPLE_JSON_TASKS, SCHEMA_ADHERENCE_TASKS, etc.)
# Use the SYSTEM_PROMPTS["structured"] from the definitions
```

### Cell 5: Helper Functions
```python
# --- Chat template formatter ---
def format_messages(messages):
    """Format messages using the model's chat template.
    Override for model-specific behavior."""
    # Default (most models):
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    # For Gemma 4:
    # return processor.apply_chat_template(
    #     messages, tokenize=False,
    #     add_generation_prompt=True,
    #     enable_thinking=False,
    # )
    # For Qwen (needs /no_think):
    # messages[-1]["content"] += " /no_think"
    # return tokenizer.apply_chat_template(...)

# --- JSON extractor ---
def extract_json(raw):
    """Extract JSON from model output, handling markdown fences and extra text."""
    text = raw.strip()
    
    # 1. Direct parse
    try:
        return json.loads(text)
    except:
        pass
    
    # 2. Strip markdown fences (FIXED regex)
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # 3. Find JSON boundaries
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        s = text.find(start_char)
        e = text.rfind(end_char)
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e+1])
            except:
                pass
    return None

# --- Model-specific generate kwargs ---
BASE_GENERATE_KWARGS = {
    "max_new_tokens": 512,
}
# Add model-specific kwargs:
# For Llama: BASE_GENERATE_KWARGS["pad_token_id"] = 128001
# For Mistral: BASE_GENERATE_KWARGS["pad_token_id"] = 2

# --- Tokenizer/processor reference ---
# Set this to whichever you loaded
tok = tokenizer  # or tok = processor for Gemma
```

### Cell 6: Single Task Runner
```python
def run_single_task(task, run_num=1, temperature=0.0):
    """
    Run a single benchmark task. Returns result dict.
    
    Args:
        task: task dict from task_definitions
        run_num: sample index within this (task, temperature) condition
        temperature: sampling temperature (0.0 = greedy deterministic)
    """
    
    # Build messages
    user_content = task["prompt"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["structured"]},
        {"role": "user", "content": user_content},
    ]
    
    # Format with chat template
    text = format_messages(messages)
    
    # Tokenize
    inputs = tok(text=text, return_tensors="pt").to("cuda")
    
    # === CRITICAL: Calculate input_len AFTER tokenizing THIS task ===
    input_len = inputs["input_ids"].shape[1]
    
    # Configure generation kwargs for this temperature
    generate_kwargs = dict(BASE_GENERATE_KWARGS)
    generate_kwargs["do_sample"] = (temperature > 0.0)
    generate_kwargs["temperature"] = temperature
    if temperature > 0.0:
        # Keep deterministic helpers disabled when sampling
        generate_kwargs["top_p"] = 1.0
        generate_kwargs["top_k"] = None  # let temperature govern sampling
    
    # Generate
    start = time.time()
    outputs = model.generate(**inputs, **generate_kwargs)
    elapsed = (time.time() - start) * 1000
    
    # Decode ONLY the generated tokens
    response = tok.decode(outputs[0][input_len:], skip_special_tokens=True)
    num_tokens = outputs.shape[1] - input_len
    
    # Validation
    json_valid = False
    schema_valid = False
    parsed = None
    error_msg = None
    
    try:
        parsed = extract_json(response)
        if parsed is not None:
            json_valid = True
        else:
            error_msg = "Could not extract valid JSON"
    except Exception as e:
        error_msg = f"JSON parse error: {e}"
    
    if json_valid:
        try:
            import jsonschema
            jsonschema.validate(instance=parsed, schema=task["schema"])
            schema_valid = True
        except ImportError:
            # Fallback: check required fields
            required = task["schema"].get("required", [])
            if isinstance(parsed, dict):
                missing = [f for f in required if f not in parsed]
                if missing:
                    schema_valid = False
                    error_msg = f"Missing required fields: {missing}"
                else:
                    schema_valid = True
            else:
                schema_valid = True
        except Exception as e:
            schema_valid = False
            error_msg = f"Schema validation: {str(e)[:100]}"
    
    tokens_per_sec = round(num_tokens / (elapsed / 1000), 1) if elapsed > 0 else 0
    
    result = {
        "run": run_num,
        "temperature": temperature,
        "task_id": task["id"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "latency_ms": round(elapsed, 1),
        "tokens_generated": num_tokens,
        "tokens_per_sec": tokens_per_sec,
        "response_raw": response,
        "response_parsed": parsed,
        "error": error_msg,
    }
    
    # Print inline
    status = "✓" if schema_valid else ("~" if json_valid else "✗")
    print(f"  {status} {task['id']:<25} T={temperature:<4} JSON:{json_valid}  Schema:{schema_valid}  {elapsed:.0f}ms  {tokens_per_sec}tok/s")
    if error_msg:
        print(f"    Error: {error_msg[:80]}")
    
    return result
```

### Cell 7: Phase 1 — Single Run (14 tasks × 1 run)
```python
# ============================================================
# PHASE 1: Single Run (14 tasks × 1 run at greedy decoding)
# ============================================================

all_tasks = get_all_tasks()
phase1_results = []

print(f"PHASE 1: {MODEL_NAME} — {len(all_tasks)} tasks × 1 run")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 70)

for task in all_tasks:
    result = run_single_task(task, run_num=1, temperature=0.0)
    result["phase"] = 1
    result["model"] = MODEL_NAME
    phase1_results.append(result)

# Summary
json_pass = sum(1 for r in phase1_results if r["json_valid"])
schema_pass = sum(1 for r in phase1_results if r["schema_valid"])
print(f"\n{'='*70}")
print(f"PHASE 1 SUMMARY: {MODEL_NAME}")
print(f"  JSON Parse:   {json_pass}/{len(all_tasks)} ({100*json_pass/len(all_tasks):.0f}%)")
print(f"  Schema Valid: {schema_pass}/{len(all_tasks)} ({100*schema_pass/len(all_tasks):.0f}%)")
print(f"  Avg Latency:  {sum(r['latency_ms'] for r in phase1_results)/len(phase1_results):.0f}ms")
print(f"  Avg Speed:    {sum(r['tokens_per_sec'] for r in phase1_results)/len(phase1_results):.1f} tok/s")
print(f"Finished: {datetime.now().isoformat()}")
```

### Cell 8: Phase 2 — Temperature Robustness Probe (14 tasks × 3 temperatures × 3 runs)
```python
# ============================================================
# PHASE 2: Temperature Robustness Probe
#
# Goal: Determine whether Phase-1 failures are deterministic (systematic) or
# sampling-induced (stochastic). This is a SUPPORTING experiment, not the
# main contribution. Run only on:
#   - Models with Phase-1 failures that matter (Llama 1B/3B, Qwen 0.6B, Phi-4-mini)
#   - 1-2 control models that hit 100% schema validity (Qwen 4B, Gemma E2B)
#
# If the probe reveals surprising small-model collapse under sampling, expand
# to the full 11-model sweep. Otherwise, this section answers the robustness
# question cheaply and the paper moves on to Phase 3.
# ============================================================

PHASE2_TEMPERATURES = [0.0, 0.3, 0.7]
PHASE2_SAMPLES_PER_CONDITION = 3  # independent stochastic samples per (task, temp)
phase2_results = []

print(f"\nPHASE 2 (PROBE): {MODEL_NAME} — {len(all_tasks)} tasks × {len(PHASE2_TEMPERATURES)} temps × {PHASE2_SAMPLES_PER_CONDITION} samples")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 70)

for temperature in PHASE2_TEMPERATURES:
    print(f"\n--- Temperature {temperature} ---")
    for task in all_tasks:
        for sample_num in range(1, PHASE2_SAMPLES_PER_CONDITION + 1):
            result = run_single_task(task, run_num=sample_num, temperature=temperature)
            result["phase"] = 2
            result["model"] = MODEL_NAME
            phase2_results.append(result)

# Aggregate summary per (task, temperature)
from collections import defaultdict
aggregates = defaultdict(list)
for r in phase2_results:
    key = (r["task_id"], r["temperature"])
    aggregates[key].append(r)

print(f"\n{'='*70}")
print(f"PHASE 2 AGGREGATE: {MODEL_NAME}")
print(f"{'Task ID':<25} {'Temp':>6} {'N':>4} {'JSON':>8} {'Schema':>10} {'Avg ms':>8} {'Avg t/s':>8}")
print("-" * 75)

# Also aggregate overall per temperature
overall_by_temp = defaultdict(lambda: {"json": 0, "schema": 0, "total": 0, "latencies": [], "speeds": []})

for (task_id, temperature), runs in sorted(aggregates.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    jp = sum(1 for r in runs if r["json_valid"])
    sp = sum(1 for r in runs if r["schema_valid"])
    avg_ms = sum(r['latency_ms'] for r in runs) / len(runs)
    avg_tps = sum(r['tokens_per_sec'] for r in runs) / len(runs)
    n = len(runs)
    print(f"{task_id:<25} {temperature:>6.1f} {n:>4} {jp}/{n:>6} {sp}/{n:>8} {avg_ms:>7.0f}ms {avg_tps:>7.1f}")
    
    overall_by_temp[temperature]["json"] += jp
    overall_by_temp[temperature]["schema"] += sp
    overall_by_temp[temperature]["total"] += n
    overall_by_temp[temperature]["latencies"].extend([r['latency_ms'] for r in runs])
    overall_by_temp[temperature]["speeds"].extend([r['tokens_per_sec'] for r in runs])

print("-" * 75)
print(f"OVERALL BY TEMPERATURE:")
for temperature in PHASE2_TEMPERATURES:
    stats = overall_by_temp[temperature]
    total = stats["total"]
    json_pct = 100 * stats["json"] / total if total else 0
    schema_pct = 100 * stats["schema"] / total if total else 0
    avg_lat = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
    avg_tps = sum(stats["speeds"]) / len(stats["speeds"]) if stats["speeds"] else 0
    print(f"  T={temperature:<4}  JSON {stats['json']}/{total} ({json_pct:.0f}%)  Schema {stats['schema']}/{total} ({schema_pct:.0f}%)  "
          f"{avg_lat:.0f}ms  {avg_tps:.1f}tok/s")

print(f"Finished: {datetime.now().isoformat()}")

# Robustness interpretation
baseline_schema_pct = 100 * overall_by_temp[0.0]["schema"] / overall_by_temp[0.0]["total"]
t7_schema_pct = 100 * overall_by_temp[0.7]["schema"] / overall_by_temp[0.7]["total"]
delta = baseline_schema_pct - t7_schema_pct
print(f"\nRobustness check:")
print(f"  Baseline (T=0.0): {baseline_schema_pct:.0f}%")
print(f"  T=0.7:            {t7_schema_pct:.0f}%")
print(f"  Delta:            {delta:.0f} percentage points")
if delta == 0:
    print("  → Failures are deterministic under sampling; expand Phase 2 only if other reasons arise.")
else:
    print(f"  → Sampling induces new failures. Consider expanding Phase 2 to 5 temps × 5 samples.")
```

### Cell 10: Phase 3 — Constrained Decoding (14 tasks × 3 decoders)

This cell replaces the simple `run_single_task` call with a decoder-aware version. It tests three decoding conditions: `native` (baseline greedy, same as Phase 1), `outlines`, and `xgrammar`.

```python
# ============================================================
# PHASE 3: Constrained Decoding × Model Scale
#
# Goal: Does constrained decoding rescue small-model failures?
#       Which failures are structural (CD-fixable) vs semantic (CD-resistant)?
#
# Conditions:
#   native   — unconstrained greedy (reproduces Phase 1)
#   outlines — Outlines JSON schema generation
#   xgrammar — XGrammar logits processor
#
# All conditions use greedy decoding (temperature=0.0, do_sample=False)
# so results are deterministic and directly comparable.
# ============================================================

# --- Install CD frameworks (run once) ---
# IMPORTANT: use %pip (not !pip or a shell `pip install`) so the package lands in
# the SAME Python the Jupyter kernel is running.
#   %pip install outlines xgrammar
#
# NOTE: this targets the Outlines v1+ API (Generator + from_transformers).
# Outlines v0 used `from outlines import models, generate` / `generate.json()`;
# that API was removed in v1.0.

import sys as _sys

# --- CD framework imports ---
HAS_OUTLINES = False
HAS_XGRAMMAR = False

# Outlines v1 API: `import outlines` exposes from_transformers + Generator;
# `outlines.types.JsonSchema` is the schema output type for Generator.
try:
    import outlines
    from outlines.types import JsonSchema
    HAS_OUTLINES = True
except Exception as _e:
    # Broad catch: outlines may be installed but fail to import due to a
    # dependency/version conflict. Surface the real error (and the kernel python).
    print(f"Warning: could not import outlines ({type(_e).__name__}: {_e}).")
    print(f"  kernel python: {_sys.executable}")
    print('  Install into THIS kernel via a cell:  %pip install outlines xgrammar')

try:
    import xgrammar
    HAS_XGRAMMAR = True
except Exception as _e:
    print(f"Warning: could not import xgrammar ({type(_e).__name__}: {_e}).")
    print(f"  kernel python: {_sys.executable}")
    print('  Install into THIS kernel via a cell:  %pip install outlines xgrammar')


# --- CD-aware single task runner ---
def run_single_task_cd(task, run_num=1, temperature=0.0, decoder="native"):
    """
    Run a single benchmark task with optional constrained decoding.

    Args:
        task: task dict from task_definitions
        run_num: sample index
        temperature: 0.0 (all Phase 3 uses greedy for determinism)
        decoder: "native", "outlines", or "xgrammar"
    """

    # Build messages
    user_content = task["prompt"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["structured"]},
        {"role": "user", "content": user_content},
    ]
    text = format_messages(messages)

    # Configure generation kwargs
    generate_kwargs = dict(BASE_GENERATE_KWARGS)
    generate_kwargs["do_sample"] = False  # Phase 3 = greedy for comparability
    # Don't add `temperature` when do_sample=False: newer transformers flags it
    # as an invalid/ignored generation flag. Phase 3 is always greedy anyway.

    compile_ms = 0.0

    # ============== NATIVE (baseline) ==============
    if decoder == "native":
        inputs = tok(text=text, return_tensors="pt").to("cuda")
        input_len = inputs["input_ids"].shape[1]

        start = time.time()
        outputs = model.generate(**inputs, **generate_kwargs)
        elapsed = (time.time() - start) * 1000

        response = tok.decode(outputs[0][input_len:], skip_special_tokens=True)
        num_tokens = outputs.shape[1] - input_len

    # ============== OUTLINES (v1 API) ==============
    elif decoder == "outlines":
        if not HAS_OUTLINES:
            raise ImportError("outlines not installed")

        # outlines_model is wrapped once per notebook (see Cell 10b)

        # Build a Generator for this schema (compiles the FSM here)
        compile_start = time.time()
        schema_json = json.dumps(task["schema"])
        generator = outlines.Generator(outlines_model, JsonSchema(schema_json))
        compile_ms = (time.time() - compile_start) * 1000

        # Generate (Outlines manages tokenization internally; kwargs pass through)
        gen_start = time.time()
        gen_kwargs = {k: v for k, v in generate_kwargs.items()
                      if k in ["max_new_tokens", "pad_token_id"]}
        response = generator(text, **gen_kwargs)
        elapsed = (time.time() - gen_start) * 1000

        # Count tokens (Outlines v1 returns a raw string)
        num_tokens = len(tok.encode(response))

    # ============== XGRAMMAR (0.2 API) ==============
    elif decoder == "xgrammar":
        if not HAS_XGRAMMAR:
            raise ImportError("xgrammar not installed")

        # xgrammar_compiler is built once per notebook (TokenizerInfo is
        # per-model: it reads the whole vocab). See Cell 10b.

        # Compile grammar from schema (per-task) + build the HF logits processor
        compile_start = time.time()
        schema_str = json.dumps(task["schema"])
        compiled_grammar = xgrammar_compiler.compile_json_schema(schema_str)
        xgrammar_processor = xgrammar.contrib.hf.LogitsProcessor(compiled_grammar)
        compile_ms = (time.time() - compile_start) * 1000

        # Generate with logits processor injected
        inputs = tok(text=text, return_tensors="pt").to("cuda")
        input_len = inputs["input_ids"].shape[1]

        start = time.time()
        outputs = model.generate(
            **inputs,
            logits_processor=[xgrammar_processor],
            **generate_kwargs
        )
        elapsed = (time.time() - start) * 1000

        response = tok.decode(outputs[0][input_len:], skip_special_tokens=True)
        num_tokens = outputs.shape[1] - input_len

    else:
        raise ValueError(f"Unknown decoder: {decoder}")

    # ============== VALIDATION (identical for all decoders) ==============
    json_valid = False
    schema_valid = False
    parsed = None
    error_msg = None

    try:
        parsed = extract_json(response)
        if parsed is not None:
            json_valid = True
        else:
            error_msg = "Could not extract valid JSON"
    except Exception as e:
        error_msg = f"JSON parse error: {e}"

    if json_valid:
        try:
            import jsonschema
            jsonschema.validate(instance=parsed, schema=task["schema"])
            schema_valid = True
        except Exception as e:
            schema_valid = False
            error_msg = f"Schema validation: {str(e)[:100]}"

    tokens_per_sec = round(num_tokens / (elapsed / 1000), 1) if elapsed > 0 else 0

    result = {
        "run": run_num,
        "temperature": temperature,
        "decoder": decoder,
        "task_id": task["id"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "latency_ms": round(elapsed, 1),
        "compile_ms": round(compile_ms, 1),
        "tokens_generated": num_tokens,
        "tokens_per_sec": tokens_per_sec,
        "response_raw": response,
        "response_parsed": parsed,
        "error": error_msg,
    }

    status = "✓" if schema_valid else ("~" if json_valid else "✗")
    compile_str = f" (compile: {compile_ms:.0f}ms)" if compile_ms > 0 else ""
    print(f"  {status} {task['id']:<25} [{decoder:<8}] Schema:{schema_valid}  {elapsed:.0f}ms{compile_str}  {tokens_per_sec}tok/s")
    if error_msg and not schema_valid:
        print(f"    Error: {error_msg[:80]}")

    return result
```

```python
# --- Cell 10b: Initialize CD frameworks (run once per model) ---

if HAS_OUTLINES:
    print("Wrapping model for Outlines (v1 from_transformers)...")
    outlines_model = outlines.from_transformers(model, tok)
    print("✓ Outlines model ready")

if HAS_XGRAMMAR:
    print("Initializing XGrammar (TokenizerInfo + GrammarCompiler) ...")
    # TokenizerInfo is per-model (reads the full vocab); build it once.
    # Pass model.config.vocab_size so the token bitmask matches lm_head size
    # (some models pad vocab to a multiple of 32).
    tokenizer_info = xgrammar.TokenizerInfo.from_huggingface(
        tok, vocab_size=model.config.vocab_size
    )
    xgrammar_compiler = xgrammar.GrammarCompiler(tokenizer_info)
    print("✓ XGrammar compiler ready")
```

```python
# --- Cell 10c: Run Phase 3 ---

PHASE3_DECODERS = ["native", "outlines", "xgrammar"]
phase3_results = []

all_tasks = get_all_tasks()

print(f"\nPHASE 3: {MODEL_NAME} — {len(all_tasks)} tasks × {len(PHASE3_DECODERS)} decoders")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 70)

for decoder in PHASE3_DECODERS:
    print(f"\n--- Decoder: {decoder} ---")
    for task in all_tasks:
        result = run_single_task_cd(task, run_num=1, temperature=0.0, decoder=decoder)
        result["phase"] = 3
        result["model"] = MODEL_NAME
        phase3_results.append(result)

# Summary
print(f"\n{'='*70}")
print(f"PHASE 3 SUMMARY: {MODEL_NAME}")
print(f"{'Task ID':<25} {'native':>8} {'outlines':>8} {'xgrammar':>8}")
print("-" * 55)

from collections import defaultdict
p3_agg = defaultdict(dict)
for r in phase3_results:
    p3_agg[r["task_id"]][r["decoder"]] = r["schema_valid"]

for task_id in sorted(p3_agg.keys()):
    n = p3_agg[task_id].get("native", "")
    o = p3_agg[task_id].get("outlines", "")
    x = p3_agg[task_id].get("xgrammar", "")
    print(f"{task_id:<25} {'✓' if n else '✗':>8} {'✓' if o else '✗':>8} {'✓' if x else '✗':>8}")

# Overall rates
for dec in PHASE3_DECODERS:
    total = sum(1 for r in phase3_results if r["decoder"] == dec)
    passed = sum(1 for r in phase3_results if r["decoder"] == dec and r["schema_valid"])
    pct = 100 * passed / total if total else 0
    avg_ms = sum(r["latency_ms"] for r in phase3_results if r["decoder"] == dec) / total
    print(f"\n{dec:<10}: {passed}/{total} ({pct:.1f}%)  avg {avg_ms:.0f}ms/task")

print(f"\nFinished: {datetime.now().isoformat()}")
```

```python
# --- Cell 10d: Export Phase 3 results ---

import csv
from pathlib import Path

MODEL_SHORT = MODEL_NAME.split("/")[-1].replace("-", "_").lower()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save raw JSON
raw_path = f"results/v2/phase3_{MODEL_SHORT}_raw_{timestamp}.json"
with open(raw_path, "w") as f:
    export_results = []
    for r in phase3_results:
        er = {k: v for k, v in r.items()}
        if er.get("response_parsed") is not None:
            er["response_parsed"] = str(er["response_parsed"])
        export_results.append(er)
    json.dump(export_results, f, indent=2, default=str)
print(f"Raw results saved: {raw_path}")

# Save CSV
csv_path = f"results/v2/phase3_{MODEL_SHORT}.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "model", "phase", "decoder", "temperature", "run", "task_id",
        "category", "difficulty", "json_valid", "schema_valid",
        "latency_ms", "compile_ms", "tokens_generated", "tokens_per_sec", "error"
    ])
    writer.writeheader()
    for r in phase3_results:
        writer.writerow({k: r.get(k, "") for k in writer.fieldnames})
print(f"CSV results saved: {csv_path}")
print(f"Total Phase 3 results: {len(phase3_results)}")
```

### Cell 9: Export Results
```python
# ============================================================
# EXPORT: Save results to files
# ============================================================

import csv
from pathlib import Path

MODEL_SHORT = MODEL_NAME.split("/")[-1].replace("-", "_").lower()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 1. Save raw results (JSON)
raw_path = f"results/v2/{MODEL_SHORT}_raw_{timestamp}.json"
with open(raw_path, "w") as f:
    # Convert parsed responses to string for JSON serialization
    export_results = []
    for r in phase1_results + phase2_results:
        er = {k: v for k, v in r.items()}
        if er.get("response_parsed") is not None:
            er["response_parsed"] = str(er["response_parsed"])
        export_results.append(er)
    json.dump(export_results, f, indent=2, default=str)
print(f"Raw results saved: {raw_path}")

# 2. Save CSV (appends to shared results file)
csv_path = "results/v2/benchmark_results_v2.csv"
file_exists = Path(csv_path).exists()

all_results = phase1_results + phase2_results
with open(csv_path, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "model", "phase", "temperature", "run", "task_id", "category", "difficulty",
        "json_valid", "schema_valid", "latency_ms", "tokens_generated",
        "tokens_per_sec", "error"
    ])
    if not file_exists:
        writer.writeheader()
    for r in all_results:
        writer.writerow({k: r.get(k, "") for k in writer.fieldnames})
print(f"CSV results saved: {csv_path}")

print(f"\nTotal results exported: {len(all_results)} "
      f"(Phase 1: {len(phase1_results)}, Phase 2: {len(phase2_results)})")
```

---

## Model-Specific Notes for Each Notebook

### Qwen3-0.6B / Qwen3-1.7B
- Base model (not instruct), but still uses chat template
- Must append `/no_think` to user message content to suppress thinking tokens
- Uses `AutoTokenizer`

### Qwen3-4B-Instruct
- Instruct model
- Must append `/no_think` to user message content
- Uses `AutoTokenizer`

### Qwen3-30B-A3B
- MoE model: 30B total, 3B active per forward pass
- Fits on RTX 4090 (only activates ~3B at a time)
- Must append `/no_think`
- Uses `AutoTokenizer`

### Llama 3.2 1B / 3B
- Must set `pad_token_id=128001` in BASE_GENERATE_KWARGS
- Uses `AutoTokenizer`

### Phi-4-mini
- No special handling
- Uses `AutoTokenizer`

### Gemma 3n 2B
- Check if it uses `AutoTokenizer` or `AutoProcessor`
- Uses standard chat template
- Uses `AutoTokenizer` (verify on model card)

### Gemma 4 2B / 4B / 9B / 12B / E2B
- Use `AutoProcessor` and `AutoModelForVision2Seq` (text-only still uses processor)
- `format_messages` example provided in Cell 5
- Uses `AutoProcessor`

### Mistral-Small-3.2-24B
- Dense 24B; requires ~55GB VRAM (use A100 80GB)
- No special chat-template handling beyond standard `apply_chat_template`
- Uses `AutoTokenizer`

### Gemma 4 E2B
- Uses `AutoProcessor` (not AutoTokenizer)
- Must use `processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)`
- For tokenization: `processor(text=text, return_tensors="pt")`
- For decode: `processor.decode(...)`

### Mistral-Small-24B
- Must set `pad_token_id=2` in BASE_GENERATE_KWARGS
- Needs RTX 6000 Ada (48GB) — will NOT fit on RTX 4090
- Uses `AutoTokenizer`

---

## Critical Rules (Read Before Every Notebook)

1. **`input_len` MUST be calculated inside `run_single_task()`** — NOT from a variable set outside the loop
2. **Task definitions are pasted INLINE** — no imports from external files
3. **Raw outputs are saved** — every response text is captured
4. **`extract_json` regex is FIXED** — the markdown fence pattern uses `r'```(?:json)?\s*(.*?)\s*```'`
5. **`temperature` controls `do_sample`** — `T=0.0` uses greedy decoding; `T>0.0` enables sampling. Phase 1 runs greedy; Phase 2 runs a cheap robustness probe; Phase 3 adds constrained decoding conditions.
6. **Every notebook is self-contained** — can run independently on any GPU instance
7. **Export saves BOTH JSON (raw) and CSV (summary)** — JSON for debugging, CSV for analysis; CSV must include the `temperature` and `decoder` columns so Phase 1/2/3 rows can be analyzed together
8. **Print the timestamp** before and after each phase
