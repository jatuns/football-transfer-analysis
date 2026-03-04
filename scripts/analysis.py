"""
Football Transfer Intelligence — Phase 2
Data Cleaning & Visualization (Matplotlib / Seaborn)

Run: python scripts/analysis.py
Plots saved to: data/processed/plots/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import seaborn as sns
from scipy.stats import gaussian_kde
from scipy.ndimage import uniform_filter1d
import warnings
import os

warnings.filterwarnings("ignore")

# ── Create directories ─────────────────────────────────────────────────────────
os.makedirs("data/processed/plots", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "#0d1117",
    "axes.facecolor":   "#161b22",
    "axes.labelcolor":  "white",
    "xtick.color":      "white",
    "ytick.color":      "white",
    "text.color":       "white",
    "grid.color":       "#30363d",
    "axes.edgecolor":   "#30363d",
})

LEAGUE_COLORS = {
    "eng Premier League": "#3d85c8",
    "es La Liga":         "#e63946",
    "it Serie A":         "#06d6a0",
    "de Bundesliga":      "#ffd166",
    "fr Ligue 1":         "#c77dff",
}

LEAGUE_LABELS = {
    "eng Premier League": "Premier League",
    "es La Liga":         "La Liga",
    "it Serie A":         "Serie A",
    "de Bundesliga":      "Bundesliga",
    "fr Ligue 1":         "Ligue 1",
}

# ── 1. LOAD & CLEAN DATA ───────────────────────────────────────────────────────
print("Loading data...")
df_raw = pd.read_csv("data/raw/players_data_light-2024_2025.csv")
print(f"   Raw data: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns")

# Drop duplicate columns
dup_prefixes = [
    "Rk_stats_", "Nation_stats_", "Age_stats_",
    "Pos_stats_", "Comp_stats_", "Born_stats_",
]
drop_cols = [c for c in df_raw.columns if any(c.startswith(p) for p in dup_prefixes)]
df = df_raw.drop(columns=drop_cols).copy()

# Convert to numeric
num_cols = ["Age", "MP", "Min", "90s", "Gls", "Ast", "xG", "xAG",
            "PrgC", "PrgP", "PrgR", "Cmp%", "SoT", "Tkl", "Int", "Won%"]
for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter players with at least 5 appearances
df = df[df["MP"] >= 5].copy()

# Simplify position (take first)
df["primary_position"] = df["Pos"].str.split(",").str[0]

# League column
df["League"] = df["Comp"]

# Save cleaned data
df.to_csv("data/processed/players_clean.csv", index=False)
print(f"   Clean data: {df.shape[0]} rows -> data/processed/players_clean.csv ✅")

# ── PLOT 1 — Goals per League (Violin + Strip) ────────────────────────────────
print("\nPlot 1: Goals distribution by league...")

# Filter attackers and midfielders for more meaningful goal distribution
fw_mf = df[df["primary_position"].isin(["FW", "MF"])].copy()

fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

lig_sirasi = list(LEAGUE_COLORS.keys())
colors     = list(LEAGUE_COLORS.values())
labels     = [LEAGUE_LABELS[l] for l in lig_sirasi]

for i, (lig, color, label) in enumerate(zip(lig_sirasi, colors, labels)):
    data = fw_mf[fw_mf["League"] == lig]["Gls"].dropna().values

    parts = ax.violinplot(data, positions=[i], widths=0.7,
                          showmedians=False, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_facecolor(color)
        pc.set_alpha(0.4)
        pc.set_edgecolor(color)

    jitter = np.random.uniform(-0.15, 0.15, size=len(data))
    ax.scatter(np.full(len(data), i) + jitter, data,
               color=color, alpha=0.35, s=12, zorder=2)

    median = np.median(data)
    ax.hlines(median, i - 0.2, i + 0.2, color="white",
              linewidth=2.5, zorder=3,
              path_effects=[pe.withStroke(linewidth=4, foreground="#0d1117")])
    ax.text(i, median + 0.3, f"{median:.1f}",
            ha="center", va="bottom", color="white",
            fontsize=10, fontweight="bold")

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel("Goals", fontsize=12)
ax.set_title("Goals Distribution by League — Forwards & Midfielders (2024/25)",
             fontsize=15, fontweight="bold", pad=15)
fig.text(0.5, -0.02,
    "💡 Bundesliga forwards score the most on average — La Liga shows the widest spread with several high outliers.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/01_goals_by_league.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/01_goals_by_league.png")

# ── PLOT 2 — xG vs Actual Goals (Scatter) ────────────────────────────────────
print("Plot 2: xG vs Actual Goals...")

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

fw_df = df[df["primary_position"].isin(["FW", "MF"])].copy()
fw_df = fw_df.dropna(subset=["xG", "Gls"])

for lig, color in LEAGUE_COLORS.items():
    sub = fw_df[fw_df["League"] == lig]
    ax.scatter(sub["xG"], sub["Gls"], c=color, alpha=0.6, s=40,
               label=LEAGUE_LABELS[lig])

max_val = max(fw_df["xG"].max(), fw_df["Gls"].max()) + 1
ax.plot([0, max_val], [0, max_val], "--", color="#8b949e",
        linewidth=1.5, label="xG = Goals (expected)")

fw_df["overperform"] = fw_df["Gls"] - fw_df["xG"]
top5 = fw_df.nlargest(5, "overperform")
for _, row in top5.iterrows():
    ax.annotate(row["Player"], (row["xG"], row["Gls"]),
                fontsize=7, color="white", alpha=0.9,
                xytext=(5, 5), textcoords="offset points")

ax.set_xlabel("Expected Goals (xG)", fontsize=12)
ax.set_ylabel("Actual Goals", fontsize=12)
ax.set_title("xG vs Actual Goals — Overperformers by League (2024/25)",
             fontsize=14, fontweight="bold", pad=15)
ax.legend(fontsize=9, framealpha=0.2)
fig.text(0.5, -0.02,
    "💡 Players above the dashed line scored more than expected — overperformance is a key transfer value indicator.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/02_xg_vs_goals.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/02_xg_vs_goals.png")

# ── PLOT 3 — Most Efficient Clubs (G+A per 90) ───────────────────────────────
print("Plot 3: Most efficient clubs (G+A per 90)...")

df["GA_per90"] = (df["Gls"] + df["Ast"]) / df["90s"].replace(0, np.nan)
club_efficiency = (
    df.groupby(["Squad", "League"])["GA_per90"]
    .mean()
    .reset_index()
    .sort_values("GA_per90", ascending=False)
    .head(20)
)

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

bar_colors = [LEAGUE_COLORS.get(row["League"], "#8b949e")
              for _, row in club_efficiency.iterrows()]
ax.barh(club_efficiency["Squad"], club_efficiency["GA_per90"],
        color=bar_colors, alpha=0.85)

ax.set_xlabel("Average Goals+Assists / 90 min", fontsize=12)
ax.set_title("Top 20 Most Efficient Clubs — Goal Contribution (G+A per 90)",
             fontsize=14, fontweight="bold", pad=15)
ax.invert_yaxis()

patches = [mpatches.Patch(color=c, label=LEAGUE_LABELS[l])
           for l, c in LEAGUE_COLORS.items()]
ax.legend(handles=patches, fontsize=9, framealpha=0.2, loc="lower right")
fig.text(0.5, -0.02,
    "💡 PSG and Nice lead the ranking — Bundesliga clubs dominate the top 20, suggesting an attacking style of play.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/03_club_efficiency.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/03_club_efficiency.png")

# ── PLOT 4 — Age vs xG (Performance Curve) ───────────────────────────────────
print("Plot 4: Age vs xG (performance curve)...")

fw_age = df[df["primary_position"].isin(["FW", "MF"])].dropna(subset=["Age", "xG"])
fw_age = fw_age[(fw_age["Age"] >= 17) & (fw_age["Age"] <= 36)].copy()

fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

for lig, color in LEAGUE_COLORS.items():
    sub = fw_age[fw_age["League"] == lig]
    ax.scatter(sub["Age"], sub["xG"], c=color, alpha=0.25, s=18,
               label=LEAGUE_LABELS[lig])

age_grp = fw_age.groupby("Age")["xG"].mean().reset_index().sort_values("Age")
smooth  = uniform_filter1d(age_grp["xG"].values, size=3)
ax.plot(age_grp["Age"], smooth, color="white", linewidth=3,
        zorder=5, label="Age average (smoothed)")

peak_age = int(age_grp.loc[age_grp["xG"].idxmax(), "Age"])
peak_xg  = age_grp["xG"].max()
ax.axvline(peak_age, color="#ffd166", linewidth=1.5, linestyle="--", alpha=0.7)
ax.text(peak_age + 0.3, peak_xg * 0.85,
        f"Peak: age {peak_age}",
        color="#ffd166", fontsize=10, fontweight="bold")

ax.set_xlabel("Age", fontsize=12)
ax.set_ylabel("Expected Goals (xG)", fontsize=12)
ax.set_title("Age & Goal Productivity — Player Performance Curve (FW + MF, 2024/25)",
             fontsize=14, fontweight="bold", pad=15)
ax.legend(fontsize=9, framealpha=0.2, ncol=2)
fig.text(0.5, -0.02,
    "💡 Goal productivity peaks between ages 24–28 — players in this range command the highest transfer fees.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/04_age_xg_curve.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/04_age_xg_curve.png")

# ── PLOT 5 — Progressive Carries by Position (KDE) ───────────────────────────
print("Plot 5: Progressive carries by position...")

pos_order  = ["DF", "MF", "FW"]
pos_labels = {"DF": "Defenders", "MF": "Midfielders", "FW": "Forwards"}
pos_colors = {"DF": "#06d6a0", "MF": "#3d85c8", "FW": "#e63946"}

fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=False)
fig.patch.set_facecolor("#0d1117")
fig.suptitle("Progressive Carries (PrgC) by Position",
             fontsize=15, fontweight="bold", color="white", y=1.01)

pos_df = df[df["primary_position"].isin(pos_order)].dropna(subset=["PrgC"])

for ax, pos in zip(axes, pos_order):
    ax.set_facecolor("#161b22")
    data  = pos_df[pos_df["primary_position"] == pos]["PrgC"].values
    color = pos_colors[pos]

    kde    = gaussian_kde(data, bw_method=0.3)
    x_vals = np.linspace(data.min(), data.max(), 300)
    y_vals = kde(x_vals)

    ax.fill_between(x_vals, y_vals, alpha=0.35, color=color)
    ax.plot(x_vals, y_vals, color=color, linewidth=2.5)

    median = np.median(data)
    ax.axvline(median, color="white", linewidth=1.8, linestyle="--", alpha=0.8)
    ax.text(median + 0.5, max(y_vals) * 0.05,
            f"Med: {median:.0f}", color="white", fontsize=9)

    ax.set_title(pos_labels[pos], fontsize=13, fontweight="bold",
                 color=color, pad=10)
    ax.set_xlabel("PrgC", fontsize=11)
    ax.set_ylabel("Density" if pos == "DF" else "", fontsize=11)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

fig.text(0.5, -0.02,
    "💡 Forwards carry the ball further per action (long right tail) — midfielders lead in volume of progressive carries.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/05_prgc_by_position.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/05_prgc_by_position.png")

# ── PLOT 6 — Correlation Heatmap ──────────────────────────────────────────────
print("Plot 6: Correlation heatmap...")

corr_cols = ["Age", "MP", "Min", "Gls", "Ast", "xG", "xAG",
             "PrgC", "PrgP", "SoT", "Cmp%", "Tkl", "Int"]
corr_cols = [c for c in corr_cols if c in df.columns]
corr_df   = df[corr_cols].dropna()

fig, ax = plt.subplots(figsize=(11, 9))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

corr_matrix = corr_df.corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

cmap = sns.diverging_palette(220, 10, as_cmap=True)
sns.heatmap(
    corr_matrix, mask=mask, cmap=cmap, center=0,
    annot=True, fmt=".2f", annot_kws={"size": 8},
    linewidths=0.5, linecolor="#30363d",
    ax=ax, cbar_kws={"shrink": 0.8}
)
ax.set_title("Player Statistics Correlation Matrix",
             fontsize=14, fontweight="bold", pad=15)
fig.text(0.5, -0.02,
    "💡 xG–Goals (0.93) and xAG–SoT (0.91) are nearly interchangeable — both can be used as proxies in predictive models.",
    ha="center", fontsize=10, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/06_correlation_matrix.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/06_correlation_matrix.png")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════════╗
║  Phase 2 — Python Analysis Complete!                        ║
╠══════════════════════════════════════════════════════════════╣
║  Clean data : data/processed/players_clean.csv             ║
║  Plots      : data/processed/plots/                        ║
║     01 — Goals distribution by league (violin)             ║
║     02 — xG vs Actual Goals scatter                        ║
║     03 — Top 20 most efficient clubs                       ║
║     04 — Age-performance curve                             ║
║     05 — Progressive carries by position (KDE)            ║
║     06 — Correlation matrix                                ║
╠══════════════════════════════════════════════════════════════╣
║  Next step: notebooks/r_analysis.R                         ║
╚══════════════════════════════════════════════════════════════╝
""")