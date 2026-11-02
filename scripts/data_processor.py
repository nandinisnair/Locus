"""
Data Processor: Aggregates raw OSM data into locality-level features.
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
LOCALITIES_OUTPUT = Path(__file__).parent.parent / "backend" / "localities.json"
BUSINESS_TYPES = ["medical", "restaurant", "laptop", "mobile", "automobile", "stationary"]


class DataProcessor:
    def __init__(self):
        self.pois_df = None
        self.roads_df = None
        self.transit_df = None
        self.rent_df = None
        self.localities = {}
        self.grid_meta = {}

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        """Haversine distance in km between two latitude/longitude points."""
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _locate_cell_key(self, lat, lon):
        """Return cell key for a point if it falls within grid bounds, else None."""
        if not self.grid_meta:
            return None

        min_lat = self.grid_meta["min_lat"]
        min_lon = self.grid_meta["min_lon"]
        max_lat = self.grid_meta["max_lat"]
        max_lon = self.grid_meta["max_lon"]
        grid_size = self.grid_meta["grid_size"]
        n_lon = self.grid_meta["n_lon"]

        if not (min_lat <= lat < max_lat and min_lon <= lon < max_lon):
            return None

        lat_idx = int((lat - min_lat) / grid_size)
        lon_idx = int((lon - min_lon) / grid_size)
        cell_id = lat_idx * n_lon + lon_idx
        return f"cell_{cell_id:04d}"

    def _assign_cell_keys_vectorized(self, df, lat_col="lat", lon_col="lon"):
        """Assign grid cell keys to point dataframe using vectorized binning."""
        if df.empty or not self.grid_meta:
            return df

        out = df.copy()
        min_lat = self.grid_meta["min_lat"]
        min_lon = self.grid_meta["min_lon"]
        max_lat = self.grid_meta["max_lat"]
        max_lon = self.grid_meta["max_lon"]
        grid_size = self.grid_meta["grid_size"]
        n_lon = self.grid_meta["n_lon"]

        mask = (
            out[lat_col].notna()
            & out[lon_col].notna()
            & (out[lat_col] >= min_lat)
            & (out[lat_col] < max_lat)
            & (out[lon_col] >= min_lon)
            & (out[lon_col] < max_lon)
        )

        out["cell_key"] = None
        if mask.any():
            lat_idx = np.floor((out.loc[mask, lat_col].to_numpy() - min_lat) / grid_size).astype(int)
            lon_idx = np.floor((out.loc[mask, lon_col].to_numpy() - min_lon) / grid_size).astype(int)
            cell_ids = lat_idx * n_lon + lon_idx
            out.loc[mask, "cell_key"] = [f"cell_{cid:04d}" for cid in cell_ids]

        return out

    def load_data(self):
        """Load all GeoJSON and CSV datasets."""
        print("Loading datasets...")

        # Load POIs
        try:
            with open(DATA_DIR / "osm_chennai_pois.geojson", encoding="utf-8") as f:
                pois_geojson = json.load(f)
                pois_list = []
                for feature in pois_geojson.get("features", []):
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})
                    coords = geom.get("coordinates", [None, None])
                    if coords[0] is not None and coords[1] is not None:
                        pois_list.append(
                            {
                                "lon": float(coords[0]),
                                "lat": float(coords[1]),
                                "amenity": props.get("amenity"),
                                "shop": props.get("shop"),
                                "name": props.get("name", ""),
                            }
                        )
                self.pois_df = pd.DataFrame(pois_list) if pois_list else pd.DataFrame()
                print(f"  Loaded {len(self.pois_df)} POIs")
        except Exception as e:
            print(f"  Error loading POIs: {e}")
            self.pois_df = pd.DataFrame()

        # Roads are currently not consumed by ranking features.
        # Skip loading this heavy file to reduce startup cost.
        self.roads_df = pd.DataFrame()
        print("  Skipped roads dataset (not used in scoring pipeline)")

        # Load transit stops
        try:
            with open(DATA_DIR / "transit_stops.geojson", encoding="utf-8") as f:
                transit_geojson = json.load(f)
                transit_list = []
                for feature in transit_geojson.get("features", []):
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})
                    coords = geom.get("coordinates", [None, None])
                    if coords[0] is not None and coords[1] is not None:
                        transit_list.append(
                            {
                                "lon": float(coords[0]),
                                "lat": float(coords[1]),
                                "name": props.get("name", ""),
                                "type": "metro" if "railway" in props else "bus",
                            }
                        )
                self.transit_df = pd.DataFrame(transit_list) if transit_list else pd.DataFrame()
                print(f"  Loaded {len(self.transit_df)} transit stops")
        except Exception as e:
            print(f"  Error loading transit: {e}")
            self.transit_df = pd.DataFrame()

        # Load rent data
        try:
            self.rent_df = pd.read_csv(DATA_DIR / "rent_by_locality.csv")
            print(f"  Loaded {len(self.rent_df)} locality rent records")
        except Exception as e:
            print(f"  Error loading rent: {e}")
            self.rent_df = pd.DataFrame()

    def create_locality_grid(self, grid_size=0.02):
        """Create grid cells covering Chennai + southern suburbs (Potheri/Kattankulathur)."""
        print("\nCreating locality grid...")

        min_lat, min_lon = 12.70, 79.96
        max_lat, max_lon = 13.30, 80.42

        localities = {}
        cell_id = 0

        # Keep endpoint-inclusive grid dimensions to preserve existing 744-cell geometry.
        n_lat = int(round((max_lat - min_lat) / grid_size)) + 1
        n_lon = int(round((max_lon - min_lon) / grid_size)) + 1

        for lat_idx in range(n_lat):
            lat = min_lat + lat_idx * grid_size
            for lon_idx in range(n_lon):
                lon = min_lon + lon_idx * grid_size
                cell_key = f"cell_{cell_id:04d}"
                localities[cell_key] = {
                    "id": cell_id,
                    "name": f"Area {cell_id}",
                    "lat": round(lat + grid_size / 2, 4),
                    "lon": round(lon + grid_size / 2, 4),
                    "bounds": {
                        "min_lat": round(lat, 4),
                        "max_lat": round(lat + grid_size, 4),
                        "min_lon": round(lon, 4),
                        "max_lon": round(lon + grid_size, 4),
                    },
                    "poi_count": 0,
                    "amenities": 0,
                    "shops": 0,
                    "transit_stops": 0,
                    "bus_stops": 0,
                    "metro_stops": 0,
                    "business_types": {bt: 0 for bt in BUSINESS_TYPES},
                }
                cell_id += 1

        max_grid_lat = min_lat + n_lat * grid_size
        max_grid_lon = min_lon + n_lon * grid_size

        self.localities = localities
        self.grid_meta = {
            "min_lat": min_lat,
            "min_lon": min_lon,
            "max_lat": max_grid_lat,
            "max_lon": max_grid_lon,
            "grid_size": grid_size,
            "n_lat": n_lat,
            "n_lon": n_lon,
        }

        print(f"  Created {len(localities)} grid cells")
        print(f"  Lat range: {min_lat} to {round(max_grid_lat, 2)}, Lon range: {min_lon} to {round(max_grid_lon, 2)}")

    def categorize_poi_by_business_type(self, row):
        """Categorize a POI by business type."""
        amenity = str(row.get("amenity", "")).lower()
        shop = str(row.get("shop", "")).lower()

        if amenity in ["hospital", "clinic", "pharmacy", "doctors", "dentist", "blood_bank"]:
            return "medical"
        if amenity in ["restaurant", "cafe", "bar", "fast_food", "ice_cream", "food_court", "food"]:
            return "restaurant"
        if shop in ["computer", "electronics", "electrical"]:
            return "laptop"
        if shop == "mobile_phone":
            return "mobile"
        if shop in ["car_repair", "car", "motorcycle_repair", "motorcycle", "car_parts", "tyres"]:
            return "automobile"
        if shop in ["stationery", "books", "copyshop"]:
            return "stationary"

        return None

    def aggregate_pois_per_locality(self):
        """Count POIs within each locality cell by business type (vectorized)."""
        print("Aggregating POIs per locality...")

        for cell in self.localities.values():
            cell["poi_count"] = 0
            cell["amenities"] = 0
            cell["shops"] = 0
            cell["business_types"] = {bt: 0 for bt in BUSINESS_TYPES}

        if len(self.pois_df) == 0:
            print("  No POI data")
            return

        pois = self.pois_df.copy()
        pois["business_type"] = pois.apply(self.categorize_poi_by_business_type, axis=1)
        pois = self._assign_cell_keys_vectorized(pois)
        pois = pois.dropna(subset=["cell_key"])

        if pois.empty:
            print("  No POIs within configured grid")
            return

        grouped = pois.groupby("cell_key")
        for cell_key, chunk in grouped:
            if cell_key not in self.localities:
                continue
            cell = self.localities[cell_key]
            cell["poi_count"] = int(len(chunk))
            cell["amenities"] = int(chunk["amenity"].notna().sum())
            cell["shops"] = int(chunk["shop"].notna().sum())
            bt_counts = chunk["business_type"].value_counts(dropna=True).to_dict()
            cell["business_types"] = {bt: int(bt_counts.get(bt, 0)) for bt in BUSINESS_TYPES}

    def aggregate_transit_per_locality(self):
        """Count transit stops within each locality cell (vectorized)."""
        print("Aggregating transit stops per locality...")

        for cell in self.localities.values():
            cell["transit_stops"] = 0
            cell["bus_stops"] = 0
            cell["metro_stops"] = 0

        if len(self.transit_df) == 0:
            print("  No transit data")
            return

        transit = self._assign_cell_keys_vectorized(self.transit_df)
        transit = transit.dropna(subset=["cell_key"])
        if transit.empty:
            print("  No transit points within configured grid")
            return

        grouped = transit.groupby("cell_key")
        for cell_key, chunk in grouped:
            if cell_key not in self.localities:
                continue
            cell = self.localities[cell_key]
            cell["transit_stops"] = int(len(chunk))
            cell["bus_stops"] = int((chunk["type"] == "bus").sum())
            cell["metro_stops"] = int((chunk["type"] == "metro").sum())

    def map_rent_to_localities(self):
        """Map rent data to localities with confidence-aware interpolation."""
        print("Mapping rent data to localities (confidence-aware)...")

        if len(self.rent_df) == 0:
            print("  No rent data")
            return

        for cell in self.localities.values():
            cell["rent"] = None
            cell["rent_min"] = None
            cell["rent_max"] = None
            cell["rent_confidence"] = 0.0
            cell["rent_source"] = "unknown"

        keys = list(self.localities.keys())
        lats = np.array([self.localities[k]["lat"] for k in keys])
        lons = np.array([self.localities[k]["lon"] for k in keys])

        mapped_count = 0
        nearby_updates = 0

        rent_has_coords = "lat" in self.rent_df.columns and "lon" in self.rent_df.columns
        if not rent_has_coords:
            print("  Rent data has no lat/lon columns; skipping rent mapping")
            return

        for _, rent_row in self.rent_df.iterrows():
            if pd.isna(rent_row.get("lat")) or pd.isna(rent_row.get("lon")):
                continue
            if pd.isna(rent_row.get("avg_rent")):
                continue

            locality_name = str(rent_row.get("locality", "")).strip()
            avg_rent = float(rent_row["avg_rent"])
            min_rent = float(rent_row.get("min_rent", avg_rent * 0.75))
            max_rent = float(rent_row.get("max_rent", avg_rent * 1.25))
            target_lat = float(rent_row["lat"])
            target_lon = float(rent_row["lon"])

            direct_key = self._locate_cell_key(target_lat, target_lon)
            if direct_key is None:
                sq = (lats - target_lat) ** 2 + (lons - target_lon) ** 2
                nearest_idx = int(np.argmin(sq))
                direct_key = keys[nearest_idx]

            direct_cell = self.localities[direct_key]
            direct_cell["rent"] = avg_rent
            direct_cell["rent_min"] = min_rent
            direct_cell["rent_max"] = max_rent
            direct_cell["rent_confidence"] = 1.0
            direct_cell["rent_source"] = "direct"
            direct_cell["locality_name"] = locality_name
            direct_cell["name"] = locality_name or direct_cell.get("name", "Unknown")
            direct_cell["actual_lat"] = round(target_lat, 4)
            direct_cell["actual_lon"] = round(target_lon, 4)
            mapped_count += 1

            for cell in self.localities.values():
                if cell.get("rent_source") == "direct":
                    continue
                dist_km = self._haversine(target_lat, target_lon, cell["lat"], cell["lon"])
                if dist_km > 1.8:
                    continue

                candidate_conf = max(0.35, 0.75 - dist_km / 4.0)
                if candidate_conf <= float(cell.get("rent_confidence", 0.0)):
                    continue

                cell["rent"] = avg_rent * (1 + 0.04 * dist_km)
                cell["rent_min"] = min_rent
                cell["rent_max"] = max_rent
                cell["rent_confidence"] = round(candidate_conf, 3)
                cell["rent_source"] = "nearby_interpolated"
                nearby_updates += 1

        known = [
            (c["lat"], c["lon"], float(c["rent"]))
            for c in self.localities.values()
            if c.get("rent") is not None
        ]

        estimated_count = 0
        if known:
            for cell in self.localities.values():
                if cell.get("rent") is not None:
                    continue

                best_dist = float("inf")
                best_rent = None
                for rlat, rlon, rval in known:
                    dist_km = self._haversine(cell["lat"], cell["lon"], rlat, rlon)
                    if dist_km < best_dist:
                        best_dist = dist_km
                        best_rent = rval

                if best_rent is None:
                    best_rent = 50.0
                    best_dist = 12.0

                decay = max(0.65, 1.0 - (best_dist / 30.0))
                conf = max(0.12, min(0.55, 0.6 * math.exp(-best_dist / 10.0)))
                cell["rent"] = max(20.0, best_rent * decay)
                cell["rent_confidence"] = round(conf, 3)
                cell["rent_source"] = "nearest_estimate"
                estimated_count += 1

        print(f"  Directly mapped: {mapped_count} localities")
        print(f"  Nearby interpolated updates: {nearby_updates}")
        print(f"  Nearest-estimated cells: {estimated_count}")

    def assign_locality_names(self):
        """Assign real locality names to unnamed grid cells by nearest known locality."""
        print("Assigning locality names...")

        named_cells = [
            (c["lat"], c["lon"], c.get("locality_name", ""))
            for c in self.localities.values()
            if c.get("locality_name")
        ]

        unnamed_count = 0
        for cell in self.localities.values():
            if cell.get("locality_name"):
                continue

            best_dist = float("inf")
            best_name = ""
            for nlat, nlon, nname in named_cells:
                dist = ((cell["lat"] - nlat) ** 2 + (cell["lon"] - nlon) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_name = nname

            if best_name and best_dist < 0.05:
                cell["locality_name"] = f"Near {best_name}"
                cell["name"] = f"Near {best_name}"
                unnamed_count += 1
            elif best_name:
                cell["locality_name"] = f"{best_name} Outskirts"
                cell["name"] = f"{best_name} Outskirts"
                unnamed_count += 1

        still_unnamed = sum(1 for c in self.localities.values() if not c.get("locality_name"))
        print(f"  Named {unnamed_count} cells by proximity")
        print(f"  Directly named: {len(named_cells)}, Still generic: {still_unnamed}")

    def compute_competition_scores(self):
        """Compute market-strength score based on shop density."""
        print("Computing competition scores...")

        for cell in self.localities.values():
            shop_count = cell.get("shops", 0)
            cell["competition_raw"] = shop_count
            cell["competition"] = min(shop_count / 50.0, 1.0)

    def normalize_features(self):
        """Normalize all features to 0-1 range with robust clipping."""
        print("Normalizing features...")

        poi_counts = np.array([c.get("poi_count", 0) for c in self.localities.values()], dtype=float)
        rents = np.array([c.get("rent", 80) for c in self.localities.values()], dtype=float)
        transit_counts = np.array([c.get("transit_stops", 0) for c in self.localities.values()], dtype=float)

        poi_p5, poi_p95 = np.percentile(poi_counts, [5, 95]) if len(poi_counts) else (0, 1)
        rent_p5, rent_p95 = np.percentile(rents, [5, 95]) if len(rents) else (0, 1)
        transit_p5, transit_p95 = np.percentile(transit_counts, [5, 95]) if len(transit_counts) else (0, 1)

        def robust_norm(value, lo, hi):
            if hi <= lo:
                return 0.5
            clipped = min(max(float(value), lo), hi)
            return (clipped - lo) / (hi - lo)

        bt_max = {}
        for bt in BUSINESS_TYPES:
            max_count = max((c.get("business_types", {}).get(bt, 0) for c in self.localities.values()), default=0)
            bt_max[bt] = max_count

        for cell in self.localities.values():
            poi_count = cell.get("poi_count", 0)
            cell["crowd_normalized"] = round(robust_norm(poi_count, poi_p5, poi_p95), 6)

            rent = cell.get("rent", float(np.median(rents) if len(rents) else 80.0))
            rent_scaled = robust_norm(rent, rent_p5, rent_p95)
            cell["rent_normalized"] = round(1.0 - rent_scaled, 6)

            transit = cell.get("transit_stops", 0)
            cell["accessibility_normalized"] = round(robust_norm(transit, transit_p5, transit_p95), 6)
            cell["competition_normalized"] = round(min(max(cell.get("competition", 0), 0.0), 1.0), 6)

            bt_counts = cell.get("business_types", {})
            active_types = sum(1 for bt in BUSINESS_TYPES if bt_counts.get(bt, 0) > 0)
            cell["business_diversity"] = round(active_types / len(BUSINESS_TYPES), 6)

            for bt in BUSINESS_TYPES:
                count = float(bt_counts.get(bt, 0))
                max_count = bt_max.get(bt, 0)
                if max_count <= 0:
                    cell[f"{bt}_normalized"] = 0.0
                    continue
                denom = math.log1p(max_count)
                cell[f"{bt}_normalized"] = round(math.log1p(count) / denom, 6)

    def save_localities(self):
        """Save processed localities to JSON."""
        print("\nSaving processed localities...")

        output = {"localities": self.localities, "count": len(self.localities)}
        with open(LOCALITIES_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"  Saved {len(self.localities)} localities")

    def run(self):
        """Execute pipeline."""
        print("=" * 60)
        print("DATA PROCESSING PIPELINE")
        print("=" * 60)

        self.load_data()
        self.create_locality_grid(grid_size=0.02)
        self.aggregate_pois_per_locality()
        self.aggregate_transit_per_locality()
        self.compute_competition_scores()
        self.map_rent_to_localities()
        self.assign_locality_names()
        self.normalize_features()
        self.save_localities()

        named = sum(1 for c in self.localities.values() if c.get("locality_name"))
        with_rent = sum(1 for c in self.localities.values() if c.get("rent") is not None)
        direct_rent = sum(1 for c in self.localities.values() if c.get("rent_source") == "direct")
        print("\nData processing complete")
        print(f"   Total cells: {len(self.localities)}")
        print(f"   Named cells: {named}")
        print(f"   Cells with rent: {with_rent}")
        print(f"   Direct rent cells: {direct_rent}")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()
