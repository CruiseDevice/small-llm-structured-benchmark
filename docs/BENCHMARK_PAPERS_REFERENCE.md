# Benchmarking Papers Reference

> Literature survey for: **Small LLM Structured Output Benchmark**
> Date compiled: 2026-05-05
> Purpose: Identify relevant benchmarks, position the thesis gap, and inform experimental design

---

## Tier 1: Must-Read (Directly Relevant)

### 1. JSONSchemaBench — ICML 2025
- **Paper**: arXiv 2501.10868 — "Generating Structured Outputs from Language Models: Benchmark and Studies"
- **Authors**: Saibo Geng, Hudson Cooper, Michał Moskal, Samuel Jenkins, Julian Berman, Nathan Ranchin, Robert West, Eric Horvitz, Harsha Nori (EPFL + Microsoft)
- **What**: 10K real-world JSON schemas benchmarking constrained decoding frameworks
- **Frameworks tested**: Guidance, Outlines, Llamacpp, XGrammar, OpenAI, Gemini
- **Evaluation dimensions**:
  - **Efficiency**: Grammar Compilation Time (GCT), Time to First Token (TTFT), Time per Output Token (TPOT)
  - **Coverage**: Declared, Empirical, True coverage + Compliance Rate
  - **Quality**: Impact on downstream task accuracy (GSM8K, Last Letter, Shuffle Objects)
- **Key findings**:
  - Constrained decoding can speed up generation by 50% vs unconstrained
  - Guidance outperforms all other frameworks on efficiency, coverage, and quality
  - Constrained decoding consistently improves downstream task accuracy by up to 4%
  - Llama-3.2-1B used for coverage experiments (in our model range)
- **Why it matters**: Gold standard for evaluating structured output generation. Our thesis should cite and compare against this.
- **Code**: https://github.com/guidance-ai/jsonschemabench
- **Also on**: EleutherAI/lm-evaluation-harness
- **Dataset**: https://huggingface.co/datasets/epfl-dlab/JSONSchemaBench

### 2. BFCL — Berkeley Function Calling Leaderboard — ICML 2025
- **Paper**: "The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models" (PMLR v267, pp. 48371-48392)
- **Authors**: Shishir G. Patil, Huanzhi Mao, Fanjia Yan, Charlie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, Joseph E. Gonzalez (UC Berkeley)
- **What**: The de facto standard benchmark for function/tool calling evaluation
- **Categories**:
  - BFCL V1: Simple, Multiple, Parallel, Parallel-Multiple Function + Chatting, Relevance Detection, REST API, SQL, Java, JavaScript
  - BFCL V2: Live data (67K+ real-world examples from enterprise/OSS contributions), Irrelevance/Relevance Detection
  - BFCL V3: Multi-Turn (Base, Missing Parameters, Missing Functions, Long-Context, Composite)
  - BFCL V4: Holistic agentic evaluation
- **Evaluation metric**: Novel AST (Abstract Syntax Tree) sub-string matching + executable validation
- **Data**: 2K+ curated test cases across 40+ sub-domains
- **Why it matters**: Everyone in function-calling benchmarks against this. Many papers below use BFCL as evaluation framework.
- **Live leaderboard**: https://gorilla.cs.berkeley.edu/leaderboard
- **Code**: https://github.com/ShishirPatil/gorilla (BFCL evaluation)

### 3. "Small Models, Big Tasks" — April 2025
- **Paper**: arXiv 2504.19277 — "Small Models, Big Tasks: An Exploratory Empirical Study on Small Language Models for Function Calling"
- **Authors**: Ishan Kavathekar, Raghav Donakanti, Ponnurangam Kumaraguru, Karthik Vaidhyanathan (IIIT Hyderabad)
- **What**: Exploratory empirical study on SLMs for function calling across diverse domains
- **Method**: Zero-shot, few-shot, and fine-tuning approaches; with/without prompt injection; edge device deployment
- **Key findings**:
  - SLMs improve from zero-shot → few-shot → fine-tuning
  - SLMs **struggle significantly with adhering to output format** — directly relevant to our research gap
  - Models are generally robust to prompt injection (slight performance decline)
  - Edge device experiments show practical feasibility but highlight limitations
- **Why it matters**: Almost exactly our thesis topic. We need to clearly differentiate our work from this.
- **Differentiation angle**: They focus on function calling; we focus on JSON schema adherence with constrained decoding frameworks.

---

