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


def test_plugin_spec_version_and_new_ui_permissions():
    spec = _load_spec()
    assert spec["spec_version"] == "1.1.0"
    assert "ui.home" in spec["permissions"]
    assert "ui.tools" in spec["permissions"]
    assert spec["contributes"]["home"] == "ui.home"
    assert spec["contributes"]["tools"] == "ui.tools"


def test_manifest_resolve_path_rejects_escape(tmp_path):
    manifest_mod = _load_module(
        "modules.plugin_host.manifest",
        "modules/plugin_host/manifest.py",
    )
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    assert manifest_mod.resolve_path(str(plugin_dir), "ui/Card.qml").startswith(str(plugin_dir))
    for unsafe in ("../outside.qml", str(tmp_path / "absolute.qml")):
        try:
            manifest_mod.resolve_path(str(plugin_dir), unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe plugin path accepted: {unsafe}")


def test_invoke_hook_reaches_registry_and_bus():
    registry_mod = _load_module(
        "modules.plugin_host.registry",
        "modules/plugin_host/registry.py",
    )
    bus_mod = _load_module(
        "modules.plugin_host.event_bus",
        "modules/plugin_host/event_bus.py",
    )
    # dispatch imports registry/bus; load after stubs
    dispatch_mod = _load_module(
        "modules.plugin_host.dispatch",
        "modules/plugin_host/dispatch.py",
    )

    # reset singletons for isolation
    registry_mod._registry = registry_mod.ContributionRegistry()
    bus_mod._bus = bus_mod.EventBus()

    seen = []

    def hook_fn(*args, **kwargs):
        seen.append(("hook", args))

    def bus_fn(*args, **kwargs):
        seen.append(("bus", args))

    registry_mod.get_registry().add_hook("test.event", "p1", hook_fn)
    bus_mod.get_event_bus().on("test.event", bus_fn, plugin_id="p2")
    results = dispatch_mod.invoke_hook("test.event", 1, 2)
    assert len(results) >= 2
    kinds = {x[0] for x in seen}
    assert "hook" in kinds and "bus" in kinds
