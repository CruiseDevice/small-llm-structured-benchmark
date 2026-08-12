import time
import json
from tasks import SIMPLE_JSON_TASKS

# Try to import jsonschema for strict schema validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("⚠️  jsonschema not installed. Install with: pip install jsonschema")
    print("   Falling back to JSON parse-only validation.\n")

# Note: `model` and `tokenizer` must already be loaded in scope before running this script.
results = []

SYSTEM_PROMPT = "You are helpful assistant. Response with ONLY valid JSON. No markdown, no code blocks, no explanation."

for i, task in enumerate(SIMPLE_JSON_TASKS):
    print(f"\n{'='*60}")
    print(f"Task {i+1}/{len(SIMPLE_JSON_TASKS)}: {task['id']}  (difficulty: {task['difficulty']})")
    print(f"{'='*60}")
    print(f"Prompt: {task['prompt'][:100]}...")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task["prompt"]},
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    start = time.time()
    outputs = model.generate(**inputs, max_new_tokens=512, do_sample=False)
    elapsed = (time.time() - start) * 1000

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    num_tokens = outputs.shape[1] - inputs["input_ids"].shape[1]

    # --- Validation ---
    json_valid = False
    schema_valid = False
    parsed = None
    error_msg = None

    # 1) Check if it's valid JSON
    try:
        parsed = json.loads(response.strip())
        json_valid = True
    except Exception as e:
        error_msg = f"JSON parse error: {e}"

    # 2) Check if it conforms to the schema
    if json_valid and HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=parsed, schema=task["schema"])
            schema_valid = True
        except jsonschema.ValidationError as e:
            schema_valid = False
            error_msg = f"Schema validation error: {e.message}"
    elif json_valid and not HAS_JSONSCHEMA:
        # Basic required-fields check as fallback
        required = task["schema"].get("required", [])
        missing = [f for f in required if f not in (parsed if isinstance(parsed, dict) else {})]
        if missing:
            schema_valid = False
            error_msg = f"Missing required fields: {missing}"
        else:
            schema_valid = True  # best-effort

    tokens_per_sec = round(num_tokens / (elapsed / 1000), 1) if elapsed > 0 else 0

    result = {
        "id": task["id"],
        "difficulty": task["difficulty"],
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "latency_ms": round(elapsed, 1),
        "tokens_generated": num_tokens,
        "tokens_per_sec": tokens_per_sec,
        "response": response,
        "error": error_msg,
    }
    results.append(result)

    # --- Print summary ---
    print(f"\nResponse: {response[:200]}{'...' if len(response) > 200 else ''}")
    print(f"Latency: {round(elapsed, 1)} ms | Tokens: {num_tokens} | Speed: {tokens_per_sec} tok/s")
    print(f"Valid JSON: {'✅ YES' if json_valid else '❌ NO'}")
    print(f"Schema Valid: {'✅ YES' if schema_valid else '❌ NO'}")
    if error_msg:
        print(f"Error: {error_msg}")

# --- Final Summary ---
print(f"\n\n{'='*60}")
print("FINAL SUMMARY")
print(f"{'='*60}")
print(f"{'Task ID':<25} {'Diff':<8} {'JSON':<8} {'Schema':<8} {'Latency':<10} {'tok/s':<8}")
print("-" * 70)

passed_json = 0
passed_schema = 0
for r in results:
    json_status = "✅" if r["json_valid"] else "❌"
    schema_status = "✅" if r["schema_valid"] else "❌"
    if r["json_valid"]:
        passed_json += 1
    if r["schema_valid"]:
        passed_schema += 1
    print(f"{r['id']:<25} {r['difficulty']:<8} {json_status:<8} {schema_status:<8} {r['latency_ms']:<10} {r['tokens_per_sec']:<8}")

print("-" * 70)
print(f"JSON Parse Rate:  {passed_json}/{len(results)} ({100*passed_json/len(results):.0f}%)")
print(f"Schema Valid Rate: {passed_schema}/{len(results)} ({100*passed_schema/len(results):.0f}%)")
