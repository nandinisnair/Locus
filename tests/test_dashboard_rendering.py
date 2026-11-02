from pathlib import Path


def test_dashboard_contains_render_targets_and_null_safe_mappings():
    dashboard_path = Path("frontend/dashboard.html")
    html = dashboard_path.read_text(encoding="utf-8")

    # Integration baseline: required render containers exist
    assert 'id="searchesList"' in html
    assert 'id="preferencesList"' in html
    assert 'id="favoritesList"' in html

    # Contract: dashboard normalizes backend schema fields
    assert "function normalizeSearchRecord" in html
    assert "search_radius" in html
    assert "latitude" in html
    assert "longitude" in html

    # Contract: favorites rendering is null-safe for coordinates
    assert "function formatCoord" in html
    assert "formatCoord(f.latitude)" in html
    assert "formatCoord(f.longitude)" in html
