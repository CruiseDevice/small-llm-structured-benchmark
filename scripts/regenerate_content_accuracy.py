#!/usr/bin/env python3
"""Regenerate Figure 4: Content accuracy vs. model size (fig2_content_accuracy.pdf).

Data source: results/v2/phase3/phase3_semantic_evaluation_v2.csv, column
content_accuracy_corrected -- the post-normalization evaluator that Table 6,
Section 4.3, and the heatmap use. Same convention as regenerate_heatmap.py.

Design rules (learned the hard way):
  - THE ORIGINAL BUG (2026-08-28 audit): this figure was hand-built from
    content_accuracy_original -- the superseded pre-normalization scoring --
    so its lines (e.g. Qwen-0.6B native 89.4%) contradicted Table 6 (87.1%)
    and understated the extract_receipt rescue the text describes. The
    asserts below pin BOTH the corrected values AND corrected != original.
  - categorical equally-spaced x axis, model names only: the old log-scale
    axis merged "3.8"/"4.0" into "3.84.0", garbled "Phi 4-mini"/"Qwen 4B",
    and left a stray matplotlib "2 x 10^0" tick at a position with no model
  - y axis capped at 102: a 105% tick on an accuracy axis is impossible
  - legend BELOW the axes: an in-axes legend hid the Llama-3B native point
  - tab10 palette (native red / outlines blue / xgrammar green), matching the
    schema-validity and overhead figures -- the old figure used seaborn muted
    and visibly did not match its siblings
  - ONE shaded band, native -> best CD (max of outlines/xgrammar), labeled:
    the old figure shaded an ambiguous region between native and both CD lines
  - marker styles match the schema figure: solid red circles, dashed blue
    hollow rings, solid green squares drawn last (nested when values coincide)

Run:  .venv/bin/python scripts/regenerate_content_accuracy.py
"""
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "v2" / "phase3" / "phase3_semantic_evaluation_v2.csv"
OUT = ROOT / "paper_overleaf" / "figures" / "fig2_content_accuracy.pdf"

MODELS = [  # (model_id, display) -- categorical order, smallest-param-mix first as in siblings
    ("Qwen-0.6B", "Qwen 0.6B"),
    ("Llama-1B", "Llama 1B"),
    ("Llama-3B", "Llama 3B"),
    ("Phi-4-mini", "Phi 4-mini"),
    ("Qwen-4B", "Qwen 4B"),
]
DECODERS = ["native", "outlines", "xgrammar"]
COLORS = {"native": "#d62728", "outlines": "#1f77b4", "xgrammar": "#2ca02c"}

agg = defaultdict(lambda: defaultdict(list))  # model -> decoder -> [corrected]
with open(CSV) as f:
    for r in csv.DictReader(f):
        agg[r["model"]][r["decoder"]].append(float(r["content_accuracy_corrected"]))

assert all(len(agg[m][d]) == 14 for m, _ in MODELS for d in DECODERS), "expected 5 x 3 x 14"
acc = {d: np.array([100.0 * sum(agg[m][d]) / len(agg[m][d]) for m, _ in MODELS]) for d in DECODERS}
best_cd = np.maximum(acc["outlines"], acc["xgrammar"])

# ---- guardrails: pin every value to Table 6 (corrected scoring) ---------------
expect = {  # Table 6, x100
    "native":   [87.1, 77.1, 77.7, 92.9, 100.0],
    "outlines": [92.9, 92.9, 99.1, 99.9, 99.9],
    "xgrammar": [94.3, 98.6, 99.1, 100.0, 100.0],
}
for d, want in expect.items():
    for got, w, (m, _) in zip(acc[d], want, MODELS):
        assert abs(got - w) < 0.06, f"{m}/{d}: corrected mean {got:.2f} vs Table 6 {w}"

# and pin the bug itself: corrected MUST differ from original where the
# rescoring changed values (guards against ever feeding it the wrong column)
with open(CSV) as f:
    orig = defaultdict(list)
    for r in csv.DictReader(f):
        orig[(r["model"], r["decoder"])].append(float(r["content_accuracy_original"]))
for m, d in [("Qwen-0.6B", "native"), ("Phi-4-mini", "native")]:
    o = 100.0 * sum(orig[(m, d)]) / len(orig[(m, d)])
    c = acc[d][[mm for mm, _ in MODELS].index(m)]
    assert abs(c - o) > 1.5, f"{m}/{d}: corrected ({c:.1f}) too close to original ({o:.1f}) -- wrong column?"

# ---- plot -----------------------------------------------------------------------
x = np.arange(len(MODELS))

fig, ax = plt.subplots(figsize=(4.2, 3.4))
# shaded band FIRST (under everything): native -> best CD improvement
ax.fill_between(x, acc["native"], best_cd, color="#999999", alpha=0.14,
                label="CD improvement", zorder=1)

ax.plot(x, acc["native"], marker="o", markersize=4.5, linewidth=1.6,
        color=COLORS["native"], label="Native", zorder=2)
ax.plot(x, acc["xgrammar"], linewidth=1.6, color=COLORS["xgrammar"],
        label="XGrammar", zorder=3)  # markers drawn last, nested in rings
ax.plot(x, acc["outlines"], marker="o", markersize=6.5, linewidth=1.4,
        linestyle=(0, (6, 3)), color=COLORS["outlines"],
        markerfacecolor="white", label="Outlines", zorder=4)
ax.plot(x, acc["xgrammar"], linestyle="none", marker="s", markersize=3.8,
        color=COLORS["xgrammar"], zorder=5)

ax.set_xticks(x)
ax.set_xticklabels([label for _, label in MODELS], fontsize=8)
ax.set_xlim(-0.35, len(MODELS) - 0.65)
ax.set_ylim(70, 102)
ax.set_yticks([70, 80, 90, 100])
ax.set_ylabel("Content accuracy (%)", fontsize=9)
ax.tick_params(labelsize=8)
ax.grid(True, axis="y", alpha=0.25, linewidth=0.5)

# annotate the headline residual: Qwen-0.6B's remaining gap under its BEST CD
# condition (100 - 94.3 = 5.7pp) -- the largest residual gap of the five models.
# Arrow spans EXACTLY green(best CD)->100 with no shrink, and the label spells
# out its endpoints in words: readers were parsing "under best CD" as a
# POSITION (the blue-green gap) instead of a CONDITION, and shrink padding
# pulled the tips ~0.5pp short of both ends (that was the sixth bug).
resid = 100.0 - best_cd[0]
ax.annotate("", xy=(0, 100), xytext=(0, best_cd[0]),
            arrowprops=dict(arrowstyle="<->", color="#333333",
                            linewidth=0.9, shrinkA=0, shrinkB=0))
ax.text(-0.28, 100.5, f"best CD leaves {resid:.1f}pp gap to 100%",
        ha="left", va="bottom", fontsize=7, color="#333333")

handles, labels = ax.get_legend_handles_labels()
order = [labels.index("Native"), labels.index("Outlines"),
         labels.index("XGrammar"), labels.index("CD improvement")]
ax.legend([handles[i] for i in order], [labels[i] for i in order],
          loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2,
          frameon=False, fontsize=8, handletextpad=0.4, columnspacing=1.2)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.with_suffix(".png"), bbox_inches="tight", dpi=200)
print(f"wrote {OUT}")
for d in DECODERS:
    print(f"{d:<9}:", [f"{v:.1f}" for v in acc[d]])
print("best CD  :", [f"{v:.1f}" for v in best_cd])
print(f"Qwen-0.6B residual gap under best CD: {resid:.1f}pp")
