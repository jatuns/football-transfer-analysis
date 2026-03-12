# ⚽ Football Transfer Intelligence

End-to-end data analysis project exploring transfer spending, player market values, and financial efficiency across Europe's Big 5 leagues (2024/25 season).

## 🎯 Key Questions
- Which clubs get the best value from transfer spending?
- What factors influence a player's market value?
- Is there a correlation between transfer budget and performance?

## 🛠️ Tech Stack
| Tool | Purpose |
|------|---------|
| PostgreSQL | Database design & storage |
| Python (Pandas, Matplotlib, Seaborn, Scikit-learn) | Data collection, cleaning, visualization & ML |
| R (ggplot2, dplyr, tidyverse) | Statistical analysis & visualization |
| Tableau | Interactive dashboard |

## 📁 Project Structure
```
football-transfer-analysis/
├── data/
│   ├── raw/                    # Raw CSV files (gitignored)
│   └── processed/
│       ├── players_clean.csv   # Cleaned player stats
│       ├── tableau_data.csv    # Merged data for Tableau
│       └── plots/              # All generated visualizations
│           └── r/              # R-generated plots
├── sql/
│   ├── create_tables.sql       # Database schema (6 tables)
│   └── analysis_queries.sql    # Analysis queries
├── scripts/
│   ├── load_data.py            # Load CSVs into PostgreSQL
│   ├── scrape_transfers.py     # Scrape Transfermarkt data
│   ├── analysis.py             # Python visualizations (6 plots)
│   └── market_value_model.py   # ML market value prediction
├── notebooks/
│   └── r_analysis.R            # R statistical analysis (4 plots)
└── dashboard/
    └── football_transfer_dashboard.twb   # Tableau workbook
```

## 📊 Data Sources
- **Player statistics**: FBref via Kaggle (2,854 players, 5 leagues, 2024/25)
- **Transfer data**: Transfermarkt — scraped with Selenium/BeautifulSoup (339 transfers, summer 2024 + winter 2025)

## 🚀 How to Run

### 1. Database Setup
```bash
psql -U postgres -c "CREATE DATABASE football_transfers;"
psql -U postgres -d football_transfers -f sql/create_tables.sql
python3 scripts/load_data.py
```

### 2. Scrape Transfer Data
```bash
python3 scripts/scrape_transfers.py
```

### 3. Python Analysis
```bash
pip3 install pandas matplotlib seaborn scipy scikit-learn psycopg2-binary
python3 scripts/analysis.py
python3 scripts/market_value_model.py
```

### 4. R Analysis
```r
install.packages(c("tidyverse", "ggrepel", "scales", "patchwork"))
Rscript notebooks/r_analysis.R
```

## 📈 Analysis Highlights

### Goals Distribution by League
![Goals by League](data/processed/plots/01_goals_by_league.png)

### xG vs Actual Goals
![xG vs Goals](data/processed/plots/02_xg_vs_goals.png)

### Top 20 Most Efficient Clubs
![Club Efficiency](data/processed/plots/03_club_efficiency.png)

### Age & Performance Curve
![Age xG Curve](data/processed/plots/04_age_xg_curve.png)

### Progressive Carries by Position
![PrgC by Position](data/processed/plots/05_prgc_by_position.png)

### Correlation Matrix
![Correlation](data/processed/plots/06_correlation_matrix.png)

### Market Value Model — Actual vs Predicted
![Model](data/processed/plots/07_actual_vs_predicted.png)

### Feature Importance
![Feature Importance](data/processed/plots/08_feature_importance.png)

## 🔬 Key Findings
- **xG reliability**: xG and actual goals correlation r = **0.93** — xG is a highly reliable performance metric
- **Peak productivity**: Goal output peaks at **ages 24–28** consistently across all five leagues
- **Transfer spending**: Premier League clubs outspend all other leagues — over **2x** the next highest (Bundesliga)
- **Market value model**: R² = **0.16** — statistical performance alone explains only 16% of transfer fees, highlighting the significant role of non-statistical factors (brand value, contract length, club need, media market)
- **Efficiency leaders**: PSG and Nice lead G+A per 90 — Bundesliga dominates the top 20 most efficient clubs

## 📊 Interactive Dashboard
> 🔗 Tableau Public: *coming soon*

Features:
- Click a league in the bar chart → all views filter automatically
- Dropdown league filter
- Transfer spending vs performance bubble chart (size = goals scored)
