# 🗺️ Locus Copilot

> **Location Intelligence & Business Site Selection System for Chennai**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Leaflet](https://img.shields.io/badge/Map-Leaflet.js-brightgreen?logo=leaflet)](https://leafletjs.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📌 What Is Locus Copilot?

Locus Copilot is a **full-stack location intelligence web application** built for Chennai, India. It helps entrepreneurs, retailers, and investors identify the **best commercial locations** to open a new business — using real OpenStreetMap geospatial data and classical Decision Science models.

No black-box ML. No opaque algorithms. Just **transparent, explainable, mathematically verified** spatial economics.

---

## 🧩 Problem Statement

Business owners in Chennai face a high-stakes spatial decision problem across four conflicting criteria:

| Criterion | Goal |
|-----------|------|
| 💰 Rent | Affordable overhead |
| 👥 Footfall | High customer traffic |
| 🏪 Competition | Market gap or validated demand |
| 🚌 Transit | Accessible location |

These criteria **conflict** — a prime T. Nagar spot has massive footfall but sky-high rent. A quiet OMR suburb is cheap but empty. Locus Copilot solves this trade-off with **data-driven multi-criteria analysis**.

---

## ✨ Features

- 🗺️ **Interactive Leaflet Map** — Color-coded ranked location markers across Chennai
- ⚖️ **Custom Weight Sliders** — Tune Rent / Crowd / Competition / Accessibility priorities in real time
- 🏷️ **Preset Profiles** — Balanced, Budget, Foot Traffic, Low Competition
- 🏢 **Business Type Filtering** — Medical, Restaurant, Laptop, Mobile, Automobile, Stationary
- 🔬 **5 Decision Science Models** — AHP, TOPSIS, Huff Gravity, Central Place Theory, MAUT
- 📊 **Data Quality Indicator** — Shows confidence score and coverage % per search area
- 👤 **User Authentication** — Register / Login with JWT tokens
- 📁 **Dashboard** — Saved searches, preferences, favorite locations
- 🛡️ **Admin Panel** — User management and system statistics
- 🌙 **Dark / Light Theme** — Warm sage-green & gold design system
- 📥 **Export CSV** — Download analysis results
- 📱 **Responsive Design** — Works on desktop and mobile

---

## 🧠 Decision Science Models

### 1. AHP — Analytic Hierarchy Process *(Saaty, 1980)*
Derives mathematically consistent criterion weights from expert pairwise comparison matrices. Computes Principal Eigenvalue (λ_max), Consistency Index (CI), and verifies Consistency Ratio (CR < 0.10).

### 2. TOPSIS — Technique for Order Preference by Similarity to Ideal Solution *(Hwang & Yoon, 1981)*
Re-ranks top locations by Euclidean distance to the Positive Ideal Solution (A⁺) and Negative Ideal Solution (A⁻). Closeness coefficient C_i = S⁻ / (S⁺ + S⁻).

### 3. Huff Retail Gravity Model *(David Huff, 1963)*
Estimates probabilistic customer catchment area: P_j = (A_j × d_j^−λ) / Σ(A_k × d_k^−λ). Travel friction exponent λ varies by business trip purpose.

### 4. Christaller Central Place Theory *(Walter Christaller, 1933)*
Classifies every locality cell into 5 functional urban orders — from Regional CBD to Residential/Emerging Zone — based on retail threshold and transit connectivity.

### 5. MAUT — Multi-Attribute Utility Theory
Builds a personalized utility function from your own search history. Recommends unvisited high-utility localities using empirical preference weights: U(x) = Σ w_i · u_i(x).

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Decision Science | Pure Python + NumPy (AHP, TOPSIS, Huff, Central Place, MAUT) |
| Data Processing | Pandas, NumPy |
| Auth | PyJWT (HS256), passlib (PBKDF2-SHA256) |
| Database | SQLite |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Map | Leaflet.js + OpenStreetMap tiles |
| Data Sources | OSM GeoJSON (POIs, Transit), CSV (Rent by locality) |

---

## 📁 Project Structure

```
Locus_Copilot/
├── backend/
│   ├── main.py               # FastAPI app — all API endpoints
│   ├── scoring_engine.py     # Weighted MCDA scoring engine
│   ├── decision_science.py   # AHP, TOPSIS, Huff Gravity, Central Place, MAUT
│   ├── database.py           # SQLite — users, searches, favorites
│   ├── auth.py               # JWT token creation and verification
│   └── localities.json       # Pre-processed 300+ locality grid
├── frontend/
│   ├── landing.html          # Public landing page
│   ├── login.html            # User login
│   ├── register.html         # User registration
│   ├── index.html            # Main analysis app (map + controls + results)
│   ├── dashboard.html        # User dashboard
│   ├── admin.html            # Admin panel
│   └── theme.css             # Design system (light/dark themes)
├── scripts/
│   └── data_processor.py     # OSM → locality grid ETL pipeline
├── data/                     # Raw GeoJSON and CSV datasets
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.9+
- pip
- Modern browser with internet (for map tiles)

### Step 1 — Clone the repo
```bash
git clone https://github.com/nandinisnair/Locus.git
cd Locus
```

### Step 2 — Create virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Start the backend
```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Step 5 — Start the frontend
```powershell
# Open a new terminal
cd frontend
python -m http.server 8080
```

### Step 6 — Open in browser
```
http://localhost:8080/landing.html
```

> **Windows users:** You can also double-click `START.bat` to launch everything automatically.

---

## 🔑 Default Admin Account

```
Email:    admin@locuscopilot.com
Password: admin123
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/localities` | All 300+ localities |
| GET | `/api/criteria` | Criterion metadata |
| POST | `/api/analyze` | Run weighted MCDA analysis |
| GET | `/api/analyze/preset/{name}` | Run with preset weights |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT |
| GET | `/api/user/profile` | User profile |
| GET | `/api/user/searches` | Search history |
| GET | `/api/user/favorites` | Saved favorites |
| GET | `/api/decision-science/ahp-weights/{type}` | AHP weights + CR for business type |
| GET | `/api/decision-science/central-places` | Christaller hierarchy summary |
| GET | `/api/decision-science/recommendations` | MAUT personalized recommendations |
| GET | `/api/admin/stats` | System statistics (admin only) |
| GET | `/api/admin/users` | User list (admin only) |

Interactive API docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 📐 Scoring Formula

```
Score = Σ (w_i × normalized_i) × confidence_factor
      + support_bonus          (business-profile fit, 15%)
      + type_signal_bonus      (market presence signal, 12–16%)
      + mode_bonus             (competition mode fit, 8–10%)
      - low_presence_penalty   (if demand-following and zero existing shops)
```

All features normalized to [0, 1] using robust percentile scaling (P5–P95). Business type signals use log1p normalization to handle skewed shop count distributions.

---

## 🗂️ Data Sources

| Dataset | Format | Source |
|---------|--------|--------|
| Chennai POIs | GeoJSON | OpenStreetMap Overpass API |
| Transit Stops | GeoJSON | OpenStreetMap |
| Rent by Locality | CSV | Public locality rent estimates |

---

## 🎨 Design System

- **Light theme** — Cream (`#fffcf7`), sage green (`#5b7f6e`), gold (`#c49b5c`)
- **Dark theme** — Dark gray (`#1c1c1e`), lighter sage (`#7faa96`), warm gold (`#d4a95e`)
- Smooth CSS page transitions
- Theme preference persisted in localStorage

---

## 🛠️ Troubleshooting

**"API Error" when analyzing**
→ Make sure backend is running on port 8000. Check uvicorn terminal for errors.

**Map tiles not loading**
→ Requires internet connection. Serve frontend via `http://`, not `file://`.

**"Unauthorized" errors**
→ JWT may have expired. Log out and log back in.

**Port already in use**
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
```

---

## 👩‍💻 Author

**Nandini S Nair**  
[github.com/nandinisnair](https://github.com/nandinisnair)

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
