#!/usr/bin/env python3
"""Regenerate Figure 2: Schema validity rate vs. model size (fig1_schema_validity.pdf).

Data source: results/v2/phase3/phase3_semantic_evaluation_v2.csv (schema_valid
column, aggregated per model x decoder over 14 tasks). Same source as Table 5.

Design rules (learned the hard way):
  - log-scale x axis: params span 0.6-4B, linear spacing crushes 0.6/1B together
  - ONE label level on the x axis: model names only (no numeric ticks underneath)
  - y axis capped at 102: a 105% tick on a percentage axis is impossible
  - legend BELOW the axes: the CD lines sit at a flat 100%, so any in-axes
    legend overlaps them (that was the old bug)

Run:  .venv/bin/python scripts/regenerate_schema_validity.py
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "v2" / "phase3" / "phase3_semantic_evaluation_v2.csv"
OUT = ROOT / "paper_overleaf" / "figures" / "fig1_schema_validity.pdf"

# x positions: true parameter counts (log scale), labeled by model name
MODELS = [  # (model_id, display, params_B)
    ("Qwen-0.6B",  "Qwen 0.6B", 0.6),
    ("Llama-1B",   "Llama 1B",   1.0),
    ("Llama-3B",   "Llama 3B",   3.0),
    ("Phi-4-mini", "Phi 4-mini", 3.8),
    ("Qwen-4B",    "Qwen 4B",    4.0),
]
DECODERS = ["native", "outlines", "xgrammar"]
COLORS = {"native": "#d62728", "outlines": "#1f77b4", "xgrammar": "#2ca02c"}

# aggregate schema validity per (model, decoder)
from collections import defaultdict
agg = defaultdict(list)
with open(CSV) as f:
    for r in csv.DictReader(f):
        agg[(r["model"], r["decoder"])].append(r["schema_valid"] == "True")
assert len(agg) == 15 and all(len(v) == 14 for v in agg.values()), "expected 15x14"

rates = {k: 100.0 * sum(v) / len(v) for k, v in agg.items()}

# spot-check against Table 5 in the paper
for probe, want in [(("Llama-1B", "native"), 78.6), (("Qwen-0.6B", "native"), 92.9),
                    (("Phi-4-mini", "native"), 92.9), (("Qwen-4B", "native"), 100.0)]:
    got = rates[probe]
    assert abs(got - want) < 0.05, f"{probe}: got {got}, paper says {want}"

# Categorical, equally-spaced x axis: 5 discrete models; the log-scale variant
# crowds Llama-3B / Phi-4-mini / Qwen-4B ticks too tightly for legible labels.
x = list(range(len(MODELS)))
ys = {d: np.array([rates[(m, d)] for m, _, _ in MODELS]) for d in DECODERS}

fig, ax = plt.subplots(figsize=(4.2, 3.4))
for d in DECODERS:
    ax.plot(x, ys[d], marker="o", markersize=4.5, linewidth=1.6,
            color=COLORS[d], label=d.capitalize())

ax.set_xticks(x)
ax.set_xticklabels([label for _, label, _ in MODELS], fontsize=8)
ax.set_xlim(-0.35, len(MODELS) - 0.65)

ax.set_ylim(70, 102)
ax.set_yticks([70, 80, 90, 100])
ax.set_ylabel("Schema validity (%)", fontsize=9)
ax.tick_params(labelsize=8)
ax.grid(True, axis="y", alpha=0.25, linewidth=0.5)

# annotate the native gap (categorical x: index 3 = Phi-4-mini at 92.9)
ax.annotate("21.4pp gap", xy=(3, 92.9), xytext=(0.65, 74.5),
            fontsize=8, color=COLORS["native"],
            arrowprops=dict(arrowstyle="-", color=COLORS["native"],
                            linewidth=0.8, shrinkA=0, shrinkB=2))

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3,
          frameon=False, fontsize=8, handletextpad=0.4, columnspacing=1.2)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.with_suffix(".png"), bbox_inches="tight", dpi=200)
print(f"wrote {OUT}")
print("values plotted (native):", dict(zip([m for m, _, _ in MODELS], ys["native"])))
print("CD lines both flat at:", ys["outlines"][0], ys["xgrammar"][0])
