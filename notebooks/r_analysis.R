# ============================================================
# Football Transfer Intelligence — Aşama 2 (R)
# İstatistiksel Analiz & ggplot2 Görselleştirme
#
# Kurulum (bir kez çalıştır):
#   install.packages(c("tidyverse", "ggrepel", "scales", "patchwork", "corrplot"))
#
# Çalıştır:
#   Rscript notebooks/r_analysis.R
# ============================================================

library(tidyverse)
library(ggrepel)
library(scales)
library(patchwork)

# ── Temalar ──────────────────────────────────────────────────────────────────
dark_theme <- theme(
  plot.background    = element_rect(fill = "#0d1117", color = NA),
  panel.background   = element_rect(fill = "#161b22", color = NA),
  panel.grid.major   = element_line(color = "#30363d", size = 0.4),
  panel.grid.minor   = element_blank(),
  axis.text          = element_text(color = "white", size = 10),
  axis.title         = element_text(color = "white", size = 12),
  plot.title         = element_text(color = "white", size = 15, face = "bold", margin = margin(b = 10)),
  plot.subtitle      = element_text(color = "#8b949e", size = 10, margin = margin(b = 15)),
  legend.background  = element_rect(fill = "#0d1117", color = NA),
  legend.text        = element_text(color = "white", size = 9),
  legend.title       = element_text(color = "#8b949e", size = 9),
  strip.background   = element_rect(fill = "#21262d"),
  strip.text         = element_text(color = "white", face = "bold"),
  plot.margin        = margin(15, 15, 15, 15)
)

lig_renkleri <- c(
  "eng Premier League" = "#3d85c8",
  "es La Liga"         = "#e63946",
  "it Serie A"         = "#06d6a0",
  "de Bundesliga"      = "#ffd166",
  "fr Ligue 1"         = "#c77dff"
)

lig_kisaltma <- c(
  "eng Premier League" = "Premier League",
  "es La Liga"         = "La Liga",
  "it Serie A"         = "Serie A",
  "de Bundesliga"      = "Bundesliga",
  "fr Ligue 1"         = "Ligue 1"
)

# ── Veriyi Oku ───────────────────────────────────────────────────────────────
cat("📂 Temiz veri okunuyor...\n")
df <- read_csv("data/processed/players_clean.csv", show_col_types = FALSE)

df <- df %>%
  mutate(
    Lig         = Comp,
    Lig_kisa    = recode(Comp, !!!lig_kisaltma),
    GA_per90    = (Gls + Ast) / ifelse(`90s` == 0, NA, `90s`),
    overperform = Gls - xG
  ) %>%
  filter(!is.na(Lig))

cat(sprintf("   %d oyuncu yüklendi ✅\n\n", nrow(df)))

dir.create("data/processed/plots/r", showWarnings = FALSE, recursive = TRUE)

# ═══════════════════════════════════════════════════════════════════════════════
# GRAFİK R-1 — Lig Başına Gol+Asist Violin Plot
# ═══════════════════════════════════════════════════════════════════════════════
cat("📊 Grafik R-1: Violin plot — G+A per 90...\n")

p1 <- df %>%
  filter(!is.na(GA_per90), GA_per90 < 2) %>%
  ggplot(aes(x = Lig_kisa, y = GA_per90, fill = Lig)) +
  geom_violin(alpha = 0.75, trim = TRUE, color = NA) +
  geom_boxplot(width = 0.12, fill = "#0d1117", color = "white", outlier.shape = NA) +
  scale_fill_manual(values = lig_renkleri, guide = "none") +
  labs(
    title    = "Lig Başına Gol Katkısı Dağılımı",
    subtitle = "Gol + Asist / 90 Dakika — 2024/25 Sezonu",
    x        = NULL,
    y        = "G+A per 90"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R1_violin_ga90.png", p1,
       width = 11, height = 7, dpi = 150, bg = "#0d1117")
