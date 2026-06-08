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


def test_start_app_keeps_vite_proxy_aligned_with_selected_backend_port():
    script = Path(__file__).resolve().parents[2] / "start_app_v2.sh"
    frontend_config = Path(__file__).resolve().parents[2] / "frontend" / "vite.config.ts"

    script_content = script.read_text(encoding="utf-8")
    vite_content = frontend_config.read_text(encoding="utf-8")

    assert 'export VITE_API_PROXY_TARGET="http://127.0.0.1:$BACKEND_PORT"' in script_content
    assert 'export VITE_BACKEND_PROXY_TARGET="$VITE_API_PROXY_TARGET"' in script_content
    assert 'export VITE_PORT="$FRONTEND_PORT"' in script_content
    assert "wait_for_frontend_home" in script_content
    assert "Frontend Loopback URL: http://127.0.0.1:$FRONTEND_PORT" in script_content
    assert "without a port is not this Vite app" in script_content
    assert "process.env.VITE_API_PROXY_TARGET" in vite_content
    assert "process.env.VITE_BACKEND_PROXY_TARGET" in vite_content
    assert "process.env.BACKEND_PORT || '8000'" in vite_content
    assert "`http://127.0.0.1:${backendProxyPort}`" in vite_content
    assert "target: apiProxyTarget" in vite_content