## Tier 2: Highly Relevant (Read for Ideas & Positioning)

### 4. TinyAgent — Oct 2024
- **Paper**: arXiv 2409.00608 — "TinyAgent: Function Calling at the Edge"
- **Authors**: Lutfi Eren Erdogan, Nicholas Lee, Siddharth Jha, Sehoon Kim, et al. (UC Berkeley / SqueezeAI Lab)
- **What**: End-to-end framework for training SLMs (1.1B, 7B) for function calling on edge devices (MacBook)
- **Techniques**:
  - LLMCompiler for function calling plans with DAG-based dependency tracking
  - Curated 80K synthetic training data from GPT-4-Turbo (~$500 cost)
  - Tool RAG: Fine-tuned DeBERTa-v3-small for tool retrieval (16-way classification, 0.998 recall)
  - 4-bit quantization for edge deployment
- **Key results**:
  - TinyAgent-1.1B: 80.06% success rate (vs GPT-4-Turbo: 79.08%)
  - TinyAgent-7B: 84.95% success rate
  - 4-bit quantized 1.1B: 0.68GB model size, 2.9s latency, 80.35% accuracy
- **Evaluation metric**: Graph Isomorphism Success Rate (DAG comparison of function calling plans)
- **Takeaway**: Shows SLMs can match/exceed large models with targeted fine-tuning on narrow tasks.

### 5. TinyLLM — Nov 2025
- **Paper**: arXiv 2511.22138 — "TinyLLM: Evaluation and Optimization of Small Language Models for Agentic Tasks on Edge Devices"
- **Authors**: Mohd Ariful Haque, Fahad Rahman, Kishor Datta Gupta, Khalil Shujaee, Roy George (Clark Atlanta University)
- **What**: Comprehensive benchmarking of SLMs (<3B) for agentic tasks using BFCL framework
- **Models tested** (with BFCL results):

| Model | Overall Acc | Live | Non-Live (AST) | Multi-Turn |
|-------|-------------|------|-----------------|------------|
| xLAM-2-3b-fc-r (FC) | 65.74% | 81.03% | 88.22% | 55.62% |
| Qwen3-4B (Prompt) | 62.04% | 75.52% | 82.58% | 35.25% |
| Qwen3-1.7B (Prompt) | 55.49% | 63.48% | 80.03% | 16.88% |
| xLAM-2-1b-fc-r (FC) | 53.97% | 61.57% | 72.42% | 8.38% |
| Qwen3-0.6B (Prompt) | 45.76% | 58.86% | 67.78% | 1.38% |
| TinyLlama-1.1B | 19.73% | 39.18% | 20.00% | 0.00% |
| TinyAgent-1.1B | 19.70% | 39.09% | 20.00% | 0.00% |

- **Optimization methods explored**: SFT, PEFT (LoRA/QLoRA), RL (PPO), DPO, Hybrid (SFT+RL)
- **DPO pipeline**: Converted AgentBank/ALFRED SFT data to chosen-rejected pairs
- **Key insight**: Ultra-compact models (<1B) are inadequate for agentic tasks; 1-3B range is the sweet spot
- **Takeaway**: BFCL numbers for our exact model range. Great baseline comparison data.

### 6. ToolACE — Sep 2024
- **Paper**: arXiv 2409.00920 — "ToolACE: Winning the Points of LLM Function Calling"
- **Authors**: Weiwen Liu, Xu Huang, Xingshan Zeng, et al. (multiple institutions)
- **What**: Automatic agentic pipeline for generating diverse, accurate function-calling training data
- **Data**: 26,507 diverse APIs via self-evolution synthesis; multi-agent dialog generation
- **Verification**: Dual-layer (rule-based + model-based) verification system
- **Key result**: 8B model trained on their data achieves SOTA on BFCL, rivaling GPT-4
- **Takeaway**: Data quality/diversity is critical. Their verification methodology is worth borrowing.

### 7. SLMs for Agentic Tool Calling — Dec 2025
- **Paper**: arXiv 2512.15943 — "Small Language Models for Efficient Agentic Tool Calling: Outperforming Large Models with Targeted Fine-tuning"
- **Authors**: Polaris Jhandi, Owais Kazi, Shreyas Subramanian, Neel Sendas
- **What**: Fine-tuned OPT-350M on ToolBench → 77.55% pass rate
- **Comparison**:

| Model | Params | Pass Rate |
|-------|--------|-----------|
| Their SLM (OPT-350M fine-tuned) | 350M | 77.55% |
| ToolLLaMA-DFS | 7B | 30.18% |
| ChatGPT-CoT | 175B | 26.00% |
| ToolLLaMA-CoT | 7B | 16.27% |
| Claude-CoT | 52B | 2.73% |

- **Caveats**: Evaluated only on ToolBench; tight coupling between training data and evaluation; may not generalize
- **Takeaway**: Shows what's possible with aggressive specialization, but also the risk of overclaiming on narrow benchmarks.

---

## Tier 3: Useful Context

### 8. HREF — Dec 2024
- **Paper**: arXiv 2412.15524 — "HREF: Human Response-Guided Evaluation of Instruction Following"
- **What**: Benchmark for evaluating instruction following with 4,258 human-written instructions across 11 task categories
- **Focus**: LLM-as-a-Judge reliability for instruction following
- **Relevance**: Instruction following is a related but distinct capability from structured output generation.

### 9. Previously Identified Papers
These are papers already in our research corpus:
- **StructEval** (arXiv 2505.20139)
- **StructTest** (arXiv 2412.18011)
- **STED Framework** (arXiv 2512.23712)
- **TOON** (arXiv 2601.12014)

---

## Gap Analysis & Research Positioning

### Our Thesis Niche
No focused benchmark for small-scale open-source models (1B-8B) in production structured output with constrained decoding frameworks.

### How We Differentiate

| Dimension | JSONSchemaBench | BFCL | Small Models Big Tasks | TinyLLM | Our Opportunity |
|-----------|----------------|------|----------------------|---------|-----------------|
| Model focus | 1B-8B | All sizes | SLMs | SLMs (<3B) | ✅ Same range |
| Structured output (JSON Schema) | ✅ Primary | Partial | ❌ | ❌ | ✅ Our differentiator |
| Constrained decoding comparison | ✅ Core focus | ❌ | ❌ | ❌ | ✅ **Big gap** |
| Function calling | ❌ | ✅ Primary | ✅ | ✅ | Complementary |
| Schema adherence evaluation | ✅ | ❌ | ❌ | ❌ | ✅ Underserved |
| Production realism | High (10K schemas) | High (67K live) | Medium | Medium | Our angle |
| Multi-framework comparison | ✅ (6 frameworks) | ❌ | ❌ | ❌ | ✅ Extend to models |

### The Clearest Research Gap
Nobody has done a focused benchmark that tests **small models (1B-8B) specifically on JSON schema adherence** (not just function calling) **with multiple constrained decoding frameworks** (Guidance, Outlines, XGrammar, Llamacpp) in production-like conditions.

- **JSONSchemaBench** evaluates frameworks, not models systematically across scales
- **BFCL** evaluates models but focuses on function calling, not schema adherence
- **Small Models Big Tasks** evaluates SLMs but focuses on function calling, not constrained decoding
- **TinyLLM** evaluates SLMs on BFCL but doesn't compare constrained decoding frameworks

**Our contribution**: A systematic evaluation of how different constrained decoding frameworks affect small model performance on real-world JSON schema adherence tasks, measuring the interplay between model scale, decoding strategy, and schema complexity.

---

## Key Frameworks to Evaluate
Based on the literature:
1. **Guidance** — Best coverage and efficiency in JSONSchemaBench
2. **Outlines** — Popular but slow compilation, lower coverage on complex schemas
3. **Llamacpp** (grammar module) — Good coverage, moderate efficiency
4. **XGrammar** — Fast compilation but under-constrained (permissive)
5. **Native (no constrained decoding)** — Baseline for schema adherence

## Key Models to Test
Aligned with our thesis plan:
- Qwen3-4B-Instruct
- Qwen3-1.7B / Qwen3-0.6B
- Gemma 4 E2B-it / Gemma 4 E4B-it
- Llama 3.2 1B / 3B
- Phi-4-mini
- Mistral-Small-3.2 24B (reference model)

## Action Items
- [ ] Read JSONSchemaBench paper in detail — methodology is directly applicable
- [ ] Read BFCL V3/V4 blog posts for multi-turn evaluation ideas
- [ ] Differentiate from "Small Models, Big Tasks" paper — they're closest to our topic
- [ ] Consider using JSONSchemaBench dataset as evaluation benchmark
- [ ] Consider adding BFCL evaluation for comparison with TinyLLM numbers
- [ ] Design experiments that test model × framework × schema complexity interactions
