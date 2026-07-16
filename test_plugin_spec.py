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
    assert spec["spec_version"] == "2.0.0"
    assert "ui.home" in spec["permissions"]
    assert "ui.tools" in spec["permissions"]
    assert "ui.live" in spec["permissions"]
    assert "versions.read" in spec["permissions"]
    assert "download.source" in spec["permissions"]
    assert spec["contributes"]["home"] == "ui.home"
    assert spec["contributes"]["tools"] == "ui.tools"
    assert "live" in (spec.get("panel_areas") or [])


def test_install_plugin_from_path_uses_manifest_id(tmp_path, monkeypatch):
    import modules.plugin as plugin_mod

    plugin_root = tmp_path / "Plugin"
    plugin_root.mkdir()
    monkeypatch.setattr(plugin_mod.BLglobals, "datapath", str(tmp_path), raising=False)

    source = tmp_path / "src"
    source.mkdir()
    (source / "plugin.json").write_text(
        json.dumps(
            {
                "id": "com.example.news",
                "name": "News",
                "version": "1.2.3",
                "permissions": ["ui.home"],
            }
        ),
        encoding="utf-8",
    )
    (source / "ui").mkdir()
    (source / "ui" / "HomeCard.qml").write_text("import QtQuick\nItem {}", encoding="utf-8")

    ok, detail = plugin_mod.install_plugin_from_path(str(source), force=True)
    assert ok is True
    assert detail == "com.example.news"
    installed = plugin_root / "com.example.news" / "plugin.json"
    assert installed.is_file()

    # nested zip root
    import zipfile

    nested_zip = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested_zip, "w") as bundle:
        bundle.writestr("wrap/plugin.json", (source / "plugin.json").read_text(encoding="utf-8"))
        bundle.writestr("wrap/ui/HomeCard.qml", "import QtQuick\nItem {}")
    ok, detail = plugin_mod.install_plugin_from_path(str(nested_zip), force=True)
    assert ok is True
    assert detail == "com.example.news"


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


def test_registry_panels_and_clear():
    registry_mod = _load_module(
        "modules.plugin_host.registry",
        "modules/plugin_host/registry.py",
    )
    registry_mod._registry = registry_mod.ContributionRegistry()
    reg = registry_mod.get_registry()
    reg.add_panel(
        "live",
        {
            "id": "p1",
            "plugin_id": "com.demo",
            "title": "Demo",
            "qml": "/tmp/x.qml",
            "order": 10,
        },
    )
    reg.add_source("mods", {"id": "src1", "plugin_id": "com.demo", "title": "Src"})
    reg.add_channel({"id": "ch1", "plugin_id": "com.demo"})
    assert len(reg.get_panels("live")) == 1
    assert len(reg.get_sources("mods")) == 1
    assert len(reg.get_channels()) == 1
    reg.clear_plugin("com.demo")
    assert reg.get_panels("live") == []
    assert reg.get_sources("mods") == []
    assert reg.get_channels() == []


def test_services_base_result():
    base = _load_module("modules.services.base", "modules/services/base.py")
    r = base.ok({"a": 1})
    assert r.ok and r.to_dict()["status"] == "success"
    e = base.err("boom", "x")
    assert not e.ok and e.to_dict()["message"] == "boom"
