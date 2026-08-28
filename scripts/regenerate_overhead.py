#!/usr/bin/env python3
"""Regenerate Figure 3: CD framework overhead (fig4_overhead.pdf).

Data source: results/v2/phase3/phase3_<model>.csv (compile_ms and
tokens_per_sec columns, 14 tasks x 3 decoders per model, greedy single runs).

Design rules (learned the hard way):
  - this figure had NO regeneration script until 2026-08-28: the original was
    hand-built and could silently go stale after any data re-run
  - XGrammar bars MUST be labeled in ms: 4-8 ms renders as "0.0s" in seconds
    (that was the old bug -- the figure's headline number was invisible)
  - panel (a) is LOG scale and must say so: values span 4 ms to 19.5 s
  - compile bars get min-max whiskers across the 14 schemas: the 19.5 s
    Outlines peak (Phi-4-mini, funcall_search_multi) must be visible in the
    figure, not just claimed in the text
  - panel (b) carries per-bar delta labels: the old caption said throughput
    "is preserved across all conditions", but Outlines runs 9-13% below
    native on 4 of 5 models (and XGrammar is +8% on Qwen-4B, i.e. noise)
  - asserts below pin every number the paper text quotes (Table-5-style)

Run:  .venv/bin/python scripts/regenerate_overhead.py
"""
import csv
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSVDIR = ROOT / "results" / "v2" / "phase3"
OUT = ROOT / "paper_overleaf" / "figures" / "fig4_overhead.pdf"

MODELS = [  # (csv filename stem, two-line display label)
    ("Qwen3-0.6B", "Qwen\n0.6B"),
    ("Llama-3.2-1B-Instruct", "Llama\n1B"),
    ("Llama-3.2-3B-Instruct", "Llama\n3B"),
    ("Phi-4-mini-instruct", "Phi\n4-mini"),
    ("Qwen3-4B-Instruct-2507", "Qwen\n4B"),
]
COLORS = {"native": "#d62728", "outlines": "#1f77b4", "xgrammar": "#2ca02c"}

compile_ms = defaultdict(list)   # (model, decoder) -> [compile_ms]
tput = defaultdict(list)         # (model, decoder) -> [tokens_per_sec]

for stem, _ in MODELS:
    with open(CSVDIR / f"phase3_{stem}.csv") as f:
        for r in csv.DictReader(f):
            if r["compile_ms"]:
                compile_ms[(stem, r["decoder"])].append(float(r["compile_ms"]))
            if r["tokens_per_sec"]:
                tput[(stem, r["decoder"])].append(float(r["tokens_per_sec"]))

assert all(len(compile_ms[(m, d)]) == 14 for m, _ in MODELS
           for d in ["outlines", "xgrammar"]), "expected 5 models x 2 decoders x 14 tasks"
assert all(len(tput[(m, d)]) == 14 for m, _ in MODELS
           for d in ["native", "outlines", "xgrammar"]), "expected 5 x 3 x 14 throughput rows"

c_mean = {k: sum(v) / len(v) for k, v in compile_ms.items()}
c_min = {k: min(v) for k, v in compile_ms.items()}
c_max = {k: max(v) for k, v in compile_ms.items()}
t_mean = {k: sum(v) / len(v) for k, v in tput.items()}
delta = {(m, d): 100.0 * (t_mean[(m, d)] - t_mean[(m, "native")]) / t_mean[(m, "native")]
         for m, _ in MODELS for d in ["outlines", "xgrammar"]}

# ---- guardrails: pin every number the paper text quotes ----------------------
expect_cmean = {  # avg compile time (ms) per (model, decoder)
    ("Qwen3-0.6B", "outlines"): 3031.7, ("Llama-3.2-1B-Instruct", "outlines"): 1983.6,
    ("Llama-3.2-3B-Instruct", "outlines"): 2022.6, ("Phi-4-mini-instruct", "outlines"): 4863.4,
    ("Qwen3-4B-Instruct-2507", "outlines"): 2662.0,
    ("Qwen3-0.6B", "xgrammar"): 7.0, ("Llama-3.2-1B-Instruct", "xgrammar"): 4.2,
    ("Llama-3.2-3B-Instruct", "xgrammar"): 4.3, ("Phi-4-mini-instruct", "xgrammar"): 8.4,
    ("Qwen3-4B-Instruct-2507", "xgrammar"): 5.5,
}
for k, want in expect_cmean.items():
    assert abs(c_mean[k] - want) < 0.15, f"compile mean {k}: got {c_mean[k]:.2f}, expected {want}"

# text claim: Outlines peak 19.5 s (Phi-4-mini) and 2.0-4.9 s per-model averages
assert abs(c_max[("Phi-4-mini-instruct", "outlines")] - 19540.0) < 0.5, "19.5 s peak claim"
ol_means_s = [c_mean[(m, "outlines")] / 1000 for m, _ in MODELS]
assert 1.95 <= min(ol_means_s) <= 2.05 and 4.80 <= max(ol_means_s) <= 4.95, "2.0-4.9 s average claim"

# text claim: XGrammar -1.6..-3.7% on first four models, +8% on Qwen-4B;
# Outlines -9..-13% on first four models
xg = [delta[(m, "xgrammar")] for m, _ in MODELS]
ol = [delta[(m, "outlines")] for m, _ in MODELS]
assert 8.0 <= xg[4] <= 8.5, f"Qwen-4B xgrammar +8% claim: got {xg[4]:.2f}"
assert -4.0 <= min(xg[:4]) and max(xg[:4]) <= -1.5, "1.6-3.7% xgrammar claim"
assert -13.0 <= min(ol[:4]) and max(ol[:4]) <= -9.0, "9-13% outlines penalty claim"

