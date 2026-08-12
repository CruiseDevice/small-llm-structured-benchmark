1|     1|# Research Findings Log
2|     2|
3|     3|## Session: 2026-05-05
4|     4|
5|     5|### Finding 1: Qwen3-0.6B produces messy but parseable JSON
6|     6|- Model wraps output in `<think/>` tags + markdown code fences even with `/no_think`
7|     7|- `extract_json` function needed to strip wrappers before parsing
8|     8|- Once extracted, JSON is structurally valid 100% of the time
9|     9|- Speed: ~34 tok/s — significantly faster than 4B
10|    10|
11|    11|### Finding 2: Qwen3-4B-Instruct produces clean JSON out of the box
12|    12|- No thinking tags, no markdown wrapping — raw JSON directly
13|    13|- 100% JSON parse, 100% schema valid across all 14 tasks
14|    14|- Speed: ~26 tok/s — slower but more reliable
15|    15|- Better semantic quality (names, values are more realistic)
16|    16|
17|    17|### Finding 3: Where 0.6B breaks — type precision and multi-step compliance
18|    18|- `funcall_search_multi`: Asked for 2 function calls, returned only 1 (search_web). Partial instruction compliance.
19|    19|- `extract_receipt`: Price values were strings ("4.98") instead of numbers (4.98). Schema type mismatch.
20|    20|- Both failures are subtle — model understands JSON structure, fails on type enforcement and counting.
21|    21|
22|    22|### Finding 4: Function calling and extraction are harder categories for small models
23|    23|- Simple JSON and schema adherence: 0.6B at 100%
24|    24|- Function calling: 0.6B at 67% (1 of 3 failed)
25|    25|- Extraction: 0.6B at 67% (1 of 3 failed)
26|    26|- Pattern: tasks requiring semantic understanding + strict typing break first
27|    27|
28|    28|### Finding 5: 4B is slower on simple tasks but faster on complex ones
29|    29|- Simple tasks: 4B is similar or slightly slower latency
30|    30|- Complex tasks (api_response, receipt): 4B can be much faster because it generates fewer wasted tokens (no thinking blocks)
31|    31|- But `extract_receipt` took 6.8s on 4B vs 5.4s on 0.6B — 4B generates more detailed output
32|    32|
33|    33|### Finding 6: Phi-4-mini is 2.3x faster than Qwen3-4B but less accurate
34|    34|- 76-82 tok/s vs Qwen3-4B's ~26 tok/s — dramatically faster
35|    35|- But 78% schema valid vs Qwen3-4B's 100% — speed comes at accuracy cost
36|    36|- Only 9/14 tasks ran (Simple JSON category missing from run — need to re-test)
37|    37|
38|    38|### Finding 7: Phi-4-mini has unusual failure mode — outputs schema instead of data
39|    39|- `schema_weather`: Model output a JSON Schema definition (`"type": "object", "properties": {...}`) wrapping the actual data
40|    40|- The values were inside "properties" instead of at top level — model confused schema definition with data instance
41|    41|- This is different from Qwen3-0.6B's failures — it's a prompt comprehension issue, not a type issue
42|    42|
43|    43|### Finding 8: Receipt price extraction is a consistent failure across models
44|    44|- Qwen3-0.6B: prices as strings without "$" ("4.98" as string)
45|    45|- Phi-4-mini: prices as strings with "$" ("$4.98", "$20.49")
46|    46|- Both fail on `extract_receipt` — monetary value type coercion is a systematic weakness in small models
47|    47|- Qwen3-4B handles this correctly — suggests this is a capability that emerges with scale
48|    48|
49|    49|### Updated Comparison Table (3 models, tasks that all ran)
50|    50|| Metric              | Qwen3-0.6B | Phi-4-mini | Qwen3-4B |
51|    51||---------------------|------------|------------|----------|
52|    52|| Schema Valid Rate   | 86% (12/14)| 78% (7/9)  | 100%     |
53|    53|| Avg tok/s           | ~34.4      | ~80        | ~26.2    |
54|    54|| extract_receipt     | FAIL (str) | FAIL ($)   | PASS     |
55|    55|
56|    56|### Key Questions for Later
57|    57|- Will constrained decoding (outlines/lm-format-enforcer) fix the type errors?
58|    58|- Do other models also fail on receipt extraction?
59|    59|- Does temperature affect type precision?
60|    60|- How do models behave on real-world schemas (OpenAPI, JSON Schema from production APIs)?
61|    61|- Phi-4-mini's schema-instead-of-data failure — is this systematic or a one-off?
62|    62|
63|    63|### Finding 9: Llama 3.2 1B has the most diverse failure modes
64|    64|- 71% schema valid (10/14) — worst so far
65|    65|- 4 failures, each a different kind:
66|    66|  1. `json_complex_api`: Missing required field `metadata` — incomplete generation
67|    67|  2. `schema_database_record`: Leaked JSON Schema keyword `additionalProperties: false` into the data output — model confused schema spec with instance data
68|    68|  3. `schema_config_file`: Missing required field `logging` — incomplete nested structure
69|    69|  4. `funcall_search_multi`: Single object instead of array + only 1 function call — same as 0.6B
70|    70|- Interesting: Llama 1B PASSED `extract_receipt` — the only sub-4B model to do so. Got prices as numbers correctly.
71|    71|
72|    72|### Finding 10: Failure mode diversity by model size
73|    73|- 0.6B (Qwen): Type coercion errors (strings vs numbers)
74|    74|- 3.8B (Phi-4): Schema/data confusion + type coercion
75|    75|- 1B (Llama): Incomplete fields + schema keyword leakage + array/object confusion
76|    76|- 4B (Qwen3): No failures
77|    77|- Pattern: smaller models each have unique failure profiles — not just "more errors" but different kinds of errors
78|    78|
79|    79|### Updated Comparison Table (4 models)
80|    80|| Metric              | Qwen3-0.6B | Llama-1B | Phi-4-mini | Qwen3-4B |
81|    81||---------------------|------------|----------|------------|----------|
82|    82|| Params              | 0.6B       | 1B       | 3.8B       | 4B       |
83|    83|| Schema Valid Rate   | 86%        | 71%      | 86%        | 100%     |
84|    84|| Avg tok/s           | ~34.4      | ~81.5    | ~78.2      | ~26.2    |
85|    85|| extract_receipt     | FAIL       | PASS     | FAIL       | PASS     |
86|    86|| funcall_search_multi| FAIL       | FAIL     | PASS       | PASS     |
87|    87|
88|    88|### Finding 11: Llama 3.2 3B is WORSE than Llama 3.2 1B — scaling inversion
89|    89|- 3B: 79% JSON parse, 64% schema valid
90|    90|- 1B: 100% JSON parse, 71% schema valid
91|    91|- 3B is the only model so far that fails to produce valid JSON at all (3 tasks)
92|    92|- Failures include fundamentally broken output: concatenated JSON objects with semicolons, truncated arrays, corrupted structures
93|    93|- Also ~40% slower than 1B (48 tok/s vs 82 tok/s)
94|    94|- This is a genuine "scaling doesn't always help" finding — same family, larger model, worse results
95|    95|- Possible explanation: 3B may have been over-trained or its instruction tuning may be less aligned for structured output specifically
96|    96|
97|    97|### Finding 12: Gemma 4 E2B-it — MoE is slow and mediocre for structured output
98|    98|- 79% schema valid (11/14) — tied with Phi-4-mini for second-worst
99|    99|- Only model other than Llama 3B to produce invalid JSON (funcall_search_multi: concatenated two JSON objects without array wrapper)
100|   100|- Speed: ~20.5 tok/s — slowest model so far, despite being MoE with only 2B active params
101|   101|- Unique failure: `schema_config_file` used 'OPTIONS' as an HTTP method — not in the allowed enum ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']. Model invented a valid-but-disallowed value.
102|   102|- `json_complex_api`: same missing 'metadata' failure as Llama 1B
103|   103|- Extract receipt: PASSED ✅ — correct price types
104|   104|- Pattern: MoE architecture doesn't help for structured output — the active parameter count (2B) is what matters, and it performs like a ~2B model
105|   105|
106|   106|### Finding 13: Gemma 4 E4B-it — more accurate than E2B but painfully slow
107|   107|- 86% schema valid (12/14) — improved from E2B's 79%, now tied with Qwen3-0.6B and Phi-4-mini
108|   108|- Only 2 failures, both shared with E2B: `json_complex_api` (missing metadata) and `funcall_search_multi` (concatenated objects)
109|   109|- PASSED `schema_config_file` which E2B failed — the 2x active params fixed the enum compliance issue
110|   110|- Speed: ~1.7 tok/s — **12x slower than E2B**, ~15x slower than Qwen3-4B. Latencies of 20-100 seconds are production-unusable.
111|   111|- Extract receipt: PASSED ✅ — correct price types
112|   112|- The JSON/extract accuracy is good but the speed makes it impractical for any real use case
113|   113|- This suggests the Gemma MoE models have very high inference overhead — 4B active params shouldn't be this slow
114|   114|- Note: both Gemma models share exact same failure signature (json_complex_api + funcall_search_multi) — suggests a family-level weakness
115|   115|
116|   116|### Finding 14: Gemma E4B re-run — first run was hardware-bottlenecked
117|   117|- Re-ran on fresh Vast.ai instance: ~17 tok/s instead of 1.7 tok/s — **10x faster**
118|   118|- Accuracy is **identical**: same 86% schema valid, same 2 failures, same error messages
119|   119|- Confirms: first run was GPU memory/contention issue, not a model characteristic
120|   120|- 17 tok/s is still slowest of the non-bottlenecked runs (E2B at ~20, Qwen3-4B at ~26)
121|   121|- MoE routing overhead is real but not catastrophic — ~17 tok/s for 4B active is usable if not fast
122|   122|- **Takeaway: inference infrastructure matters enormously for benchmarking** — the 1.7 tok/s result should be excluded from analysis
123|   123|
124|   124|### Updated Comparison Table (7 models)
125|   125|| Metric              | Qwen3-0.6B | Llama-1B | Gemma-E2B | Gemma-E4B | Llama-3B | Phi-4-mini | Qwen3-4B |
126|   126||---------------------|------------|----------|-----------|-----------|----------|------------|----------|
127|   127|| Params              | 0.6B       | 1B       | 2B act    | 4B act    | 3B       | 3.8B       | 4B       |
128|   128|| JSON Parse Rate     | 100%       | 100%     | 93%       | 93%       | 79%      | 100%       | 100%     |
129|   129|| Schema Valid Rate   | 86%        | 71%      | 79%       | 86%       | 64%      | 86%        | 100%     |
130|   130|| Avg tok/s           | ~34.4      | ~81.5    | ~20.5     | ~17.1     | ~48.3    | ~78.2      | ~26.2    |
131|   131|| extract_receipt     | FAIL       | PASS     | PASS      | PASS      | PASS     | FAIL       | PASS     |
132|   132|| funcall_search_multi| FAIL       | FAIL     | FAIL      | FAIL      | FAIL     | PASS       | PASS     |
133|   133|
134|   134|### Finding 15: Mistral-Small-3.2 24B — 100% accuracy but 10-40x slower than small models
135|   135|- 100% JSON parse, 100% schema valid — only model besides Qwen3-4B to achieve this
136|   136|- Speed: 2.4 tok/s on RTX 6000 Ada (48GB VRAM)
137|   137|- Latencies: 7-77 seconds per task (vs 0.3-7 seconds for smaller models)
138|   138|- Full run took ~10 minutes vs ~1 minute for most other models
139|   139|- Clean output but wraps in markdown code fences inconsistently
140|   140|
141|   141|### Finding 16: Only 2 models achieved 100% on all tasks — and one is 6x smaller
142|   142|- Qwen3-4B: 100% accuracy at 26 tok/s
143|   143|- Mistral-Small-3.2 24B: 100% accuracy at 2.4 tok/s
144|   144|- Qwen3-4B is 6x smaller, 10x faster, and equally accurate
145|   145|- Key paper finding: for structured output specifically, you don't need a big model
146|   146|
147|   147|### COMPLETE BENCHMARK TABLE (8 models)
148|   148|| Model              | Params | JSON% | Schema% | tok/s | Hardware       |
149|   149||--------------------|--------|-------|---------|-------|----------------|
150|   150|| Qwen3-0.6B        | 0.6B   | 100%  | 86%     | 34.4  | RTX 4090       |
151|   151|| Llama-3.2-1B      | 1B     | 100%  | 71%     | 81.5  | RTX 4090       |
152|   152|| Llama-3.2-3B      | 3B     | 79%   | 64%     | 48.3  | RTX 4090       |
153|   153|| Phi-4-mini         | 3.8B   | 100%  | 86%     | 78.2  | RTX 4090       |
154|   154|| Qwen3-4B          | 4B     | 100%  | 100%    | 26.2  | RTX 4090       |
155|   155|| Gemma-4-E2B       | ~5B MoE| 93%   | 79%     | 20.5  | RTX 4090       |
156|   156|| Gemma-4-E4B       | ~8B MoE| 100%  | 86%     | 17.1  | RTX 4090       |
157|   157|| Mistral-Small-3.2 | 24B    | 100%  | 100%    | 2.4   | RTX 6000 Ada   |
158|   158|
159|   159|### Key findings summary for paper:
160|   160|1. Scaling inversion: Llama-3B worse than Llama-1B
161|   161|2. Architecture matters more than size: Phi-4-mini (3.8B) = Qwen3-0.6B accuracy at 2.3x speed
162|   162|3. 4B is the accuracy ceiling: Qwen3-4B matches 24B Mistral at 10x the speed
163|   163|4. funcall_search_multi is the hardest task — only Qwen3-4B and Mistral-24B pass
164|   164|5. extract_receipt type coercion fails on 0.6B and Phi-4 but passes on Llama-1B — model-specific, not size-specific
165|   165|6. MoE doesn't help: Gemma E2B/E4B underperform dense models of similar active params
166|   166|7. Each model has a unique failure profile — not just "more errors" but different kinds
167|   167|
168|   168|---
169|   169|
170|   170|## Phase 2: Multi-Run Benchmarking (3x per task)
171|   171|
172|   172|### Session: 2026-05-06
173|   173|
174|   174|### Finding 17: Qwen3-0.6B Phase 2 — 3-run results confirm zero variance in pass/fail
175|   175|- 42 data points (14 tasks x 3 runs), RTX 4090
176|   176|- JSON Parse: 42/42 (100%), Schema Valid: 36/42 (86%) — identical to Phase 1 single-run
177|   177|- Both failures are 0/3 (never pass): `funcall_search_multi` and `extract_receipt`
178|   178|- All 12 passing tasks are 3/3 (never fail)
179|   179|
180|   180|### Finding 18: Greedy decoding produces deterministic results — outputs are byte-identical across runs
181|   181|- Every task produces the exact same output text in all 3 runs
182|   182|- Latency varies slightly (~5-10% between runs) due to GPU scheduling, but tokens and content are identical
183|   183|- This confirms: with `do_sample=False`, pass/fail is a function of model + prompt, not randomness
184|   184|- Implication for paper: 3 runs establish reliability of the measurement (latency variance), but a single run suffices for accuracy claims with greedy decoding
185|   185|
186|   186|### Finding 19: Phase 2 latency is more stable than Phase 1
187|   187|- Phase 1 avg tok/s: ~34.4 (single run, mixed conditions)
188|   188|- Phase 2 avg tok/s: ~38.6 (3 runs, fresh RTX 4090)
189|   189|- ~12% faster — likely because Phase 2 ran on a fresh RunPod instance with no prior model memory pressure
190|   190|- Latency std dev across 3 runs is very tight: typically <5% of mean per task
191|   191|
192|   192|### Finding 20: funcall_search_multi — consistent single-call output across all runs
193|   193|- Model always returns only `search_web` with 1 item in the array, never `send_email`
194|   194|- Error is always the same: single object `{name: "search_web", ...}` instead of array of 2 objects
195|   195|- The model understands the function calling format but fails on multi-step planning (recognizing that 2 calls are needed)
196|   196|- This is a capability gap, not a formatting issue
197|   197|
198|   198|### Finding 21: extract_receipt — monetary type coercion is deterministic
199|   199|- Prices always returned as strings ("4.98", "4.47") instead of numbers (4.98, 4.47)
200|   200|- Identical failure in all 3 runs
201|   201|- Phase 1 showed same behavior — this is a systematic model-level bug
202|   202|- Constrained decoding (outlines) should theoretically fix this by forcing numeric type
203|   203|
204|   204|### Phase 2 Qwen3-0.6B Aggregate Results
205|   205|| Task ID                 | JSON  | Schema | Avg Latency | Avg tok/s |
206|   206||-------------------------|-------|--------|-------------|-----------|
207|   207|| json_simple_person      | 3/3   | 3/3    | 1214.3 ms   | 37.9      |
208|   208|| json_simple_product     | 3/3   | 3/3    | 1228.6 ms   | 38.2      |
209|   209|| json_nested_address     | 3/3   | 3/3    | 1831.1 ms   | 38.8      |
210|   210|| json_array_orders       | 3/3   | 3/3    | 3506.9 ms   | 39.4      |
211|   211|| json_complex_api        | 3/3   | 3/3    | 4878.1 ms   | 38.4      |
212|   212|| schema_weather          | 3/3   | 3/3    | 1299.8 ms   | 39.2      |
213|   213|| schema_database_record  | 3/3   | 3/3    | 2307.3 ms   | 38.6      |
214|   214|| schema_config_file      | 3/3   | 3/3    | 3854.8 ms   | 37.9      |
215|   215|| funcall_get_weather     | 3/3   | 3/3    | 662.5 ms    | 39.3      |
216|   216|| funcall_search_multi    | 3/3   | 0/3    | 1247.4 ms   | 39.3      |
217|   217|| funcall_database_query  | 3/3   | 3/3    | 1420.0 ms   | 38.7      |
218|   218|| extract_business_card   | 3/3   | 3/3    | 1820.1 ms   | 38.0      |
219|   219|| extract_receipt         | 3/3   | 0/3    | 4832.1 ms   | 38.3      |
220|   220|| extract_api_log         | 3/3   | 3/3    | 3914.5 ms   | 38.6      |
221|   221|
222|   222|### Finding 22: Llama 3.2 1B Phase 2 — deterministic failures, but different from Phase 1
223|   223|- 42 data points (14 tasks x 3 runs), RTX 4090
224|   224|- JSON Parse: 39/42 (93%), Schema Valid: 30/42 (71%)
225|   225|- 4 failures, all 0/3 (fully deterministic):
226|   226|  1. `json_complex_api` — missing `metadata` field (same as Phase 1)
227|   227|  2. `schema_weather` — generates 2 JSON objects concatenated without array wrapper, fails extraction (was PASS in Phase 1)
228|   228|  3. `schema_database_record` — leaks `additionalProperties: false` into data (same as Phase 1)
229|   229|  4. `funcall_search_multi` — single object instead of array (same as Phase 1)
230|   230|- Key difference from Phase 1: `schema_config_file` now PASSES (was fail), `schema_weather` now FAILS (was pass)
231|   231|- Possible explanation: different RunPod instance, different torch/transformers version (pip upgrade fix from last session), or subtle environment difference affecting greedy decoding
232|   232|- Speed: ~99.3 tok/s — 22% faster than Phase 1's ~81.5 tok/s (fresher/cleaner GPU instance)
233|   233|
234|   234|### Finding 23: Llama 1B extract_receipt PASSES consistently — model-specific, not size-specific
235|   235|- 3/3 on extract_receipt with correct numeric prices
236|   236|- Confirms Phase 1 finding: Llama 1B handles monetary type coercion correctly
237|   237|- Meanwhile Qwen3-0.6B and Phi-4-mini fail on this exact task
238|   238|- This is a genuine model-level capability difference, unrelated to parameter count
239|   239|
240|   240|### Finding 24: schema_weather is Llama 1B's unique failure mode — multi-object generation
241|   241|- Instead of generating ONE weather report for ONE city, it generates TWO (New York + Los Angeles)
242|   242|- Two JSON objects concatenated without array wrapper → extract_json can't parse
243|   243|- The model "over-helps" by providing more data than requested
244|   244|- This is different from other models' failure modes — it's a task comprehension issue, not a structural issue
245|   245|
246|   246|### Phase 2 Llama 3.2 1B Aggregate Results
247|   247|| Task ID                 | JSON  | Schema | Avg Latency | Avg tok/s |
248|   248||-------------------------|-------|--------|-------------|-----------|
249|   249|| json_simple_person      | 3/3   | 3/3    | 402.9 ms    | 99.3      |
250|   250|| json_simple_product     | 3/3   | 3/3    | 392.4 ms    | 99.4      |
251|   251|| json_nested_address     | 3/3   | 3/3    | 603.0 ms    | 99.5      |
252|   252|| json_array_orders       | 3/3   | 3/3    | 1454.1 ms   | 99.7      |
253|   253|| json_complex_api        | 3/3   | 0/3    | 1782.7 ms   | 99.3      |
254|   254|| schema_weather          | 0/3   | 0/3    | 2568.5 ms   | 99.3      |
255|   255|| schema_database_record  | 3/3   | 0/3    | 681.7 ms    | 99.7      |
256|   256|| schema_config_file      | 3/3   | 3/3    | 1377.7 ms   | 98.7      |
257|   257|| funcall_get_weather     | 3/3   | 3/3    | 253.0 ms    | 98.8      |
258|   258|| funcall_search_multi    | 3/3   | 0/3    | 355.9 ms    | 98.3      |
259|   259|| funcall_database_query  | 3/3   | 3/3    | 454.7 ms    | 99.0      |
260|   260|| extract_business_card   | 3/3   | 3/3    | 583.4 ms    | 99.4      |
261|   261|| extract_receipt         | 3/3   | 3/3    | 1685.4 ms   | 99.1      |
262|   262|| extract_api_log         | 3/3   | 3/3    | 1240.6 ms   | 99.1      |
263|   263|
264|   264|### Finding 25: Llama 3.2 3B Phase 2 — scaling inversion fully confirmed
265|   265|- 42 data points (14 tasks x 3 runs), RTX 4090
266|   266|- JSON Parse: 33/42 (79%), Schema Valid: 27/42 (64%) — worst of all 8 models
267|   267|- 7 failures, all 0/3 (fully deterministic):
268|   268|  1. `json_array_orders` — truncated JSON, can't extract (0/3 JSON parse)
269|   269|  2. `json_complex_api` — `data.users` is array instead of object, schema type mismatch
270|   270|  3. `schema_database_record` — ID "4a3b2c1d0" is 9 chars, regex requires exactly 8 (`^[a-f0-9]{8}$`)
271|   271|  4. `schema_config_file` — leaks `"type":"object"` into output, structural corruption (0/3 JSON parse)
272|   272|  5. `funcall_search_multi` — two JSON objects separated by semicolon, not wrapped in array (0/3 JSON parse)
273|   273|- Speed: ~41.4 tok/s — **2.4x slower** than Llama 1B's 99.3 tok/s despite same model family
274|   274|- Phase 1 showed same pattern: 3B at 64% schema valid vs 1B at 71%. Phase 2 replicates exactly.
275|   275|- The 3B has more fundamental failures (truncation, corruption) vs 1B's subtler failures (missing fields, schema leaks)
276|   276|
277|   277|### Finding 26: Llama 3B vs 1B — same family, opposite strengths
278|   278|- `schema_weather`: 3B PASSES (3/3), 1B FAILS (0/3) — 3B doesn't over-generate multiple cities
279|   279|- `schema_config_file`: 3B FAILS (0/3), 1B PASSES (3/3) — 3B leaks schema keywords into data
280|   280|- `extract_receipt`: both PASS — monetary type coercion works in this family
281|   281|- `funcall_search_multi`: both FAIL — but differently. 1B returns single object, 3B returns two objects joined by semicolon
282|   282|- The scaling inversion isn't just "more errors" — it's qualitatively different error profiles within the same model family
283|   283|
284|   284|### Phase 2 Llama 3.2 3B Aggregate Results
285|   285|| Task ID                 | JSON  | Schema | Avg Latency | Avg tok/s |
286|   286||-------------------------|-------|--------|-------------|-----------|
287|   287|| json_simple_person      | 3/3   | 3/3    | 791.6 ms    | 40.4      |
288|   288|| json_simple_product     | 3/3   | 3/3    | 718.9 ms    | 41.7      |
289|   289|| json_nested_address     | 3/3   | 3/3    | 1070.4 ms   | 42.0      |
290|   290|| json_array_orders       | 0/3   | 0/3    | 3437.7 ms   | 41.0      |
291|   291|| json_complex_api        | 3/3   | 0/3    | 3201.0 ms   | 42.2      |
292|   292|| schema_weather          | 3/3   | 3/3    | 643.3 ms    | 42.0      |
293|   293|| schema_database_record  | 3/3   | 0/3    | 1171.5 ms   | 41.8      |
294|   294|| schema_config_file      | 0/3   | 0/3    | 1907.4 ms   | 40.9      |
295|   295|| funcall_get_weather     | 3/3   | 3/3    | 440.9 ms    | 40.8      |
296|   296|| funcall_search_multi    | 0/3   | 0/3    | 1615.3 ms   | 41.5      |
297|   297|| funcall_database_query  | 3/3   | 3/3    | 1016.3 ms   | 41.3      |
298|   298|| extract_business_card   | 3/3   | 3/3    | 1158.9 ms   | 41.4      |
299|   299|| extract_receipt         | 3/3   | 3/3    | 3086.3 ms   | 41.5      |
300|   300|| extract_api_log         | 3/3   | 3/3    | 2201.6 ms   | 41.3      |
301|   301|
302|   302|### Finding 27: Phi-4-mini Phase 2 — huge improvement over Phase 1
303|   303|- 42 data points (14 tasks x 3 runs), RTX 4090
304|   304|- JSON Parse: 42/42 (100%), Schema Valid: 36/42 (86%)
305|   305|- Phase 1: 78% schema valid with only 9/14 tasks. Phase 2: 86% with all 14 tasks — significantly better
306|   306|- Phase 1 missing Simple JSON category (4 tasks) likely ran with a different/older notebook version
307|   307|- Only 2 failures, both 0/3:
308|   308|  1. `schema_weather` — wraps data in JSON Schema structure (`"type":"object","properties":{...}`) instead of flat data. `location` ends up nested inside `properties` instead of at top level
309|   309|  2. `extract_receipt` — prices with "$" prefix as strings (`"$4.98"`, `"$20.49"`) instead of numbers. Same failure as Phase 1.
310|   310|- Speed: ~37.4 tok/s — **2x slower** than Phase 1's ~78 tok/s. Possible causes: different RunPod GPU, different torch version, or the pip upgrade from last session changed inference behavior
311|   311|
312|   312|### Finding 28: Phi-4-mini PASSES funcall_search_multi — only sub-4B model to do so
313|   313|- 3/3 on funcall_search_multi, correctly returns array of 2 function calls
314|   314|- Every other sub-4B model fails this task (Qwen3-0.6B, Llama 1B, Llama 3B)
315|   315|- Only Qwen3-4B and Mistral-24B also pass this task
316|   316|- Phi-4-mini at 3.8B params is the smallest model that can handle multi-step function calling
317|   317|- This is a meaningful capability signal — not just "more accurate" but unlocking a task category that smaller models can't do
318|   318|
319|   319|### Finding 29: schema_weather failure is consistent across runs and phases
320|   320|- Phase 1: schema-instead-of-data failure (wraps in JSON Schema definition)
321|   321|- Phase 2: same exact failure, 0/3, identical output structure every run
322|   322|- The model literally outputs `{"type":"object","properties":{"location":"SF",...},"required":[...]}` — it's generating a schema spec, not data
323|   323|- This is a prompt comprehension issue specific to how Phi-4 interprets the weather task
324|   324|
325|   325|### Phase 2 Phi-4-mini Aggregate Results
326|   326|| Task ID                 | JSON  | Schema | Avg Latency | Avg tok/s |
327|   327||-------------------------|-------|--------|-------------|-----------|
328|   328|| json_simple_person      | 3/3   | 3/3    | 1017.4 ms   | 37.4      |
329|   329|| json_simple_product     | 3/3   | 3/3    | 1007.1 ms   | 36.8      |
330|   330|| json_nested_address     | 3/3   | 3/3    | 1598.0 ms   | 36.4      |
331|   331|| json_array_orders       | 3/3   | 3/3    | 3831.5 ms   | 36.6      |
332|   332|| json_complex_api        | 3/3   | 3/3    | 4728.7 ms   | 37.2      |
333|   333|| schema_weather          | 3/3   | 0/3    | 2316.7 ms   | 37.6      |
334|   334|| schema_database_record  | 3/3   | 3/3    | 1905.7 ms   | 37.8      |
335|   335|| schema_config_file      | 3/3   | 3/3    | 3794.5 ms   | 37.7      |
336|   336|| funcall_get_weather     | 3/3   | 3/3    | 672.7 ms    | 37.2      |
337|   337|| funcall_search_multi    | 3/3   | 3/3    | 1981.8 ms   | 37.4      |
338|   338|| funcall_database_query  | 3/3   | 3/3    | 1773.1 ms   | 37.2      |
339|   339|| extract_business_card   | 3/3   | 3/3    | 1470.4 ms   | 37.4      |
340|   340|| extract_receipt         | 3/3   | 0/3    | 4359.8 ms   | 36.7      |
341|   341|| extract_api_log         | 3/3   | 3/3    | 3400.5 ms   | 37.1      |
342|   342|
343|### Finding 30: Qwen3-4B Phase 2 — perfect 100% confirmed across 3 runs
344|- 42 data points (14 tasks x 3 runs), RTX 4090
345|- JSON Parse: 42/42 (100%), Schema Valid: 42/42 (100%)
346|- Zero failures across any task, any run — identical to Phase 1
347|- Outputs appear content-identical across runs (greedy decoding determinism)
348|- Avg speed: ~33.5 tok/s — notably faster than Phase 1's ~26 tok/s (~29% speedup)
349|- Run 3 had slightly lower tok/s on some tasks (30-32 range vs 33-34 in runs 1&2) but all still passed
350|- Model: Qwen/Qwen3-4b-Instruct-2507 (newer checkpoint than Phase 1's Qwen3-4B-Instruct)
351|
352|### Finding 31: Qwen3-4B speed vs Phase 1 — RunPod instance variance confirmed again
353|- Phase 1: ~26 tok/s (single run, mixed conditions)
354|- Phase 2: ~33.5 tok/s (3 runs, fresh RTX 4090)
355|- ~29% faster — same pattern as Finding 19 (Phase 2 faster across the board)
356|- Likely cause: fresh RunPod instance, no prior model memory pressure, possible torch/cUDA version difference
357|- Important for paper: latency numbers are NOT comparable across phases — only within-phase comparisons are valid
358|
359|### Finding 32: Qwen3-4B is the confirmed accuracy ceiling at 4B params
360|- Only model to achieve 100% schema valid across ALL 14 tasks in both Phase 1 and Phase 2
361|- Mistral-24B also achieves 100% but at 6x the parameter count
362|- Phi-4-mini (3.8B) comes closest at 86% but fails on schema_weather and extract_receipt
363|- This reinforces the finding that 4B is a critical capability threshold for structured output
364|
### Finding 33: Gemma E2B Phase 2 — catastrophic regression from Phase 1
- 42 data points (14 tasks x 3 runs), RTX 4090
- JSON Parse: 18/42 (43%), Schema Valid: 15/42 (36%) — DOWN from Phase 1's 93%/79%
- Phase 1: 11/14 tasks passed schema. Phase 2: only 5/14
- Only 5 tasks pass all 3 runs: json_simple_person, json_nested_address, json_array_orders, extract_business_card, extract_receipt
- 9 tasks fail 0/3 — all completely deterministic
- This is the biggest Phase-1-to-Phase-2 regression of any model tested

### Finding 34: Gemma E2B regurgitates schemas instead of generating data
- ALL 3 Schema Adherence tasks: 0/3 — model outputs JSON Schema fragments instead of data instances
- Outputs look like `"},"unit":{"type":"string","enum":["celsius","fahrenheit"]},"conditions":{"type":"string"}` — literally echoing the schema definition from the prompt
- ALL 3 Function Calling tasks: 0/3 — same pattern. Outputs `"object", "properties": {"location": {"type":"string"}}` instead of `{"name":"get_weather","arguments":{"location":"SF"}}`
- The model can't distinguish "here's a schema to follow" from "repeat the schema back"
- Simple JSON and Extraction tasks that DON'T include schemas in the prompt work fine (5/5 JSON-only tasks pass, 2/3 extraction pass)
- This is a **prompt comprehension failure mode** — the presence of a schema in the prompt triggers regurgitation

### Finding 35: Gemma E2B json_simple_product fails uniquely — truncated output
- 0/3 on json_simple_product — output starts with `_name": "Wireless Headphones"` (missing opening `{"product`)
- The model skips the first few tokens of the JSON object
- This is a generation start failure, not a schema issue
- Meanwhile json_simple_person (similar complexity) passes 3/3

### Finding 36: Gemma E2B speed is consistent but slow
- ~17.2 tok/s across all 3 runs, near-zero variance
- Consistent with Phase 1's ~20.5 tok/s (MoE model, slower than dense models)
- Slowest model tested (Mistral-24B excluded — different GPU)
- Latency is very stable: most tasks vary <1% between runs

### Finding 37: Schema-regurgitation is a new failure category not seen in other models
- No other model exhibits this behavior — all others either generate data or fail structurally
- Gemma E2B uniquely interprets "follow this schema" as "echo this schema"
- This may be related to Gemma's training on code/schema-heavy data (MoE mixture could route schema tokens to an expert that continues the schema pattern)
- Important for paper: model architecture (MoE) doesn't just affect accuracy — it affects failure MODE
- Phase 1 did NOT show this behavior, suggesting the Phase 1 run may have used different prompting or a different Gemma checkpoint

### Phase 2 Gemma E2B Aggregate Results
| Task ID                 | JSON  | Schema | Avg Latency | Avg tok/s |
|-------------------------|-------|--------|-------------|-----------|
| json_simple_person      | 3/3   | 3/3    | 2032.4 ms   | 17.2      |
| json_simple_product     | 0/3   | 0/3    | 1911.3 ms   | 17.3      |
| json_nested_address     | 3/3   | 3/3    | 2959.9 ms   | 17.2      |
| json_array_orders       | 3/3   | 3/3    | 6751.8 ms   | 17.2      |
| json_complex_api        | 3/3   | 0/3    | 7736.1 ms   | 17.3      |
| schema_weather          | 0/3   | 0/3    | 1558.0 ms   | 17.3      |
| schema_database_record  | 0/3   | 0/3    | 3627.4 ms   | 17.4      |
| schema_config_file      | 0/3   | 0/3    | 5936.8 ms   | 17.3      |
| funcall_get_weather     | 0/3   | 0/3    | 1106.1 ms   | 17.2      |
| funcall_search_multi    | 0/3   | 0/3    | 3999.7 ms   | 17.2      |
| funcall_database_query  | 0/3   | 0/3    | 2591.8 ms   | 17.4      |
| extract_business_card   | 3/3   | 3/3    | 3172.8 ms   | 17.3      |
| extract_receipt         | 3/3   | 3/3    | 8030.1 ms   | 17.3      |
| extract_api_log         | 0/3   | 0/3    | 8043.2 ms   | 17.3      |
