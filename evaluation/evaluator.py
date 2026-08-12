"""
Evaluation module for structured output benchmark.
Checks JSON validity, schema compliance, and content accuracy.
"""

import json
import re
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


@dataclass
class EvalResult:
    """Result of evaluating a single model output."""
    task_id: str
    model_name: str
    raw_output: str
    valid_json: bool = False
    schema_compliant: bool = False
    content_accuracy: float = 0.0
    parsed_output: Optional[dict] = None
    parse_error: Optional[str] = None
    schema_errors: list = field(default_factory=list)
    latency_ms: float = 0.0
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    temperature: float = 0.0
    constrained: bool = False
    system_prompt: str = "basic"
    run_index: int = 0
    function_correct: bool = False
    params_present: bool = False
    function_call_score: float = 0.0

    def to_dict(self):
        return asdict(self)


def extract_json_from_output(raw_output: str) -> Optional[Any]:
    """
    Try to extract valid JSON from model output.
    Handles cases where model wraps JSON in markdown code blocks,
    adds extra text, etc.
    """
    # Try direct parse first
    output = raw_output.strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try removing markdown code fences
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'`(.*?)`',
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try finding JSON object/array boundaries
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = output.find(start_char)
        end_idx = output.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            candidate = output[start_idx:end_idx + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    return None


def check_json_validity(raw_output: str) -> tuple[bool, Optional[Any], Optional[str]]:
    """
    Check if the output contains valid JSON.
    Returns (is_valid, parsed_data, error_message).
    """
    parsed = extract_json_from_output(raw_output)
    if parsed is not None:
        return True, parsed, None

    # Get specific error
    try:
        json.loads(raw_output.strip())
    except json.JSONDecodeError as e:
        return False, None, str(e)

    return False, None, "Could not extract JSON from output"


def check_schema_compliance(parsed_data: Any, schema: dict) -> tuple[bool, list]:
    """
    Check if parsed JSON data complies with the given schema.
    Returns (is_compliant, list_of_errors).
    """
    if not HAS_JSONSCHEMA:
        raise ImportError("jsonschema package is required for schema validation")

    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = list(validator.iter_errors(parsed_data))

    if not errors:
        return True, []

    error_messages = []
    for error in errors:
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        error_messages.append(f"{path}: {error.message}")

    return False, error_messages


def check_function_call(parsed_output: Any, task: dict) -> tuple[bool, bool, float]:
    """
    Evaluate function calling output for correctness.
    Handles both single and multiple function calls.
    Flexible about key names: 'name'/'function' for function name,
    'arguments'/'parameters'/'params' for parameters.
    Returns (function_correct, params_present, score).
    """
    # Determine expected functions and their required param keys
    if "expected_function" in task:
        expected = [(task["expected_function"], task["expected_params_keys"])]
    elif "expected_functions" in task:
        expected = list(zip(task["expected_functions"], task["expected_params_keys"]))
    else:
        return False, False, 0.0

    # Normalize output to a list of call dicts
    calls = parsed_output if isinstance(parsed_output, list) else [parsed_output]
    if not calls or not isinstance(calls[0], dict):
        return False, False, 0.0

    # Extract function names and arguments, handling common key variations
    parsed_calls = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        func_name = call.get("name") or call.get("function") or call.get("tool")
        args = call.get("arguments") or call.get("parameters") or call.get("params") or {}
        if func_name and isinstance(func_name, str):
            parsed_calls.append((func_name, args if isinstance(args, dict) else {}))

    if not parsed_calls:
        return False, False, 0.0

    # Check function name correctness
    parsed_names = {name for name, _ in parsed_calls}
    expected_names = {name for name, _ in expected}
    functions_correct = parsed_names == expected_names

    # Check parameter presence
    total_expected = 0
    total_present = 0

    for exp_name, exp_keys in expected:
        total_expected += len(exp_keys)
        matching = [args for name, args in parsed_calls if name == exp_name]
        if not matching:
            continue  # All params for this function are missing
        args = matching[0]
        for key in exp_keys:
            if key in args:
                total_present += 1

    params_present = (total_present == total_expected) if total_expected > 0 else True
    params_fraction = total_present / total_expected if total_expected > 0 else 1.0

    # Score: function selection (50%) + params present (50%)
    func_score = 1.0 if functions_correct else 0.0
    score = 0.5 * func_score + 0.5 * params_fraction

    return functions_correct, params_present, score


def _normalize_for_comparison(s: str) -> str:
    """
    Normalize a string for semantic comparison.
    Strips case, whitespace, and common formatting punctuation
    (periods, commas, hyphens, parentheses, slashes) that do not
    change the meaning of extracted values like phone numbers,
    company names, or dates.
    
    This is necessary because exact-match scoring penalizes models
    for formatting noise (e.g., 'TechCorp Inc.' vs 'TechCorp Inc',
    '555-123-4567' vs '(555) 123-4567') that a human grader would
    accept as correct. See Section X (Evaluation Methodology).
    """
    if not isinstance(s, str):
        s = str(s)
    s = s.lower().strip()
    # Remove common formatting punctuation and collapse whitespace
    s = re.sub(r'[\.\,\-\(\)\[\]\{\}/\\]+', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def compute_content_accuracy(parsed_output: Any, expected_values: dict) -> float:
    """
    Compute how accurate the content is compared to expected values.
    Returns a score between 0.0 and 1.0.
    
    Uses punctuation-normalized comparison for string fields to avoid
    penalizing formatting variants of semantically correct values.
    """
    if parsed_output is None:
        return 0.0

    if not isinstance(parsed_output, dict):
        return 0.0

    total_fields = len(expected_values)
    if total_fields == 0:
        return 1.0

    correct_fields = 0

    for key, expected in expected_values.items():
        if key not in parsed_output:
            continue

        actual = parsed_output[key]

        if isinstance(expected, str) and isinstance(actual, str):
            # Normalized comparison: strip punctuation/formatting noise
            # for text fields (names, phones, addresses), but be careful
            # with strings that represent numbers (prices, quantities).
            # If either value looks numeric, compare numerically instead.
            def looks_numeric(s):
                try:
                    float(s.replace('$', '').replace(',', '').strip())
                    return True
                except (ValueError, AttributeError):
                    return False
            
            if looks_numeric(expected) or looks_numeric(actual):
                # Numeric comparison: strip currency symbols and compare as floats
                try:
                    e_num = float(expected.replace('$', '').replace(',', '').strip())
                    a_num = float(actual.replace('$', '').replace(',', '').strip())
                    if abs(e_num - a_num) < 0.01:
                        correct_fields += 1
                    elif abs(e_num - a_num) / max(abs(e_num), 1) < 0.1:
                        correct_fields += 0.5
                except ValueError:
                    correct_fields += 0
            elif _normalize_for_comparison(expected) == _normalize_for_comparison(actual):
                correct_fields += 1
            # Fallback: substring match on normalized strings (partial credit)
            elif _normalize_for_comparison(expected) in _normalize_for_comparison(actual) \
                 or _normalize_for_comparison(actual) in _normalize_for_comparison(expected):
                correct_fields += 0.5
        elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if abs(expected - actual) < 0.01:
                correct_fields += 1
            elif abs(expected - actual) / max(abs(expected), 1) < 0.1:
                correct_fields += 0.5
        elif isinstance(expected, list) and isinstance(actual, list):
            # For arrays, check if items match
            if len(expected) == len(actual):
                item_matches = 0
                for exp_item, act_item in zip(expected, actual):
                    if isinstance(exp_item, dict) and isinstance(act_item, dict):
                        # act_item = model output dict, exp_item = expected values dict
                        sub_score = compute_content_accuracy(act_item, exp_item)
                        item_matches += sub_score
                    elif exp_item == act_item:
                        item_matches += 1
                correct_fields += item_matches / len(expected)
        elif expected == actual:
            correct_fields += 1

    return correct_fields / total_fields


def evaluate_output(
    raw_output: str,
    task: dict,
    model_name: str,
    latency_ms: float = 0.0,
    tokens_generated: int = 0,
    temperature: float = 0.0,
    constrained: bool = False,
    system_prompt: str = "basic",
    run_index: int = 0,
) -> EvalResult:
    """
    Full evaluation of a single model output against a task.
    """
    result = EvalResult(
        task_id=task["id"],
        model_name=model_name,
        raw_output=raw_output,
        latency_ms=latency_ms,
        tokens_generated=tokens_generated,
        temperature=temperature,
        constrained=constrained,
        system_prompt=system_prompt,
        run_index=run_index,
    )

    # Step 1: Check JSON validity
    is_valid, parsed, parse_error = check_json_validity(raw_output)
    result.valid_json = is_valid
    result.parsed_output = parsed
    result.parse_error = parse_error

    # Step 2: Check schema compliance (if task has schema)
    if is_valid and "schema" in task:
        is_compliant, errors = check_schema_compliance(parsed, task["schema"])
        result.schema_compliant = is_compliant
        result.schema_errors = errors

    # Step 3: Check function calling correctness (if task has expected functions)
    if is_valid and ("expected_function" in task or "expected_functions" in task):
        func_correct, params_ok, func_score = check_function_call(parsed, task)
        result.function_correct = func_correct
        result.params_present = params_ok
        result.function_call_score = func_score
        result.content_accuracy = func_score

    # Step 4: Check content accuracy (if task has expected values)
    elif is_valid and "expected_values" in task:
        result.content_accuracy = compute_content_accuracy(parsed, task["expected_values"])

    elif is_valid:
        # No expected values and no function calling = schema-only evaluation
        result.content_accuracy = 1.0 if result.schema_compliant else 0.0

    # Step 5: Compute tokens per second
    if latency_ms > 0 and tokens_generated > 0:
        result.tokens_per_second = tokens_generated / (latency_ms / 1000.0)

    return result
