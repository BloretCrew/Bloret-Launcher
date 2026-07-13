"""插件商店安装请求 / 协议解析单测（无 pytest 依赖）。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from modules.plugin_install_request import (
    file_sha256,
    get_install_queue,
    parse_bloret_url,
    parse_install_params,
    validate_download_url,
    verify_sha256,
)
from modules.protocol_handler import extract_bloret_urls, is_bloret_url


def test_reject_http_download():
    ok, err = validate_download_url("http://evil.com/a.zip")
    assert ok is False
    assert "https" in err.lower() or "http" in err.lower()


def test_reject_untrusted_host():
    ok, err = validate_download_url("https://evil-malware.example/a.zip")
    assert ok is False
    assert "信任" in err or "host" in err.lower() or "主机" in err


def test_accept_github_https():
    ok, err = validate_download_url(
        "https://github.com/org/repo/releases/download/v1/p.zip"
    )
    assert ok is True, err


def test_parse_bloret_url():
    req, err = parse_bloret_url(
        "bloret://plugin/install?download=https%3A%2F%2Fgithub.com%2Fa%2Fb%2Fc.zip"
        "&id=com.ex.p&name=P&version=1.0"
    )
    assert err == ""
    assert req is not None
    assert req.id == "com.ex.p"
    assert req.name == "P"
    assert req.download_host() == "github.com"


def test_parse_bloret_alias():
    req, err = parse_bloret_url(
        "bloret://install-plugin?download=https://cdn.jsdelivr.net/gh/x/y@v1/p.zip&name=X"
    )
    assert err == ""
    assert req is not None
    assert req.download_host() == "cdn.jsdelivr.net"


def test_sha256_verify():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "blob.bin"
        path.write_bytes(b"hello-plugin")
        digest = file_sha256(str(path))
        ok, err = verify_sha256(str(path), digest)
        assert ok is True, err
        ok, err = verify_sha256(str(path), "0" * 64)
        assert ok is False


def test_invalid_sha256_format():
    req, err = parse_install_params(
        {
            "download": "https://github.com/a/b/c.zip",
            "sha256": "not-a-hash",
        }
    )
    assert req is None
    assert "sha256" in err.lower()


def test_extract_bloret_urls():
    assert is_bloret_url("bloret://plugin/install?x=1")
    urls = extract_bloret_urls(
        ["--foo", "bloret://plugin/install?download=https://github.com/a/b/c.zip"]
    )
    assert len(urls) == 1


def test_propose_install_host():
    from modules.plugin_host.host import PluginHost

    host = PluginHost()
    bad = json.loads(host.proposeInstall('{"download":"http://x.com/a.zip","name":"x"}'))
    assert bad["ok"] is False
    good = json.loads(
        host.proposeInstall(
            '{"download":"https://github.com/a/b/c.zip","name":"Demo","id":"com.demo"}'
        )
    )
    assert good["ok"] is True
    assert good.get("token")
    assert get_install_queue().get(good["token"]) is not None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print("RUN", name)
            fn()
            print(" OK", name)
    print("ALL PASSED")
