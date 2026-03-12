"""
Football Transfer Intelligence — Phase 3
Player Market Value Prediction (Random Forest + Linear Regression)

Run: python scripts/market_value_model.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
import os

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")
os.makedirs("data/processed/plots", exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
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

# ── 1. LOAD & MERGE DATA ──────────────────────────────────────────────────────
print("Loading data...")

players   = pd.read_csv("data/processed/players_clean.csv")
transfers = pd.read_csv("data/raw/transfers_2024_25.csv")

def parse_fee(fee):
    if pd.isna(fee): return None
    fee = str(fee).replace("€", "").strip()
    if "Loan fee:" in fee: fee = fee.replace("Loan fee:", "").strip()
    try:
        if "m" in fee: return float(fee.replace("m", "")) * 1_000_000
        if "k" in fee: return float(fee.replace("k", "")) * 1_000
    except:
        return None
    return None

transfers["fee_numeric"] = transfers["transfer_fee"].apply(parse_fee)
transfers_clean = (
    transfers.dropna(subset=["fee_numeric"])
    .sort_values("fee_numeric", ascending=False)
    .drop_duplicates(subset=["player"], keep="first")  # keep highest fee
)

df = players.merge(
    transfers_clean[["player", "fee_numeric"]],
    left_on="Player", right_on="player", how="inner"
)

print(f"   Dataset: {len(df)} players with transfer fees")

# ── 2. FEATURE ENGINEERING ────────────────────────────────────────────────────
features = [
    "Age", "MP", "Min", "Gls", "Ast", "xG", "xAG",
    "PrgC", "PrgP", "SoT", "Tkl", "Int"
]
features = [f for f in features if f in df.columns]

df_model = df[features + ["fee_numeric", "primary_position", "League"]].copy()
df_model = df_model.dropna(subset=features + ["fee_numeric"])

# Position dummies
pos_dummies = pd.get_dummies(df_model["primary_position"], prefix="pos")
df_model = pd.concat([df_model, pos_dummies], axis=1)
feature_cols = features + list(pos_dummies.columns)

X = df_model[feature_cols]
y = np.log1p(df_model["fee_numeric"])  # log transform for skewed fees

print(f"   Features: {len(feature_cols)} | Samples: {len(X)}")

# ── 3. TRAIN / TEST SPLIT ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── 4. MODELS ─────────────────────────────────────────────────────────────────
models = {
    "Linear Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression())
    ]),
    "Ridge Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=10))
    ]),
    "Random Forest": RandomForestRegressor(
        n_estimators=200, max_depth=8, random_state=42, n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42
    ),
}

print("\nModel Results:")
print(f"{'Model':<25} {'R²':>8} {'MAE (€M)':>12} {'CV R²':>10}")
print("-" * 58)

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred  = model.predict(X_test)

    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(
        np.expm1(y_test), np.expm1(y_pred)
    ) / 1_000_000

    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    cv_r2 = cv_scores.mean()

    results[name] = {
        "model": model, "r2": r2, "mae": mae,
        "cv_r2": cv_r2, "y_pred": y_pred
    }
    print(f"{name:<25} {r2:>8.3f} {mae:>11.2f}M {cv_r2:>9.3f}")

# Best model
best_name = max(results, key=lambda k: results[k]["cv_r2"])
best      = results[best_name]
print(f"\nBest model: {best_name} (CV R² = {best['cv_r2']:.3f})")

# ── 5. PLOT 1 — Actual vs Predicted ──────────────────────────────────────────
print("\nGenerating plots...")

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

y_actual    = np.expm1(y_test) / 1_000_000
y_predicted = np.expm1(best["y_pred"]) / 1_000_000

ax.scatter(y_actual, y_predicted, alpha=0.6, s=50, color="#3d85c8", zorder=2)

max_val = max(y_actual.max(), y_predicted.max()) * 1.05
ax.plot([0, max_val], [0, max_val], "--", color="#8b949e",
        linewidth=1.5, label="Perfect prediction")

# Annotate top 5 biggest errors
errors = abs(y_actual.values - y_predicted)
top5_idx = np.argsort(errors)[-5:]
test_players = df_model.iloc[y_test.index].reset_index(drop=True)
for i in top5_idx:
    try:
        name = df.iloc[y_test.index[i]]["Player"]
        ax.annotate(name, (y_actual.values[i], y_predicted[i]),
                    fontsize=7, color="white", alpha=0.85,
                    xytext=(5, 5), textcoords="offset points")
    except:
        pass

ax.set_xlabel("Actual Transfer Fee (€M)", fontsize=12)
ax.set_ylabel("Predicted Transfer Fee (€M)", fontsize=12)
ax.set_title(f"Actual vs Predicted Transfer Fee — {best_name}\n"
             f"R² = {best['r2']:.3f} | MAE = {best['mae']:.1f}M",
             fontsize=13, fontweight="bold", pad=15)
ax.legend(fontsize=10, framealpha=0.2)
fig.text(0.5, -0.02,
    "💡 Points above the dashed line are overestimated; below are underestimated — outliers often reflect non-statistical factors.",
    ha="center", fontsize=9, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/07_actual_vs_predicted.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/07_actual_vs_predicted.png")

# ── 6. PLOT 2 — Feature Importance ────────────────────────────────────────────
rf_model = results["Random Forest"]["model"]

importances = pd.Series(
    rf_model.feature_importances_, index=feature_cols
).sort_values(ascending=True).tail(12)

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

colors = ["#3d85c8" if not i.startswith("pos_") else "#c77dff"
          for i in importances.index]
ax.barh(importances.index, importances.values, color=colors, alpha=0.85)

blue_patch   = mpatches.Patch(color="#3d85c8", label="Performance stat")
purple_patch = mpatches.Patch(color="#c77dff", label="Position")
ax.legend(handles=[blue_patch, purple_patch], fontsize=9, framealpha=0.2)

ax.set_xlabel("Feature Importance", fontsize=12)
ax.set_title("Feature Importance — Random Forest\nWhat drives transfer value?",
             fontsize=13, fontweight="bold", pad=15)
fig.text(0.5, -0.02,
    "💡 Age and xG are the strongest predictors — clubs primarily pay for proven goal threat and remaining peak years.",
    ha="center", fontsize=9, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/08_feature_importance.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/08_feature_importance.png")

# ── 7. PLOT 3 — Model Comparison ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

model_names = list(results.keys())
cv_scores   = [results[m]["cv_r2"] for m in model_names]
bar_colors  = ["#ffd166" if m == best_name else "#3d85c8" for m in model_names]

bars = ax.bar(model_names, cv_scores, color=bar_colors, alpha=0.85, width=0.5)
for bar, score in zip(bars, cv_scores):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{score:.3f}", ha="center", va="bottom",
            color="white", fontsize=11, fontweight="bold")

ax.set_ylabel("Cross-Validated R²", fontsize=12)
ax.set_title("Model Comparison — 5-Fold Cross-Validated R²",
             fontsize=13, fontweight="bold", pad=15)
ax.set_ylim(0, max(cv_scores) * 1.15)
fig.text(0.5, -0.02,
    f"💡 {best_name} performs best — highlighted in gold.",
    ha="center", fontsize=9, color="#8b949e", style="italic")
plt.tight_layout()
plt.savefig("data/processed/plots/09_model_comparison.png", bbox_inches="tight")
plt.close()
print("   ✅ plots/09_model_comparison.png")

# ── 8. SUMMARY ────────────────────────────────────────────────────────────────
print(f"""
╔══════════════════════════════════════════════════════════════╗
║  Phase 3 — Market Value Model Complete!                     ║
╠══════════════════════════════════════════════════════════════╣
║  Best model : {best_name:<44} ║
║  CV R²      : {best['cv_r2']:.3f}                                         ║
║  MAE        : €{best['mae']:.1f}M                                       ║
╠══════════════════════════════════════════════════════════════╣
║  Plots:                                                     ║
║     07 — Actual vs Predicted fees                           ║
║     08 — Feature importance                                 ║
║     09 — Model comparison                                   ║
╠══════════════════════════════════════════════════════════════╣
║  Next step: Tableau Dashboard                               ║
╚══════════════════════════════════════════════════════════════╝
""")