# ---- panel data ----------------------------------------------------------------
x = np.arange(len(MODELS))
ol_mean = np.array([c_mean[(m, "outlines")] / 1000 for m, _ in MODELS])
ol_lo = np.array([c_min[(m, "outlines")] / 1000 for m, _ in MODELS])
ol_hi = np.array([c_max[(m, "outlines")] / 1000 for m, _ in MODELS])
xg_mean = np.array([c_mean[(m, "xgrammar")] / 1000 for m, _ in MODELS])
xg_lo = np.array([c_min[(m, "xgrammar")] / 1000 for m, _ in MODELS])
xg_hi = np.array([c_max[(m, "xgrammar")] / 1000 for m, _ in MODELS])
tp_nat = np.array([t_mean[(m, "native")] for m, _ in MODELS])
tp_ol = np.array([t_mean[(m, "outlines")] for m, _ in MODELS])
tp_xg = np.array([t_mean[(m, "xgrammar")] for m, _ in MODELS])
d_ol = [delta[(m, "outlines")] for m, _ in MODELS]
d_xg = [delta[(m, "xgrammar")] for m, _ in MODELS]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(4.8, 2.5))

# (a) compile time: log-scale grouped bars + min-max whiskers across 14 schemas
w = 0.36
ax1.bar(x - w / 2, ol_mean, w, color=COLORS["outlines"], label="Outlines")
ax1.bar(x + w / 2, xg_mean, w, color=COLORS["xgrammar"], label="XGrammar")
for xi, lo, hi in list(zip(x - w / 2, ol_lo, ol_hi)) + list(zip(x + w / 2, xg_lo, xg_hi)):
    ax1.plot([xi, xi], [lo, hi], color="#333333", linewidth=0.9, alpha=0.6, zorder=3)
ax1.set_yscale("log")
ax1.set_ylim(1.2e-3, 90)
ax1.set_yticks([1e-3, 1e-2, 1e-1, 1, 10])
ax1.set_yticklabels(["1 ms", "10 ms", "0.1 s", "1 s", "10 s"])
ax1.set_ylabel("Avg compile time (log scale)", fontsize=6.5)
ax1.legend(loc="upper left", fontsize=5.5, frameon=False, handlelength=1.1,
           handletextpad=0.4, borderaxespad=0.2)

lbl = dict(fontsize=5.5, ha="center", va="bottom", zorder=4,
           bbox=dict(facecolor="white", edgecolor="none", pad=0.6, alpha=0.85))
for xi, v in zip(x - w / 2, ol_mean):
    ax1.annotate(f"{v:.1f}s", xy=(xi, v), xytext=(0, 1), textcoords="offset points",
                 color=COLORS["outlines"], **lbl)
for xi, v in zip(x + w / 2, xg_mean):
    ax1.annotate(f"{v * 1000:.1f}ms", xy=(xi, v), xytext=(0, 1), textcoords="offset points",
                 color=COLORS["xgrammar"], **lbl)
# surface the headline peak: 19.5 s Outlines compile on Phi-4-mini
ax1.annotate("peak 19.5s", xy=(3 - w / 2, 19.54), xytext=(1.15, 45),
             fontsize=5.5, color=COLORS["outlines"],
             arrowprops=dict(arrowstyle="-", color=COLORS["outlines"], linewidth=0.7))

# (b) throughput: linear bars + delta-vs-native labels
w3 = 0.27
ax2.bar(x - w3, tp_nat, w3 * 0.92, color=COLORS["native"], label="Native")
ax2.bar(x, tp_ol, w3 * 0.92, color=COLORS["outlines"], label="Outlines")
ax2.bar(x + w3, tp_xg, w3 * 0.92, color=COLORS["xgrammar"], label="XGrammar")
ax2.set_ylim(0, 72)
ax2.set_ylabel("Avg throughput (tok/s)", fontsize=6.5)
# delta labels stand VERTICALLY above their own bar: horizontal text is wider
# than a bar, so centered labels spilled onto the neighboring taller bar and
# read as sunk behind it (that was the fourth bug)
for xi, v, d, col in [(x, tp_ol, d_ol, COLORS["outlines"]),
                      (x + w3, tp_xg, d_xg, COLORS["xgrammar"])]:
    for xj, vj, dj in zip(xi, v, d):
        ax2.annotate(f"{dj:+.0f}%", xy=(xj, vj), xytext=(0, 2), textcoords="offset points",
                     fontsize=5.5, ha="center", va="bottom", color=col, rotation=90)
ax2.legend(loc="upper right", fontsize=5.5, frameon=False, handlelength=1.1,
           handletextpad=0.4, borderaxespad=0.2)

for ax, title in [(ax1, "(a) Schema compilation time"), (ax2, "(b) Generation throughput")]:
    ax.set_xticks(x)
    ax.set_xticklabels([lbl_ for _, lbl_ in MODELS], fontsize=5.5)
    ax.set_xlim(-0.6, len(MODELS) - 0.4)
    ax.set_title(title, fontsize=7)
    ax.tick_params(axis="y", labelsize=5.5)
    ax.grid(True, axis="y", alpha=0.2, linewidth=0.4)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.with_suffix(".png"), bbox_inches="tight", dpi=200)
print(f"wrote {OUT}")
print("outlines compile mean s :", [f"{v:.2f}" for v in ol_mean])
print("xgrammar compile mean ms:", [f"{v * 1000:.1f}" for v in xg_mean])
print("throughput native       :", [f"{v:.1f}" for v in tp_nat])
print("outlines delta %        :", [f"{v:+.1f}" for v in d_ol])
print("xgrammar delta %        :", [f"{v:+.1f}" for v in d_xg])
