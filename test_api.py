import json
import urllib.request
import sys

url = "http://localhost:8000/api/analyze"
data = {
    "reference_lat": 13.0062,
    "reference_lon": 80.2433,
    "search_radius_km": 5.0,
    "weights": {
        "rent": 0.25,
        "crowd": 0.25,
        "competition": 0.25,
        "accessibility": 0.25
    },
    "limit": 5
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read().decode("utf-8"))
    print(json.dumps(result, indent=2))
    print("\n✅ API working! Got", len(result.get("results", [])), "ranked locations")
except Exception as e:
    print("❌ Error:", e)
    sys.exit(1)
