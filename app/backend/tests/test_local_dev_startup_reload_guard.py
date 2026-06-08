from pathlib import Path


def test_start_app_excludes_runtime_and_test_outputs_from_backend_reload():
    script = Path(__file__).resolve().parents[2] / "start_app_v2.sh"
    content = script.read_text(encoding="utf-8")

    assert "--reload" in content
    assert "--reload-exclude 'logs/*'" in content
    assert "--reload-exclude 'logs/**'" in content
    assert "--reload-exclude '__pycache__/*'" in content
    assert "--reload-exclude '__pycache__/**'" in content
    assert "--reload-exclude '.pytest_cache/*'" in content
    assert "--reload-exclude '.pytest_cache/**'" in content
    assert "--reload-exclude 'tests/*'" in content
    assert "--reload-exclude 'tests/**'" in content
    assert "Vite proxy" in content
