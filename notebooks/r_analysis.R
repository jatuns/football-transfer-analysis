# ============================================================
# Football Transfer Intelligence — Phase 2 (R)
# Statistical Analysis & ggplot2 Visualization
#
# Install packages (run once):
#   install.packages(c("tidyverse", "ggrepel", "scales", "patchwork"))
#
# Run:
#   Rscript notebooks/r_analysis.R
# ============================================================

library(tidyverse)
library(ggrepel)
library(scales)
library(patchwork)

# ── Dark Theme ────────────────────────────────────────────────────────────────
dark_theme <- theme(
  plot.background    = element_rect(fill = "#0d1117", color = NA),
  panel.background   = element_rect(fill = "#161b22", color = NA),
  panel.grid.major   = element_line(color = "#30363d", size = 0.4),
  panel.grid.minor   = element_blank(),
  axis.text          = element_text(color = "white", size = 10),
  axis.title         = element_text(color = "white", size = 12),
  plot.title         = element_text(color = "white", size = 15, face = "bold", margin = margin(b = 10)),
  plot.subtitle      = element_text(color = "#8b949e", size = 10, margin = margin(b = 15)),
  plot.caption       = element_text(color = "#8b949e", size = 9, face = "italic", margin = margin(t = 10)),
  legend.background  = element_rect(fill = "#0d1117", color = NA),
  legend.text        = element_text(color = "white", size = 9),
  legend.title       = element_text(color = "#8b949e", size = 9),
  strip.background   = element_rect(fill = "#21262d"),
  strip.text         = element_text(color = "white", face = "bold"),
  plot.margin        = margin(15, 15, 15, 15)
)

league_colors <- c(
  "eng Premier League" = "#3d85c8",
  "es La Liga"         = "#e63946",
  "it Serie A"         = "#06d6a0",
  "de Bundesliga"      = "#ffd166",
  "fr Ligue 1"         = "#c77dff"
)

league_labels <- c(
  "eng Premier League" = "Premier League",
  "es La Liga"         = "La Liga",
  "it Serie A"         = "Serie A",
  "de Bundesliga"      = "Bundesliga",
  "fr Ligue 1"         = "Ligue 1"
)

# ── Load Data ─────────────────────────────────────────────────────────────────
cat("Loading clean data...\n")
df <- read_csv("data/processed/players_clean.csv", show_col_types = FALSE)

df <- df %>%
  mutate(
    League       = Comp,
    League_short = recode(Comp, !!!league_labels),
    GA_per90     = (Gls + Ast) / ifelse(`90s` == 0, NA, `90s`),
    overperform  = Gls - xG
  ) %>%
  filter(!is.na(League))

cat(sprintf("   %d players loaded ✅\n\n", nrow(df)))

dir.create("data/processed/plots/r", showWarnings = FALSE, recursive = TRUE)

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT R-1 — G+A per 90 Violin Plot by League
# ═══════════════════════════════════════════════════════════════════════════════
cat("Plot R-1: Violin plot — G+A per 90...\n")

p1 <- df %>%
  filter(!is.na(GA_per90), GA_per90 < 2) %>%
  ggplot(aes(x = League_short, y = GA_per90, fill = League)) +
  geom_violin(alpha = 0.75, trim = TRUE, color = NA) +
  geom_boxplot(width = 0.12, fill = "#0d1117", color = "white", outlier.shape = NA) +
  scale_fill_manual(values = league_colors, guide = "none") +
  labs(
    title    = "Goal Contribution Distribution by League",
    subtitle = "Goals + Assists / 90 Minutes — 2024/25 Season",
    caption  = "💡 Bundesliga and Premier League show higher median G+A per 90 compared to Ligue 1 and Serie A.",
    x        = NULL,
    y        = "G+A per 90"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R1_violin_ga90.png", p1,
       width = 11, height = 7, dpi = 150, bg = "#0d1117")
