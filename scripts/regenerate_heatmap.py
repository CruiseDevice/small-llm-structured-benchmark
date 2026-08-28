#!/usr/bin/env python3
"""Regenerate the per-task content accuracy heatmap (Figure: fig3_heatmap.pdf).

IMPORTANT: uses results/v2/phase3/phase3_semantic_evaluation_v2.csv
(content_accuracy_corrected) -- the post-normalization evaluator that Table 6
and Section 4.3 of the paper use. Do NOT feed it the v1 CSV; the old figure
was built from v1 and contradicted the paper text on extract_receipt.

Layout: tasks = rows (14), model x decoder = columns (15).
Blue-dashed boxes highlight the two diagnostic task rows.

Run:  python scripts/regenerate_heatmap.py
Then recompile the paper (tectonic main.tex) and re-verify cells.
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "v2" / "phase3" / "phase3_semantic_evaluation_v2.csv"
OUT = ROOT / "paper_overleaf" / "figures" / "fig3_heatmap.pdf"

TASKS = [
    "json_simple_person", "json_simple_product", "json_nested_address",
    "json_array_orders", "json_complex_api", "schema_weather",
    "schema_database_record", "schema_config_file", "funcall_get_weather",
    "funcall_search_multi", "funcall_database_query", "extract_business_card",
    "extract_receipt", "extract_api_log",
]
MODELS = ["Qwen-0.6B", "Llama-1B", "Llama-3B", "Phi-4-mini", "Qwen-4B"]
DECODES = ["native", "outlines", "xgrammar"]
COLS = [(m, d) for m in MODELS for d in DECODES]

M = np.full((len(TASKS), len(COLS)), np.nan)
seen = set()
with open(CSV) as f:
    for r in csv.DictReader(f):
        i = TASKS.index(r["task_id"])
        j = COLS.index((r["model"], r["decoder"]))
        M[i, j] = float(r["content_accuracy_corrected"])
        seen.add((r["task_id"], r["model"], r["decoder"]))
assert len(seen) == 210, f"expected 210 unique cells, saw {len(seen)}"
assert not np.isnan(M).any(), "missing cells in matrix"

fig, ax = plt.subplots(figsize=(11, 5.4))
im = ax.imshow(M, cmap="Blues", vmin=0.0, vmax=1.0, aspect="auto")

for i in range(len(TASKS)):
    for j in range(len(COLS)):
        v = M[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                color="white" if v > 0.85 else "black")

ax.set_xticks(np.arange(-0.5, len(COLS), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(TASKS), 1), minor=True)
ax.grid(which="minor", color="white", linewidth=0.6)
ax.tick_params(which="minor", length=0)

ax.set_xticks(range(len(COLS)))
# decoder names rotated 45deg, one per column
ax.set_xticklabels([d for _, d in COLS], fontsize=8, rotation=45,
                   rotation_mode="anchor", ha="right")
# model name once per 3-column group, centered under the group
for gi, model in enumerate(MODELS):
    ax.text((gi * 3 + 1) / len(COLS), -0.16, model, transform=ax.transAxes,
            ha="center", va="top", fontsize=9, fontweight="bold")
# white vertical separators between model groups
for b in range(3, len(COLS), 3):
    ax.axvline(b - 0.5, color="white", linewidth=2.5)
ax.set_yticks(range(len(TASKS)))
ax.set_yticklabels(TASKS, fontsize=8)
ax.tick_params(length=0)

# blue dashed highlight around the two diagnostic rows
for task in ("funcall_search_multi", "extract_receipt"):
    i = TASKS.index(task)
    ax.add_patch(Rectangle((-0.5, i - 0.5), len(COLS), 1.0, fill=False,
                           edgecolor="#4C78BA", linestyle="--",
                           linewidth=1.6))

ax.set_title("Per-Task Content Accuracy: CD-Rescuable vs CD-Resistant Failures",
             fontsize=11)

cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.015)
cbar.set_label("Content Accuracy", fontsize=9, labelpad=10)
cbar.ax.tick_params(labelsize=8)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.with_suffix(".png"), bbox_inches="tight", dpi=200)
print(f"wrote {OUT}")
print("sanity spot-checks (must match paper text):")
print("  Qwen-0.6B native extract_receipt      =", M[TASKS.index('extract_receipt'), COLS.index(('Qwen-0.6B', 'native'))], "(paper: 0.000)")
print("  Qwen-0.6B xgrammar extract_receipt    =", M[TASKS.index('extract_receipt'), COLS.index(('Qwen-0.6B', 'xgrammar'))], "(paper: 1.000)")
print("  Qwen-0.6B native funcall_search_multi =", M[TASKS.index('funcall_search_multi'), COLS.index(('Qwen-0.6B', 'native'))], "(paper: 0.200)")
print("  Llama-1B xgrammar funcall_search_multi=", M[TASKS.index('funcall_search_multi'), COLS.index(('Llama-1B', 'xgrammar'))], "(paper: 1.000 hollow rescue)")
