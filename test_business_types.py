#!/usr/bin/env python3
"""Test business type filtering"""

import json
import urllib.request

test_cases = [
    ('medical', 'Medical'),
    ('restaurant', 'Restaurant'),
    ('laptop', 'Laptop/Electronics'),
    ('mobile', 'Mobile Services'),
    ('automobile', 'Automobile Repairs'),
    ('stationary', 'Stationary'),
]

base_url = 'http://localhost:8000/api/analyze'
ref_lat, ref_lon = 13.0827, 80.2707

print("=" * 60)
print("TESTING BUSINESS TYPE FILTERING")
print("=" * 60)

for business_type, business_name in test_cases:
    try:
        payload = {
            'reference_lat': ref_lat,
            'reference_lon': ref_lon,
            'search_radius_km': 5.0,
            'weights': {'rent': 0.25, 'crowd': 0.25, 'competition': 0.25, 'accessibility': 0.25},
            'business_type': business_type,
            'limit': 3,
        }
        
        req = urllib.request.Request(
            base_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode('utf-8'))
        
        if data.get('success'):
            results = data.get('results', [])
            print(f'\n{business_name}: ✅ {len(results)} locations found')
            if results:
                top = results[0]
                print(f'  Top: {top["name"]} ({top["score_percent"]}%)')
                types = top['features']['business_types']
                print(f'  Count: {types.get(business_type, 0)} {business_type} POIs')
        else:
            print(f'\n{business_name}: ❌ Error')
    except Exception as e:
        print(f'\n{business_name}: ❌ {str(e)}')

print("\n" + "=" * 60)
print("✅ Test complete")
