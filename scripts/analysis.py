"""
Football Transfer Intelligence — Aşama 2
Veri Temizleme & Görselleştirme (Matplotlib / Seaborn)

Çalıştır: python scripts/analysis.py
Grafikler: data/processed/plots/ klasörüne kaydedilir.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")

# ── Klasörleri oluştur ─────────────────────────────────────────────────────────
os.makedirs("data/processed/plots", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

# ── Stil ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "#0d1117",
    "axes.facecolor":  "#161b22",
    "axes.labelcolor": "white",
    "xtick.color":     "white",
    "ytick.color":     "white",
    "text.color":      "white",
    "grid.color":      "#30363d",
    "axes.edgecolor":  "#30363d",
})

LEAGUE_COLORS = {
    "eng Premier League": "#3d85c8",
    "es La Liga":         "#e63946",
    "it Serie A":         "#06d6a0",
    "de Bundesliga":      "#ffd166",
    "fr Ligue 1":         "#c77dff",
}

# ── 1. VERİYİ OKU & TEMİZLE ───────────────────────────────────────────────────
print("📂 Veri okunuyor...")
df_raw = pd.read_csv("data/raw/players_data_light-2024_2025.csv")
print(f"   Ham veri: {df_raw.shape[0]} satır, {df_raw.shape[1]} kolon")

# Tekrar kolonları at
dup_prefixes = [
    "Rk_stats_", "Nation_stats_", "Age_stats_",
    "Pos_stats_", "Comp_stats_", "Born_stats_",
]
drop_cols = [c for c in df_raw.columns if any(c.startswith(p) for p in dup_prefixes)]
df = df_raw.drop(columns=drop_cols).copy()

# Sayısal sütunlara dönüştür (bazıları string gelebilir)
num_cols = ["Age", "MP", "Min", "90s", "Gls", "Ast", "xG", "xAG",
            "PrgC", "PrgP", "PrgR", "Cmp%", "SoT", "Tkl", "Int", "Won%"]
for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Sadece yeterli süre oynayan oyuncuları al (min 5 maç)
df = df[df["MP"] >= 5].copy()

# Pozisyonu sadeleştir (ilk pozisyonu al)
df["ana_pozisyon"] = df["Pos"].str.split(",").str[0]

# Lig kısaltması temizle
df["Lig"] = df["Comp"]

# Temizlenmiş veriyi kaydet
df.to_csv("data/processed/players_clean.csv", index=False)
print(f"   Temiz veri: {df.shape[0]} satır → data/processed/players_clean.csv ✅")

# ── 2. GRAFİK 1 — Lig Başına Oyuncu Gol Dağılımı (Box Plot) ──────────────────
print("\n📊 Grafik 1: Lig başına gol dağılımı...")

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

lig_sirasi = list(LEAGUE_COLORS.keys())
data_by_lig = [df[df["Lig"] == lig]["Gls"].dropna().values for lig in lig_sirasi]
lig_labels  = ["Premier\nLeague", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
colors      = list(LEAGUE_COLORS.values())

bp = ax.boxplot(
    data_by_lig, patch_artist=True, notch=False,
    medianprops=dict(color="white", linewidth=2),
    whiskerprops=dict(color="#8b949e"),
    capprops=dict(color="#8b949e"),
    flierprops=dict(marker="o", markersize=3, alpha=0.5),
)
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
for flier, color in zip(bp["fliers"], colors):
    flier.set(markerfacecolor=color, markeredgecolor=color)

ax.set_xticklabels(lig_labels, fontsize=12)
ax.set_ylabel("Gol Sayısı", fontsize=12)
ax.set_title("Lig Başına Oyuncu Gol Dağılımı (2024/25)", fontsize=15, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig("data/processed/plots/01_lig_gol_dagilimi.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/01_lig_gol_dagilimi.png")

# ── 3. GRAFİK 2 — xG vs Gerçek Gol (Scatter) ─────────────────────────────────
print("📊 Grafik 2: xG vs Gerçek Gol...")

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

fw_df = df[df["ana_pozisyon"].isin(["FW", "MF"])].copy()
fw_df = fw_df.dropna(subset=["xG", "Gls"])

for lig, color in LEAGUE_COLORS.items():
    sub = fw_df[fw_df["Lig"] == lig]
    ax.scatter(sub["xG"], sub["Gls"], c=color, alpha=0.6, s=40, label=lig.replace("eng ", "").replace("es ", "").replace("it ", "").replace("de ", "").replace("fr ", ""))

# 45 derece referans çizgisi (xG = Gls)
max_val = max(fw_df["xG"].max(), fw_df["Gls"].max()) + 1
ax.plot([0, max_val], [0, max_val], "--", color="#8b949e", linewidth=1.5, label="xG = Gol (beklenti)")

# En çok xG'yi aşan oyuncuları etiketle (top 5)
fw_df["overperform"] = fw_df["Gls"] - fw_df["xG"]
top5 = fw_df.nlargest(5, "overperform")
for _, row in top5.iterrows():
    ax.annotate(row["Player"], (row["xG"], row["Gls"]),
                fontsize=7, color="white", alpha=0.9,
                xytext=(5, 5), textcoords="offset points")

ax.set_xlabel("Beklenen Gol (xG)", fontsize=12)
ax.set_ylabel("Gerçek Gol", fontsize=12)
ax.set_title("xG vs Gerçek Gol — Sürpriz Forvetler & Ligler (2024/25)", fontsize=14, fontweight="bold", pad=15)
ax.legend(fontsize=9, framealpha=0.2)
plt.tight_layout()
plt.savefig("data/processed/plots/02_xg_vs_gol.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/02_xg_vs_gol.png")

# ── 4. GRAFİK 3 — En Verimli Kulüpler (Gol+Asist / 90 dk) ───────────────────
print("📊 Grafik 3: En verimli kulüpler (G+A per 90)...")

df["GA_per90"] = (df["Gls"] + df["Ast"]) / df["90s"].replace(0, np.nan)
kulup_verim = (
    df.groupby(["Squad", "Lig"])["GA_per90"]
    .mean()
    .reset_index()
    .sort_values("GA_per90", ascending=False)
    .head(20)
)

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

bar_colors = [LEAGUE_COLORS.get(row["Lig"], "#8b949e") for _, row in kulup_verim.iterrows()]
bars = ax.barh(kulup_verim["Squad"], kulup_verim["GA_per90"], color=bar_colors, alpha=0.85)

ax.set_xlabel("Ortalama Gol+Asist / 90 dk", fontsize=12)
ax.set_title("En Verimli 20 Kulüp — Gol Katkısı (G+A per 90)", fontsize=14, fontweight="bold", pad=15)
ax.invert_yaxis()

# Lejant
patches = [mpatches.Patch(color=c, label=l.replace("eng ","").replace("es ","").replace("it ","").replace("de ","").replace("fr ",""))
           for l, c in LEAGUE_COLORS.items()]
ax.legend(handles=patches, fontsize=9, framealpha=0.2, loc="lower right")
plt.tight_layout()
plt.savefig("data/processed/plots/03_kulup_verim.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/03_kulup_verim.png")

# ── 5. GRAFİK 4 — Yaş vs xG (Oyuncu Ömrü Eğrisi) ────────────────────────────
print("📊 Grafik 4: Yaş vs xG (performans eğrisi)...")

fw_age = df[df["ana_pozisyon"].isin(["FW", "MF"])].dropna(subset=["Age", "xG"])
fw_age = fw_age[(fw_age["Age"] >= 17) & (fw_age["Age"] <= 38)]

yas_grp = fw_age.groupby("Age")["xG"].mean().reset_index()

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

ax.scatter(fw_age["Age"], fw_age["xG"], alpha=0.2, s=20, color="#3d85c8")
ax.plot(yas_grp["Age"], yas_grp["xG"], color="#ffd166", linewidth=2.5, label="Yaş ortalaması")

ax.set_xlabel("Yaş", fontsize=12)
ax.set_ylabel("Beklenen Gol (xG)", fontsize=12)
ax.set_title("Yaş & Gol Üretkenliği — Oyuncu Performans Eğrisi (FW + MF)", fontsize=14, fontweight="bold", pad=15)
ax.legend(fontsize=10, framealpha=0.2)
plt.tight_layout()
plt.savefig("data/processed/plots/04_yas_xg.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/04_yas_xg.png")

# ── 6. GRAFİK 5 — Pozisyon Başına Top Kontrol (Progressive Carries) ──────────
print("📊 Grafik 5: Pozisyon başına top taşıma...")

pos_order = ["GK", "DF", "MF", "FW"]
pos_df = df[df["ana_pozisyon"].isin(pos_order)].dropna(subset=["PrgC"])

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

pos_colors = {"GK": "#8b949e", "DF": "#06d6a0", "MF": "#3d85c8", "FW": "#e63946"}

for pos in pos_order:
    sub = pos_df[pos_df["ana_pozisyon"] == pos]["PrgC"]
    ax.hist(sub, bins=30, alpha=0.65, color=pos_colors[pos], label=pos, density=True)

ax.set_xlabel("İlerletici Top Taşıma (PrgC)", fontsize=12)
ax.set_ylabel("Yoğunluk", fontsize=12)
ax.set_title("Pozisyon Başına İlerletici Top Taşıma Dağılımı", fontsize=14, fontweight="bold", pad=15)
ax.legend(fontsize=11, framealpha=0.2)
plt.tight_layout()
plt.savefig("data/processed/plots/05_pozisyon_prgc.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/05_pozisyon_prgc.png")

# ── 7. GRAFİK 6 — Korelasyon Isı Haritası ────────────────────────────────────
print("📊 Grafik 6: Korelasyon ısı haritası...")

corr_cols = ["Age", "MP", "Min", "Gls", "Ast", "xG", "xAG",
             "PrgC", "PrgP", "SoT", "Cmp%", "Tkl", "Int"]
corr_cols = [c for c in corr_cols if c in df.columns]
corr_df = df[corr_cols].dropna()

fig, ax = plt.subplots(figsize=(11, 9))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

corr_matrix = corr_df.corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # sadece alt üçgen

cmap = sns.diverging_palette(220, 10, as_cmap=True)
sns.heatmap(
    corr_matrix, mask=mask, cmap=cmap, center=0,
    annot=True, fmt=".2f", annot_kws={"size": 8},
    linewidths=0.5, linecolor="#30363d",
    ax=ax, cbar_kws={"shrink": 0.8}
)
ax.set_title("Oyuncu İstatistikleri Korelasyon Matrisi", fontsize=14, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig("data/processed/plots/06_korelasyon.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/06_korelasyon.png")

# ── 8. ÖZET ───────────────────────────────────────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════╗
║  Aşama 2 — Python Analizi Tamamlandı!                   ║
╠══════════════════════════════════════════════════════════╣
║  📁 Temiz veri  : data/processed/players_clean.csv      ║
║  🖼️  Grafikler   : data/processed/plots/                 ║
║     01 — Lig başına gol dağılımı (box plot)             ║
║     02 — xG vs Gerçek Gol scatter                       ║
║     03 — En verimli 20 kulüp                            ║
║     04 — Yaş-Performans eğrisi                          ║
║     05 — Pozisyon başına top taşıma                     ║
║     06 — Korelasyon ısı haritası                        ║
╠══════════════════════════════════════════════════════════╣
║  📌 Sonraki adım: notebooks/r_analysis.R                ║
╚══════════════════════════════════════════════════════════╝
""")