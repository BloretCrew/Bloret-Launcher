"""Plugin store normalization and status tests."""

import json
from unittest.mock import patch

from modules.plugin_store import (
    _as_list,
    merge_install_state,
    normalize_listing,
)


VALID = {
    "id": "com.example.demo",
    "name": "Demo",
    "version": "1.2.0",
    "download": "https://github.com/example/demo/releases/download/v1/demo.zip",
    "tags": "home, tools",
    "permissions": "ui.home ui.tools",
}


def test_response_shapes():
    assert _as_list([VALID]) == [VALID]
    assert _as_list({"plugins": [VALID]}) == [VALID]
    assert _as_list({"data": {"plugins": [VALID]}}) == [VALID]
    assert _as_list({"plugin": VALID}) == [VALID]


def test_normalize_listing():
    item = normalize_listing(VALID, "https://store.bloret.com/api/v1/plugins")
    assert item["id"] == "com.example.demo"
    assert item["tags"] == ["home", "tools"]
    assert item["permissions"] == ["ui.home", "ui.tools"]


def test_invalid_listing_rejected():
    for key in ("id", "download"):
        data = dict(VALID)
        data.pop(key)
        try:
            normalize_listing(data)
        except ValueError:
            pass
        else:
            raise AssertionError(f"missing {key} accepted")

    data = dict(VALID, download="http://example.com/demo.zip")
    try:
        normalize_listing(data)
    except ValueError:
        pass
    else:
        raise AssertionError("http download accepted")


def test_merge_install_state_and_updates():
    item = normalize_listing(VALID)
    installed = [{"id": item["id"], "version": "1.0.0"}]
    result = merge_install_state([item], installed)
    assert result[0]["installed"] is True
    assert result[0]["update_available"] is True


def test_propose_delegates_without_installing():
    class FakeHost:
        def proposeInstall(self, raw):
            payload = json.loads(raw)
            assert payload["id"] == VALID["id"]
            return '{"ok":true,"pending":true}'

    from modules.plugin_store import PluginStore

    store = PluginStore(FakeHost())
    with patch("modules.plugin_store.cfg.read", return_value={}):
        result = json.loads(store.proposeInstall(json.dumps(VALID)))
    assert result["pending"] is True


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("ALL PASSED")
