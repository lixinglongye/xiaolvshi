from main import api_health_check, app, health_check


def test_api_health_alias_matches_root_health_without_startup():
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/health" in paths
    assert "/api/v1/health" in paths
    assert health_check() == {"status": "healthy"}
    assert api_health_check() == health_check()
