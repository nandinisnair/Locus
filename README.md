# Locus Copilot

> **Location Intelligence & Business Site Selection System for Chennai**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Leaflet](https://img.shields.io/badge/Map-Leaflet.js-brightgreen?logo=leaflet)](https://leafletjs.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What Is Locus Copilot?

Locus Copilot is a **full-stack location intelligence web application** built for Chennai, India. It helps entrepreneurs, retailers, and investors identify optimal commercial locations to open new businesses using real OpenStreetMap geospatial data and classical Decision Science models.

No black-box ML. No opaque algorithms. Pure **transparent, explainable, mathematically verified** spatial economics.

---

## Problem Statement

Business owners in Chennai face a high-stakes spatial decision problem across four conflicting criteria:

| Criterion | Goal |
|---|---|
| Affordability (Rent) | Low commercial overhead |
| Crowd Density (Footfall) | High customer traffic |
| Market Strength (Competition) | Validated demand or market gap |
| Transit Accessibility | Convenient customer and employee access |

These criteria **conflict**: a prime commercial corridor (such as T. Nagar) has dense footfall but premium rent, whereas peripheral suburban nodes offer low rent but lower immediate footfall. Locus Copilot resolves these trade-offs through **data-driven multi-criteria analysis**.

---

## Features

- **Interactive Spatial Map** — Dynamic Leaflet.js visualization with color-coded ranked location markers across Chennai.
- **Custom Weight Sliders** — Real-time interactive adjustment of Affordability, Crowd, Competition, and Transit accessibility priorities.
- **Preset Decision Profiles** — Instant scenarios: Balanced, Budget-Oriented, Foot Traffic-Oriented, and Low Competition.
- **Business Type Profiles** — Tailored scoring profiles for Medical, Restaurant, Laptop/Electronics, Mobile Services, Automobile, and Stationery.
- **5 Decision Science Models** — Saaty's AHP, Hwang & Yoon's TOPSIS, David Huff's Retail Gravity, Christaller's Central Place Theory, and MAUT.
- **Data Quality & Coverage Indicators** — Spatial candidate count, data source confidence metrics, and confidence level per query radius.
- **Authentication & User Profiles** — Token-based registration and authentication using JWT (HS256) and PBKDF2-SHA256 password hashing.
- **User Dashboard** — Manage saved search history, custom weight presets, and bookmarked candidate locations.
- **Administrative Panel** — System usage statistics, account management, and user controls.
- **Dual-Theme Design System** — Tailored Executive Class light theme and Obsidian Glass dark theme.
- **Data Export** — Export analyzed location rankings to CSV.
- **Responsive Architecture** — Seamless mobile, tablet, and desktop browser experience.

---

## Decision Science Models

### 1. AHP — Analytic Hierarchy Process *(Saaty, 1980)*
Derives mathematically consistent criterion weights from expert pairwise comparison matrices. Computes Principal Eigenvalue ($\lambda_{\text{max}}$), Consistency Index ($CI$), and verifies Consistency Ratio ($CR < 0.10$).

### 2. TOPSIS — Technique for Order Preference by Similarity to Ideal Solution *(Hwang & Yoon, 1981)*
Re-ranks top locations by Euclidean distance to the Positive Ideal Solution ($A^+$) and Negative Ideal Solution ($A^-$). Closeness coefficient: $C_i = \frac{S^-}{S^+ + S^-}$.

### 3. Huff Retail Gravity Model *(David Huff, 1963)*
Estimates customer catchment probability distributions: $P_j = \frac{A_j \cdot d_j^{-\lambda}}{\sum_k A_k \cdot d_k^{-\lambda}}$, with distance friction exponent $\lambda$ adjusted by business trip frequency.

### 4. Christaller Central Place Theory *(Walter Christaller, 1933)*
Classifies locality cells into 5 functional urban orders — from Regional Commercial Core (Order 1) to Residential/Emerging Zone (Order 5) — based on goods hierarchy, transit nodes, and retail density.

### 5. MAUT — Multi-Attribute Utility Theory
Calibrates individual utility functions from historical searches and favorites to recommend unvisited high-utility localities: $U(x) = \sum_i w_i \cdot u_i(x)$.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.10+, FastAPI, Uvicorn |
| Decision Science | Pure Python, NumPy (AHP, TOPSIS, Huff, Central Place, MAUT) |
| Geospatial & Data | Pandas, NumPy, GeoJSON |
| Security & Auth | PyJWT (HS256), passlib (PBKDF2-SHA256) |
| Storage | SQLite (Relational store for users, searches, favorites) |
| Frontend | Vanilla JavaScript (ES6+), HTML5, CSS3 |
| Mapping | Leaflet.js, OpenStreetMap cartography |
| Data Ingestion | OpenStreetMap Overpass POIs, transit stops, surveyed locality rent |

---

## Project Structure

```
Locus_Copilot/
├── backend/
│   ├── main.py               # FastAPI application & API endpoints
│   ├── scoring_engine.py     # Multi-criteria decision analysis (MCDA) engine
│   ├── decision_science.py   # AHP, TOPSIS, Huff Gravity, Central Place, MAUT
│   ├── database.py           # SQLite schema, users, searches, favorites
│   ├── auth.py               # JWT token creation and verification
│   └── localities.json       # Preprocessed 300+ locality grid data
├── frontend/
│   ├── landing.html          # Public overview and features page
│   ├── login.html            # User authentication
│   ├── register.html         # User registration
│   ├── index.html            # Core geospatial analysis application
│   ├── dashboard.html        # User searches, preferences, and favorites
│   ├── admin.html            # System statistics and user management
│   └── theme.css             # Cohesive dual-theme design system
├── scripts/
│   └── data_processor.py     # OSM and rent dataset aggregation ETL pipeline
├── tests/
│   ├── test_api_contract.py  # API schema, data quality, and endpoint tests
│   ├── test_dashboard_rendering.py # Dashboard DOM structure and parsing tests
│   └── test_decision_science.py   # AHP consistency, TOPSIS, and Huff model tests
├── data/                     # Geospatial GeoJSON and CSV datasets
├── requirements.txt          # Python dependency specifications
└── README.md                 # Technical documentation
```

---

## Setup & Run

### Prerequisites
- Python 3.10+
- pip
- Modern web browser with internet connection (for OpenStreetMap tiles)

### Step 1 — Clone the repository
```bash
git clone https://github.com/nandinisnair/Locus.git
cd Locus
```

### Step 2 — Create and activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Launch backend service
```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Step 5 — Launch frontend service
```powershell
# In a separate terminal session
cd frontend
python -m http.server 8080
```

### Step 6 — Access the application
Navigate to:
```
http://localhost:8080/landing.html
```

*Note for Windows users:* Execute `START.bat` to initialize both services simultaneously.

---

## Default Administrative Account

```
Email:    admin@locuscopilot.com
Password: admin123
```

---

## API Specifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health status |
| GET | `/api/localities` | List candidate locality cells |
| GET | `/api/criteria` | Multi-criteria definitions and default weights |
| POST | `/api/analyze` | Execute spatial MCDA analysis |
| GET | `/api/analyze/preset/{name}` | Execute analysis with predefined weight profile |
| POST | `/api/auth/register` | Register new user account |
| POST | `/api/auth/login` | Authenticate user and receive JWT bearer token |
| GET | `/api/user/profile` | Current user profile details |
| GET | `/api/user/searches` | Historical searches for authenticated user |
| GET | `/api/user/favorites` | Saved favorite locations |
| GET | `/api/decision-science/ahp-weights/{type}` | AHP weights and consistency metrics by business type |
| GET | `/api/decision-science/central-places` | Christaller hierarchy order summary |
| GET | `/api/decision-science/recommendations` | Personalized recommendations via MAUT |
| GET | `/api/admin/stats` | Platform operational statistics (Admin only) |
| GET | `/api/admin/users` | Platform user directory (Admin only) |

Interactive Swagger documentation available at: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Scoring Formulation

$$\text{Final Score} = \left[ \sum_{i} \left( w_i \times \text{normalized}_i \right) \right] \times \text{confidence\_factor} + \text{support\_bonus} + \text{type\_signal\_bonus} + \text{mode\_bonus} - \text{low\_presence\_penalty}$$

* Attribute normalization employs robust 5th–95th percentile clipping to eliminate outlier distortion.
* Business-type density signals utilize log1p transformations to handle skewed commercial cluster distributions.

---

## Data Sources

| Dataset | Format | Source | Description |
|---|---|---|---|
| Chennai POIs | GeoJSON | OpenStreetMap (Overpass API) | Commercial amenities, dining, medical, and retail |
| Transit Stops | GeoJSON | OpenStreetMap | Metro stations and bus stops |
| Locality Rent | CSV | Local real estate survey data | Commercial rental benchmarks (₹ / sq.ft) |

---

## Design System

- **Executive Class (Light Mode — Default):** Warm cream canvas (`#fffcf7`), forest/sage tones (`#5b7f6e`), and warm gold accents (`#c49b5c`).
- **Obsidian Glass (Dark Mode):** Deep charcoal slate (`#1c1c1e`), luminous sage (`#7faa96`), and gold accents (`#d4a95e`).
- Persistent theme toggle backed by browser `localStorage`.
- Fluid transitions and clean typography.

---

## Troubleshooting

**Backend Connection Issues:**
- Ensure the FastAPI server is running on port 8000.
- Verify status via `http://localhost:8000/health`.

**Map Tiles Not Displaying:**
- Ensure active internet connectivity for OpenStreetMap tile fetching.
- Ensure the frontend is served over HTTP (`http://localhost:8080`), not via local `file://` protocol.

**Session Expiration:**
- JWT bearer tokens expire in 24 hours. Log in again if receiving HTTP 401 Unauthorized responses.

**Port Conflict Resolution:**
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

---

## Author

**Nandini S Nair**  
[GitHub Profile](https://github.com/nandinisnair)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