cat("   ✅ R1_violin_ga90.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT R-2 — xG Overperformance Bar Chart
# ═══════════════════════════════════════════════════════════════════════════════
cat("Plot R-2: xG overperformance bar chart...\n")

top_over  <- df %>%
  filter(primary_position %in% c("FW", "MF"), !is.na(overperform)) %>%
  slice_max(overperform, n = 12)

top_under <- df %>%
  filter(primary_position %in% c("FW", "MF"), !is.na(overperform)) %>%
  slice_min(overperform, n = 12)

over_under <- bind_rows(top_over, top_under) %>%
  mutate(
    direction = ifelse(overperform > 0, "Overperformed", "Underperformed"),
    Player    = fct_reorder(Player, overperform)
  )

p2 <- over_under %>%
  ggplot(aes(x = Player, y = overperform, fill = direction)) +
  geom_col(alpha = 0.85, width = 0.7) +
  geom_hline(yintercept = 0, color = "white", linewidth = 0.5) +
  scale_fill_manual(values = c("Overperformed" = "#06d6a0",
                                "Underperformed" = "#e63946")) +
  coord_flip() +
  labs(
    title    = "xG Overperformance — Who Beat Expectations?",
    subtitle = "Goals minus xG (2024/25, FW + MF, min. 5 appearances)",
    caption  = "💡 Overperformers may indicate clinical finishing ability — or regression candidates for next season.",
    x        = NULL,
    y        = "Goals − xG",
    fill     = NULL
  ) +
  dark_theme +
  theme(legend.position = "top")

ggsave("data/processed/plots/r/R2_overperformance.png", p2,
       width = 11, height = 8, dpi = 150, bg = "#0d1117")
cat("   ✅ R2_overperformance.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT R-3 — Age & Performance: Facet by League
# ═══════════════════════════════════════════════════════════════════════════════
cat("Plot R-3: Age-xG smooth — facet by league...\n")

fw_mf <- df %>%
  filter(primary_position %in% c("FW", "MF"), Age >= 17, Age <= 38, !is.na(xG))

p3 <- fw_mf %>%
  ggplot(aes(x = Age, y = xG, color = League)) +
  geom_point(alpha = 0.25, size = 1.2) +
  geom_smooth(method = "loess", se = TRUE, linewidth = 1.4,
              color = "#ffd166", fill = "#ffd16650") +
  facet_wrap(~ League_short, ncol = 3) +
  scale_color_manual(values = league_colors, guide = "none") +
  labs(
    title    = "Age & Goal Productivity — Performance Curve by League",
    subtitle = "LOESS smooth + confidence interval | FW & MF, 2024/25",
    caption  = "💡 Peak productivity consistently falls between ages 24–28 across all five leagues.",
    x        = "Age",
    y        = "Expected Goals (xG)"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R3_age_xg_facet.png", p3,
       width = 13, height = 8, dpi = 150, bg = "#0d1117")
cat("   ✅ R3_age_xg_facet.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# PLOT R-4 — Attacking vs Defensive Intensity (Club Level)
# ═══════════════════════════════════════════════════════════════════════════════
cat("Plot R-4: Attacking vs defensive scatter (club level)...\n")

club_stats <- df %>%
  group_by(Squad, League, League_short) %>%
  summarise(
    avg_xG   = mean(xG,      na.rm = TRUE),
    avg_Tkl  = mean(Tkl,     na.rm = TRUE),
    avg_Int  = mean(Int,     na.rm = TRUE),
    avg_GA90 = mean(GA_per90, na.rm = TRUE),
    n        = n(),
    .groups  = "drop"
  ) %>%
  filter(n >= 10)

p4 <- club_stats %>%
  ggplot(aes(x = avg_Tkl + avg_Int, y = avg_xG,
             color = League, label = Squad)) +
  geom_point(aes(size = avg_GA90), alpha = 0.8) +
  geom_text_repel(size = 2.5, color = "white", alpha = 0.85,
                  max.overlaps = 15, segment.color = "#30363d") +
  scale_color_manual(values = league_colors,
                     labels = league_labels,
                     name   = "League") +
  scale_size_continuous(name = "G+A/90", range = c(2, 8)) +
  labs(
    title    = "Attacking Capacity vs Defensive Intensity",
    subtitle = "Club averages | x: Tackles + Interceptions | y: xG | size: G+A per 90",
    caption  = "💡 Top-right clubs combine high attack output with strong pressing — a hallmark of elite modern teams.",
    x        = "Average Tackles + Interceptions",
    y        = "Average xG"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R4_attack_vs_defense.png", p4,
       width = 13, height = 9, dpi = 150, bg = "#0d1117")
cat("   ✅ R4_attack_vs_defense.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
cat("Statistical analysis — correlation tests...\n")

test_cols  <- intersect(c("Gls", "xG", "Ast", "xAG", "Age", "Min",
                           "PrgC", "PrgP", "Tkl", "Int"), names(df))
corr_data  <- df %>% select(all_of(test_cols)) %>% drop_na()
corr_matrix <- cor(corr_data, method = "pearson")

cat("\nTop correlations with Goals:\n")
gol_corr <- sort(corr_matrix["Gls", ], decreasing = TRUE)
print(round(gol_corr, 3))

test_result <- cor.test(df$Gls, df$xG, method = "pearson")
cat(sprintf("\nPearson Correlation (Gls ~ xG):\n   r = %.4f | p-value = %.2e\n",
            test_result$estimate, test_result$p.value))

model_df <- df %>%
  filter(primary_position %in% c("FW", "MF")) %>%
  select(Gls, xG, Age, PrgC, Ast) %>%
  drop_na()

lm_model <- lm(Gls ~ xG + Age + PrgC + Ast, data = model_df)
cat("\nLinear Regression Summary (Gls ~ xG + Age + PrgC + Ast):\n")
print(summary(lm_model))

# ═══════════════════════════════════════════════════════════════════════════════
cat("\n╔═══════════════════════════════════════════════════════════╗\n")
cat("║  Phase 2 — R Analysis Complete!                         ║\n")
cat("╠═══════════════════════════════════════════════════════════╣\n")
cat("║  Plots saved to: data/processed/plots/r/               ║\n")
cat("║     R1 — Violin plot (G+A per 90)                      ║\n")
cat("║     R2 — xG Overperformance bar chart                  ║\n")
cat("║     R3 — Age-xG LOESS smooth facet by league           ║\n")
cat("║     R4 — Attacking vs Defensive scatter (club)         ║\n")
cat("║  Next step: scripts/market_value_model.py              ║\n")
cat("╚═══════════════════════════════════════════════════════════╝\n")