cat("   ✅ R1_violin_ga90.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# GRAFİK R-2 — xG Overperformance: Kim beklentiyi aştı?
# ═══════════════════════════════════════════════════════════════════════════════
cat("📊 Grafik R-2: xG overperformance bar chart...\n")

top_over  <- df %>% filter(ana_pozisyon %in% c("FW", "MF"), !is.na(overperform)) %>%
  slice_max(overperform, n = 12)
top_under <- df %>% filter(ana_pozisyon %in% c("FW", "MF"), !is.na(overperform)) %>%
  slice_min(overperform, n = 12)

over_under <- bind_rows(top_over, top_under) %>%
  mutate(
    direction = ifelse(overperform > 0, "Beklentiyi Aştı", "Beklentinin Altında"),
    Player = fct_reorder(Player, overperform)
  )

p2 <- over_under %>%
  ggplot(aes(x = Player, y = overperform, fill = direction)) +
  geom_col(alpha = 0.85, width = 0.7) +
  geom_hline(yintercept = 0, color = "white", linewidth = 0.5) +
  scale_fill_manual(values = c("Beklentiyi Aştı" = "#06d6a0",
                                "Beklentinin Altında" = "#e63946")) +
  coord_flip() +
  labs(
    title    = "xG Overperformance — Kim Beklentiyi Aştı?",
    subtitle = "Gol - xG farkı (2024/25, FW + MF, min. 5 maç)",
    x        = NULL,
    y        = "Gol − xG",
    fill     = NULL
  ) +
  dark_theme +
  theme(legend.position = "top")

ggsave("data/processed/plots/r/R2_overperformance.png", p2,
       width = 11, height = 8, dpi = 150, bg = "#0d1117")
cat("   ✅ R2_overperformance.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# GRAFİK R-3 — Yaş & Performans: Lig Başına Facet
# ═══════════════════════════════════════════════════════════════════════════════
cat("📊 Grafik R-3: Yaş-xG smooth — lig bazlı facet...\n")

fw_mf <- df %>%
  filter(ana_pozisyon %in% c("FW", "MF"), Age >= 17, Age <= 38, !is.na(xG))

p3 <- fw_mf %>%
  ggplot(aes(x = Age, y = xG, color = Lig)) +
  geom_point(alpha = 0.25, size = 1.2) +
  geom_smooth(method = "loess", se = TRUE, linewidth = 1.4, color = "#ffd166", fill = "#ffd16650") +
  facet_wrap(~ Lig_kisa, ncol = 3) +
  scale_color_manual(values = lig_renkleri, guide = "none") +
  labs(
    title    = "Yaş & Gol Üretkenliği — Lig Bazlı Performans Eğrisi",
    subtitle = "LOESS smooth + güven aralığı | FW & MF, 2024/25",
    x        = "Yaş",
    y        = "Beklenen Gol (xG)"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R3_yas_xg_facet.png", p3,
       width = 13, height = 8, dpi = 150, bg = "#0d1117")
cat("   ✅ R3_yas_xg_facet.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# GRAFİK R-4 — Hücum vs Savunma Scatter (Kulüp Bazlı)
# ═══════════════════════════════════════════════════════════════════════════════
cat("📊 Grafik R-4: Hücum vs savunma scatter (kulüp)...\n")

kulup_stats <- df %>%
  group_by(Squad, Lig, Lig_kisa) %>%
  summarise(
    avg_xG    = mean(xG, na.rm = TRUE),
    avg_Tkl   = mean(Tkl, na.rm = TRUE),
    avg_Int   = mean(Int, na.rm = TRUE),
    avg_GA90  = mean(GA_per90, na.rm = TRUE),
    n         = n(),
    .groups   = "drop"
  ) %>%
  filter(n >= 10)

p4 <- kulup_stats %>%
  ggplot(aes(x = avg_Tkl + avg_Int, y = avg_xG, color = Lig, label = Squad)) +
  geom_point(aes(size = avg_GA90), alpha = 0.8) +
  geom_text_repel(size = 2.5, color = "white", alpha = 0.85,
                  max.overlaps = 15, segment.color = "#30363d") +
  scale_color_manual(values = lig_renkleri,
                     labels = lig_kisaltma,
                     name   = "Lig") +
  scale_size_continuous(name = "G+A/90", range = c(2, 8)) +
  labs(
    title    = "Hücum Kapasitesi vs Savunma Yoğunluğu",
    subtitle = "Kulüp ortalamaları | x: Müdahale+Top Kesme | y: xG | nokta büyüklüğü: G+A/90",
    x        = "Ortalama Müdahale + Top Kesme",
    y        = "Ortalama xG"
  ) +
  dark_theme

ggsave("data/processed/plots/r/R4_hucum_savunma.png", p4,
       width = 13, height = 9, dpi = 150, bg = "#0d1117")
cat("   ✅ R4_hucum_savunma.png\n")

# ═══════════════════════════════════════════════════════════════════════════════
# GRAFİK R-5 — İstatistiksel Özet: Korelasyon Testi + Yorumlama
# ═══════════════════════════════════════════════════════════════════════════════
cat("📊 İstatistiksel analiz — korelasyon testleri...\n")

test_cols <- c("Gls", "xG", "Ast", "xAG", "Age", "Min", "PrgC", "PrgP", "Tkl", "Int")
test_cols <- intersect(test_cols, names(df))
corr_data <- df %>% select(all_of(test_cols)) %>% drop_na()

corr_matrix <- cor(corr_data, method = "pearson")

cat("\n📌 Gol ile en yüksek korelasyonlu değişkenler:\n")
gol_corr <- sort(corr_matrix["Gls", ], decreasing = TRUE)
print(round(gol_corr, 3))

# Pearson testi — Gls ~ xG
test_result <- cor.test(df$Gls, df$xG, method = "pearson")
cat(sprintf("\n🔬 Pearson Korelasyon (Gls ~ xG):\n   r = %.4f | p-value = %.2e\n",
            test_result$estimate, test_result$p.value))

# Linear model — Gls ~ xG + Age + PrgC
model_df <- df %>%
  filter(ana_pozisyon %in% c("FW", "MF")) %>%
  select(Gls, xG, Age, PrgC, PrgP, Ast) %>%
  drop_na()

lm_model <- lm(Gls ~ xG + Age + PrgC + Ast, data = model_df)
cat("\n📐 Linear Regression Özeti (Gls ~ xG + Age + PrgC + Ast):\n")
print(summary(lm_model))

# ═══════════════════════════════════════════════════════════════════════════════
cat("\n╔═══════════════════════════════════════════════════════════╗\n")
cat("║  Aşama 2 — R Analizi Tamamlandı!                        ║\n")
cat("╠═══════════════════════════════════════════════════════════╣\n")
cat("║  📁 Grafikler: data/processed/plots/r/                  ║\n")
cat("║     R1 — Violin plot (G+A per 90)                       ║\n")
cat("║     R2 — xG Overperformance bar chart                   ║\n")
cat("║     R3 — Yaş-xG smooth facet (lig bazlı)               ║\n")
cat("║     R4 — Hücum vs Savunma scatter (kulüp)              ║\n")
cat("║  📌 Sonraki adım: scripts/market_value_model.py         ║\n")
cat("╚═══════════════════════════════════════════════════════════╝\n")