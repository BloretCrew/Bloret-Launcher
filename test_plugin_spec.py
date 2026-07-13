import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "docs" / "plugin-spec.json"


def _load_module(name, relative_path):
    """Load a plugin_host module without importing the package side effects."""
    if "modules" not in sys.modules:
        modules_pkg = types.ModuleType("modules")
        modules_pkg.__path__ = [str(ROOT / "modules")]
        sys.modules["modules"] = modules_pkg
    if "modules.log" not in sys.modules:
        log_mod = types.ModuleType("modules.log")
        log_mod.log = lambda *args, **kwargs: None
        sys.modules["modules.log"] = log_mod
    if "modules.plugin_host" not in sys.modules:
        host_pkg = types.ModuleType("modules.plugin_host")
        host_pkg.__path__ = [str(ROOT / "modules" / "plugin_host")]
        sys.modules["modules.plugin_host"] = host_pkg

    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def test_plugin_spec_permissions_match_runtime():
    permissions_mod = _load_module(
        "modules.plugin_host.permissions",
        "modules/plugin_host/permissions.py",
    )
    spec = _load_spec()
    permissions = spec["permissions"]
    assert set(permissions) == permissions_mod.ALL_PERMISSIONS
    assert {
        name for name, details in permissions.items() if details["risk"] == "high"
    } == permissions_mod.HIGH_RISK_PERMISSIONS


def test_plugin_spec_hooks_match_runtime():
    hooks_mod = _load_module(
        "modules.plugin_host.hooks",
        "modules/plugin_host/hooks.py",
    )
    spec = _load_spec()
    assert spec["hooks"] == hooks_mod.HOOK_PERMISSIONS


def test_plugin_spec_entry_candidates_match_runtime_manifest():
    spec = _load_spec()
    assert spec["manifest_names"] == ["plugin.json", "cwplugin.json"]
    assert spec["entry_candidates"] == {
        "python": ["main.py", "plugin.py"],
        "process": ["main.exe", "main"],
        "qml_page": ["main.qml", "ui/Page.qml", "ui/page.qml"],
    }
