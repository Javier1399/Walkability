
# Urban Vitality Simulator — Walkability Analysis for Mexican Cities

> **An urban intelligence platform that transforms raw geospatial indicators into actionable intervention strategies for city planners and researchers.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Research Context

Mexico's rapid urbanization demands new tools for evaluating urban quality of life. Metropolitan areas frequently follow dispersed, vehicle-oriented development patterns that leave pedestrians underserved — particularly in peripheral zones.

This project replicates and extends the methodology from *"Walkable Southeast Asia: A Comparative Study Between Phnom Penh and Ho Chi Minh City"*, adapting it to the Mexican urban context. It integrates **Spatial Data Science**, **unsupervised machine learning**, and **interactive simulation** to evaluate pedestrian accessibility at micro-scale across Mexican metropolitan areas.

**Pilot cities:** Atitalaquia (Hidalgo) and Guanajuato (Guanajuato)  
**Collaboration:** [Universidad de Texas en San Antonio (UTSA)](https://www.utsa.edu/) — comparative analysis between Monterrey and San Antonio  
**Project lead:** Francisco Javier Benita Maldonado  
**Technical development:** Francisco Javier Romero Santos (Tecnológico de Monterrey, Querétaro Campus)

> ⚠️ All pipeline development, modeling decisions, and dashboard implementation documented in this repository were developed independently by the repository author.

---

## Central Research Question

> *"What makes a city walkable — and how can we identify the minimum intervention needed to improve urban mobility in any given zone?"*

We began with raw geospatial indicators and no predetermined use. The challenge was to transform those numbers into an understanding of **how a city organizes itself spatially**, which zones share behavioral patterns, and — critically — **which specific interventions would produce the greatest improvement in pedestrian accessibility at the lowest cost.**

This question drove every methodological decision in the pipeline.

---

## 🚀 Live Dashboard

> 🔗 **[Launch Urban Vitality Simulator →](https://movility-nvq2bcvt9w5keywfkjf8ze.streamlit.app/)**

The dashboard works like **SimCity meets urban research**: select a city, explore its walkability zones, identify areas ready for intervention, and simulate the impact of adding a park, a food market, or improving street connectivity — all grounded in real geospatial data and a trained optimization model.

### What you can do in the dashboard:

- **Explore** the city through a 2D hexagonal map colored by walkability score or urban archetype
- **Filter** by zone classification (consolidated core, transitional, peripheral, excluded) to focus your analysis
- **Diagnose** any zone: see its median walk times to food, healthcare, education, and leisure
- **Simulate** interventions: choose an intervention type (e.g. "Add food service"), set coverage percentage, and see the projected improvement in walk score, population impacted, and how many hexagons could transition to a better urban cluster
- **Compare** both cities side-by-side on walkability distributions and RIM classification breakdowns

---

## Dashboard Tabs

### ⬡ Map of Opportunities
The main view shows all hexagons colored by their **RIM v4 classification** — a seven-level system that tells you immediately which zones are consolidated, which are transitioning, and which suffer from territorial exclusion. A right panel shows the diagnostic profile of any selected zone, including walk times, intervention recommendation, and the minimum threshold values needed to transition to the next urban cluster.

### ⚡ Intervention Simulator
Select a zone from the sidebar, choose an intervention type, and set coverage. The simulator shows:
- Projected walk score improvement (based on RIM v4 sensitivity analysis deltas)
- Before/after walk time chart — **only the categories affected by the chosen intervention change**, reflecting the real urbanistic logic (adding a food market reduces food access time, not healthcare time)
- Population impacted and number of hexagons that could cross the cluster frontier

### Strategic Analysis
Side-by-side histograms comparing walk score and info gap distributions across both cities, a grouped bar chart of RIM classification proportions, and a comparative KPI table.

---

## 🗂️ Repository Structure

```
urban-vitality-simulator/
│
├── README.md                          # This file
├── LICENSE
├── requirements.txt                   # Dark theme configuration
│
├── app.py                             # Streamlit dashboard (main entry point)
│
├── data/
│   ├── Atitalaquia_urban_analysis_final.gpkg   # Final output — 422 hexagons
│   ├── Guanajuato_urban_analysis_final.gpkg    # Final output — 29,023 hexagons
│
├── notebooks/
│   └── dashboard_walkability.ipynb    # Full analysis pipeline (Google Colab)
│
├── docs/
│   └── images/
│       ├── pca_scree_plot.png
│       ├── clusters_atitalaquia.png
│       ├── clusters_guanajuato.png
│       ├── walk_score_map.png
│       ├── rim_classification_map.png
│       └── dashboard_screenshot.png
│
└── 
```

---

## Full Pipeline — From Raw Data to Urban Intelligence

### Phase 0 — Starting Point

We received two GeoPackage files containing **hexagonal grid cells** covering the full metropolitan extent of Atitalaquia and Guanajuato. Each hexagon has a radius of approximately **250 meters** — the right scale for pedestrian analysis, since it captures what a person can access within a short walk.

Each hexagon contained raw indicators calculated from two independent sources:

| Source | Coverage | Strength | Weakness |
|--------|----------|----------|---------|
| **INEGI** (Instituto Nacional de Estadística y Geografía) | Official Mexican government cartography | Authoritative, standardized | May lag behind new developments |
| **OpenStreetMap (OSM)** | Community-contributed global map | Captures recent infrastructure, commercial activity | Uneven coverage across zones |

The raw columns for each service category (food, healthcare, education, leisure) included:
- `dist_to_X` — distance to nearest OSM point of interest (meters)
- `dist_to_X_inegi` — distance to nearest INEGI point of interest (meters)
- `X_osm_count_1_2km` — count of OSM amenities within 1.2km radius
- `X_inegi_count_1_2km` — count of INEGI amenities within 1.2km radius

Plus road network indicators: `average_link_length_1_2km`, `intersection_density_ge3_1_2km`, `cul_de_sac_ratio_1_2km`, `network_density_1_2km`.

---

### Phase 1 — Data Fusion: Integrating INEGI and OSM

**The problem:** INEGI and OSM often disagreed on both distances and counts for the same zone. Simply ignoring one source would discard valuable information; using them independently would double-count everything.

**The approach:** We treated INEGI as the authoritative baseline (it follows official Mexican standards), but recognized that OSM sometimes captures commercial activity, newer infrastructure, or informal spaces that INEGI misses. The fusion logic:

```python
def process_point_4(df):
    for cat in ['food', 'healthcare', 'educational', 'leisure']:
        # Distance: take the minimum — the closest real access point wins
        df[f'dist_{cat}_combined'] = df[[f'dist_to_{cat}',
                                         f'dist_to_{cat}_inegi']].min(axis=1)
        # Count: take the maximum — whichever source detected more activity
        df[f'{cat}_count_combined'] = df[[f'{cat}_osm_count_1_2km',
                                          f'{cat}_inegi_count_1_2km']].max(axis=1)

    # Info Gap: how much do the two sources disagree?
    df['info_gap'] = abs(mean(dist_OSM_cols) - mean(dist_INEGI_cols))
    return df
```

**Why this works:** If OSM shows a food market 200m away that INEGI doesn't register, the combined distance is 200m — the pedestrian reality. The `info_gap` variable captures the magnitude of disagreement between sources, which we later use as a **data confidence penalty** in the walk score: zones where OSM and INEGI strongly disagree get a slightly discounted score to flag that the measurement is less certain.

This is not just a data cleaning step — `info_gap` became one of the 15 features in the initial PCA, reflecting the "digital visibility gap" between formal cartography and community-contributed data.

---

### Phase 2 — Exploratory Analysis

With 422 hexagons in Atitalaquia and 29,023 in Guanajuato, we ran correlation analysis (Spearman, more robust for skewed distributions) to understand which variables moved together.

Key findings from the correlation heatmaps:
- Distance variables clustered together (if you're far from food, you're probably far from healthcare too)
- Count variables also clustered, but separately from distances
- Road network variables formed a distinct group
- `info_gap` showed weak correlation with most indicators, confirming it captures something genuinely different

This guided the PCA feature selection.

---

### Phase 3 — PCA: Revealing the City's Hidden Structure

**Why PCA?** We had 15 variables per hexagon. Directly clustering in 15 dimensions is computationally expensive and prone to the curse of dimensionality — distances between points become less meaningful as dimensions grow. More importantly, many variables were correlated, meaning they conveyed redundant information.

PCA finds the directions of maximum variance in the data — the axes along which hexagons differ most from each other. By projecting 15 dimensions onto 5 principal components, we retained **87.6% of the total variance** while enabling clean 2D visualization and more robust clustering.

```python
pca = PCA(n_components=0.85)  # Retain 85% of variance
X_pca = pca.fit_transform(X_scaled)
# Result: 5 components explaining [47.3%, 20.4%, 7.2%, 6.8%, 5.9%]
```

**What PC1 captured (47.3% of variance):** The urban density gradient. High intersection density, high population, high service counts — all loaded positively. High distances loaded negatively. PC1 is essentially a score of *"how urban is this hexagon?"*

**The V-shape discovery:** When plotted in PC1 vs PC2 space, the data revealed a characteristic **V-shape** that is well-documented in urban spatial data. This shape emerges naturally when a city has a dense core surrounded by gradually dispersing periphery — the two "arms" of the V represent different types of peripheral zones (one with partial services, one truly isolated). This confirmed that the data contained meaningful spatial structure worth clustering.

**Initial PCA (v1) included all 15 variables, including healthcare and educational counts.** This later caused problems in the intervention recommender (see Phase 6) and led to a redesign.

---

### Phase 4 — K-Means Clustering: Discovering Urban Archetypes

With the data projected into PCA space, we applied K-Means clustering. We tested k=3, 4, and 5. **k=4 was selected for policy interpretability** — four distinct urban archetypes that correspond to recognizable urban planning categories:

| Cluster | Label | Profile | Walk Score (median) |
|---------|-------|---------|---------------------|
| 0 | **Periferia semi-urbana** | Food ~5km away, intersection density ~8.4/km², population ~430 | ~0.24 |
| 1 | **Núcleo urbano denso** | Food ~275m, intersection density ~247/km², population ~27,121 | ~0.80 |
| 2 | **Periferia rural extrema** | Food ~18km, almost no services, population ~74 | ~0.13 |
| 3 | **Zona periurbana** | Food ~650m, intermediate connectivity, population ~9,290 | ~0.55 |

**Global silhouette score: 0.389** — indicating meaningful cluster separation. Notably, Cluster 1 (urban core) achieved a silhouette of 0.597, confirming that the city center is clearly distinguishable from all other zones.

When mapped back to the hexagonal grid, the clusters aligned perfectly with what you'd expect geographically: the urban core concentrated in the historic center, periurban zones forming the intermediate ring, and peripheral clusters extending to the city limits and beyond. **The algorithm had learned the city's spatial structure without ever seeing its geography** — only the indicator values.

---

### Phase 5 — Sub-clustering: Structure Within Structure

Cluster 0 (periferia semi-urbana) showed an unusually high tail in its walk score distribution. Investigation revealed that two fundamentally different types of zones had been grouped together:

- **0A — Red conectada sin servicios:** Good road network (short links, dense intersections) but no nearby services. These are likely residential subdivisions built with proper street infrastructure but lacking commercial and amenity development. Walk score elevated by connectivity despite zero accessibility.
- **0B — Periferia desarticulada:** Poor road network AND no services. True disconnected periphery.

A secondary K-Means (k=2, silhouette=0.534) on connectivity and accessibility features confirmed the split. This distinction matters practically: **0A zones are viable candidates for service-based interventions**, while 0B zones need both infrastructure AND services — a much more expensive proposition.

The five resulting sub-archetypes, when mapped, followed the expected geographic order from city center outward — validating that the sub-clustering captured real urban structure.

---

### Phase 6 — Walk Score: Giving Every Hexagon a Mobility Value

To evaluate and compare zones, we needed a single composite score that captured the pedestrian experience of each hexagon. Inspired by commercial walkability indices but adapted for the Mexican data structure and scale:

#### Accessibility Score (weight: 65%)

For each service category (food, healthcare, education, leisure):

```
score_dist_X   = exp(-distance / 400)         # Exponential decay: 400m threshold
score_count_X  = log1p(count) / log1p(P95)    # Logarithmic saturation
score_access_X = 0.4 × score_dist + 0.6 × score_count
```

**Why exponential decay?** The difference between 200m and 600m to a service is enormous behaviorally. The difference between 2km and 3km is negligible — the pedestrian won't walk either. The 400m threshold captures this non-linearity.

**Why logarithmic counts?** Going from 0 to 1 food option is a transformational change. Going from 15 to 16 barely matters. The log function compresses the scale appropriately.

#### Connectivity Score (weight: 35%)

```
norm_intersec = intersection_density / P95(intersection_density)
norm_link     = 1 - (link_length / P95(link_length))   # Shorter = better
norm_cul      = 1 - cul_de_sac_ratio                   # Fewer dead ends = better
connectivity  = mean(norm_intersec, norm_link, norm_cul)
```

Road network quality matters independently of services. A well-connected street grid enables walking even when destinations are slightly farther, while cul-de-sacs and long blocks actively discourage pedestrian movement.

#### Confidence Factor (multiplicative)

```
confidence = 1 - 0.3 × (info_gap / P95(info_gap))
```

Maximum 30% penalty when OSM and INEGI strongly disagree. The score isn't zeroed out — it's flagged as uncertain. This is honest data communication.

#### Walking Times

```
walk_time_X = dist_X_combined / 75    # 75 meters/minute = 4.5 km/h standard
```

Categories: Very accessible (<5 min) / Accessible (5-10) / Moderate (10-20) / Low (20-45) / Not walkable (>45 min)

#### Temporal Coverage Index (ICT)

```
ICT = number of categories with walk_time ≤ 20 minutes   # Integer 0–4
```

A hexagon with ICT=4 has all four service types within 20 minutes walking. ICT=0 means nothing is reachable on foot within 20 minutes.

---

### Phase 7 — PCA v2 and the Institutional Bias Problem

When we implemented the first version of the intervention recommender (RIM v1), it overwhelmingly recommended "increase healthcare density" for almost every hexagon. The cause: `healthcare_count_combined` had a high loading on PC1 (0.32), which explained 47% of variance. The recommender was finding the mathematically shortest path through PCA space, and that path always went through healthcare.

**This was urbanistically incorrect.** Healthcare facilities (hospitals, clinics) are institutional, government-planned, and require years of planning and significant investment. Walkability is built bottom-up: first good street networks, then commercial activity (food, leisure) emerges organically, and institutional services follow consolidated urbanization — not the other way around.

**Solution: PCA v2** — retrained without healthcare and educational variables:

```python
FEATURES_V2 = [
    'dist_food_combined', 'dist_leisure_combined',
    'food_count_combined', 'leisure_count_combined',
    'average_link_length_1_2km', 'intersection_density_ge3_1_2km',
    'cul_de_sac_ratio_1_2km', 'network_density_1_2km',
    'amenity_diversity_inegi', 'population_count_1_2km', 'info_gap'
]
```

**Result:** PC1 in v2 is now led by `intersection_density` (0.436) and `population_count` (0.433) — genuine organic urban density. The sensitivity analysis confirmed: **road connectivity now has 6× more impact than food accessibility** in moving a hexagon toward the urban cluster target. The four-archetype cluster structure survived the redesign intact, validating that the original clusters were real, not artifacts of the institutional variables.

Silhouette dropped slightly (0.389 → 0.356) — an acceptable tradeoff for an urbanistically honest recommender.

---

### Phase 8 — RIM v4: The Minimum Intervention Recommender

**The key insight that made RIM necessary:** When we tested the recommender on all peripheral hexagons, every single one came back as "requires major intervention" with near-zero viability scores. This wasn't a bug — it was the data telling us something important.

**Mexican urban discontinuity:** The cluster separation is high (silhouette ~0.35-0.39) precisely because Mexican urban conditions are discontinuous. There is no gradual gradient from periphery to core; there are structural jumps — zones with everything, zones with nothing, separated by barriers that cannot be crossed with marginal changes. **This is quantified urban segregation.**

Trying to optimize hexagons in the deep core of a peripheral cluster is like trying to minimize a function by walking in the wrong direction. The approach needed to be more targeted.

**The frontera_score:** For each peripheral hexagon, we calculated:

```
frontera_score = dist_to_own_cluster_centroid / dist_to_target_cluster_centroid
```

A score near 1.0 means the hexagon is equidistant between its current cluster and the target — it's on the frontier. A score near 0 means it's deep in its cluster core. **Only hexagons in the top 25% (P75) of frontera_score are viable intervention candidates.**

**Sensitivity analysis for frontier hexagons:** For each candidate, we simulate individual variable changes (add 10 intersections/km², reduce food distance by 30%, add 5 food venues, etc.) and measure how much each change moves the hexagon toward the target cluster centroid in PCA v2 space. The variable with the highest delta becomes the recommended intervention.

**RIM v4 classification system:**

| Classification | Description | Typical profile |
|---------------|-------------|-----------------|
| **Consolidado** | Urban core — no intervention needed | Cluster 1 |
| **En desarrollo** | Periurban — already transitioning | Cluster 3 |
| **Transición viable** | Frontier, viability ≥ 0.7 | 0A hexagons near cluster 3 boundary |
| **Transición con esfuerzo** | Frontier, viability 0.4-0.7 | Moderate investment needed |
| **Fronterizo estructural** | On frontier but difficult to move | < 0.4 viability |
| **Núcleo de periferia** | Deep in peripheral cluster | Major policy needed |
| **Exclusión territorial** | Rural extreme — no walkable access | Cluster 2 |

**Key finding — Guanajuato territorial exclusion:** 14.5% of hexagons (4,215 cells) have a median walk time to the nearest service of **193 minutes** — over 3 hours walking to food, healthcare, or any amenity. This is not a walkability problem; it's territorial exclusion documented mathematically.

---

## 📐 Data Dictionary

Full column definitions for the `.gpkg` output files:

| Column | Type | Description |
|--------|------|-------------|
| `geometry` | Polygon | Hexagonal cell geometry (EPSG:4326) |
| `id` | int | Unique hexagon identifier |
| `NOMGEO` / `CVE_*` | str/int | INEGI administrative codes |
| `dist_X_combined` | float | Min(OSM, INEGI) distance to service X (meters) |
| `X_count_combined` | float | Max(OSM, INEGI) count of service X in 1.2km |
| `info_gap` | float | Mean absolute discrepancy between OSM and INEGI distances |
| `average_link_length_1_2km` | float | Mean street segment length in 1.2km radius (meters) |
| `intersection_density_ge3_1_2km` | float | Intersections with ≥3 roads per km² |
| `cul_de_sac_ratio_1_2km` | float | Proportion of dead-end streets [0,1] |
| `network_density_1_2km` | float | Total street length / area |
| `amenity_diversity_inegi` | float | Shannon entropy of INEGI amenity types [0,1] |
| `population_count_1_2km` | float | Population in 1.2km radius (not city total — see note) |
| `cluster_v2` | int | K-Means cluster assignment (PCA v2) |
| `cluster_v2_label` | str | Human-readable cluster archetype |
| `subcluster` | str | Sub-classification within cluster 0 |
| `walk_score` | float | Composite walkability score [0,1] |
| `accessibility_score` | float | Service accessibility component [0,1] |
| `connectivity_score` | float | Road network component [0,1] |
| `confidence` | float | Data reliability factor [0.7,1.0] |
| `walk_time_X` | float | Minutes walking to nearest service X |
| `walk_time_nearest` | float | Minutes to nearest service of any type |
| `timecat_X` | str | Categorical time level for service X |
| `ICT` | int | Temporal Coverage Index: services reachable in ≤20 min [0,4] |
| `ICT_label` | str | Human-readable ICT category |
| `frontera_score` | float | Proximity to cluster frontier (null for non-candidates) |
| `viability_score` | float | RIM viability [0,1] (null for non-candidates) |
| `viability_label` | str | Alto potencial / Potencial medio / Requiere intervención mayor |
| `grupo_dominante` | str | Red vial / Activación comercial |
| `intervencion_1` | str | Primary recommended intervention |
| `intervencion_2` | str | Secondary recommended intervention |
| `rim_clasificacion` | str | Seven-level RIM zone classification |
| `pc1_v2` / `pc2_v2` / `pc3_v2` | float | PCA v2 coordinates for visualization |

> **Note on `population_count_1_2km`:** This is the population within a 1.2km radius around each hexagon's center — not the hexagon's exclusive population. Since hexagons overlap at this radius, summing across all hexagons severely overcounts. Use the median or mean per hexagon as the interpretable metric.

---

## 🔑 Key Findings

1. **Urban discontinuity is structural, not incidental.** The high cluster separation in both cities reflects that Mexican urban conditions don't transition gradually — they jump. This is quantified spatial segregation.

2. **14.5% of Guanajuato hexagons face territorial exclusion** — median walking time to the nearest service of any type is 193 minutes. Infrastructure investment here is a matter of basic accessibility, not walkability optimization.

3. **The urban core delivers.** 92.8% of Cluster 1 hexagons (urban core) are "Very accessible" — the nearest service is under 5 minutes walking. The system works when it's built right.

4. **Institutional variables (healthcare, education) don't drive walkability.** They follow urbanization; they don't create it. Using them as intervention targets produces mathematically optimal but urbanistically impossible recommendations.

5. **Road connectivity is the foundation.** In PCA v2, improving intersection density has 6× more impact than adding food services on moving a hexagon toward the periurban cluster. Streets first, destinations second.

6. **OSM and INEGI diverge meaningfully.** The `info_gap` distribution differs substantially between cities, reflecting real differences in how well each data source captures urban activity at different scales.

---

## 🛠️ Installation & Local Run

```bash
# Clone the repository
git clone https://github.com/your-username/urban-vitality-simulator.git
cd urban-vitality-simulator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The `.gpkg` data files must be placed in a `data/` folder:
```
data/
├── Atitalaquia_urban_analysis_final.gpkg
└── Guanajuato_urban_analysis_final.gpkg
```

---

## 📦 Requirements

```
streamlit>=1.32.0
geopandas>=0.14.0
pydeck>=0.8.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
```

---

## 📓 Notebook

The full analysis pipeline is documented in [`notebooks/dashboard_walkability.ipynb`](notebooks/dashboard_walkability.ipynb), designed to run in **Google Colab**. The notebook covers:

1. Data loading and exploratory analysis
2. OSM + INEGI data fusion (`process_point_4`)
3. PCA v1 — initial dimensionality reduction with all 15 variables
4. K-Means clustering and geographic validation
5. Sub-clustering of Cluster 0 (0A vs 0B)
6. Walk Score computation (`compute_walk_score`)
7. Walking time metrics and ICT index
8. PCA v2 — redesigned without institutional variables
9. RIM v4 — frontier score, sensitivity analysis, and intervention recommendations
10. Final consolidation and export

> The notebook uses Google Colab's AI assistant (Gemini) as a code generation tool, with all analytical decisions made and validated by the researcher.

---

## Reproducibility

The analysis was designed for reproducibility. All pipeline parameters are documented in `data/pipeline_metadata_v4.json`, including:
- Feature list for PCA v2
- Number of PCA components and variance explained
- K-Means k value and cluster role assignments
- Walk score weights and decay parameters
- RIM v4 frontier percentile threshold and target cluster

New cities can be analyzed by generating hexagonal grid indicators in the same format and running the pipeline.

---

## 📝 Citation

If you use this work in your research, please cite:

```
Francisco Javier Romero Santos, "Urban Vitality Simulator: Walkability Analysis and 
Intervention Optimization for Mexican Cities," Tecnológico de Monterrey, 
Querétaro Campus, 2025. Available: https://github.com/your-username/urban-vitality-simulator
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Part of a broader initiative to evaluate walkability across 48 Mexican metropolitan areas, in collaboration with the Universidad de Texas en San Antonio (UTSA).*
