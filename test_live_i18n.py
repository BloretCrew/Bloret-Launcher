from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from modules import live_i18n


class FakeResponse:
    def __init__(self, data, status=200):
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def close(self):
        pass


class LiveI18nTests(unittest.TestCase):
    def test_cross_platform_cache_is_under_datapath(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                live_i18n.user_lang_dir(tmp),
                Path(tmp) / "lang",
            )
            self.assertEqual(
                live_i18n.cached_language_path("en-GB", tmp),
                Path(tmp) / "lang" / "en-GB.json",
            )

    def test_locale_mapping_and_urls(self):
        self.assertIn("/manifest", live_i18n.manifest_url())
        url = live_i18n.translated_url("gt-ZH")
        self.assertIn("locale=gt", url)
        self.assertIn("mode=top_voted", url)
        with self.assertRaises(ValueError):
            live_i18n.translated_url("zh-cn")
        with self.assertRaises(ValueError):
            live_i18n.normalize_language("../evil")

    def test_atomic_write_keeps_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lang" / "en-GB.json"
            self.assertTrue(live_i18n.atomic_write_json(path, {"texts": {"a": "b"}}))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["texts"]["a"], "b")
            self.assertFalse(live_i18n.atomic_write_json(path, {"texts": {"a": "b"}}))

    def test_sync_success_saves_launcher_named_file(self):
        manifest = {"lang": {"gt": {"name": "梗体中文"}}, "project": {}}
        catalog = {"texts": {"设置": "设汁", "空": ""}}
        session = FakeSession([FakeResponse(manifest), FakeResponse(catalog)])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            live_i18n.BLglobals, "datapath", tmp
        ), mock.patch.object(
            live_i18n, "_settings", return_value={
                "enabled": True,
                "baseUrl": "https://tr.bloret.net",
                "mode": "top_voted",
                "timeout": (1, 1),
            }
        ):
            result = live_i18n.sync_language("gt-ZH", session=session)
            self.assertTrue(result["ok"])
            self.assertTrue(result["updated"])
            saved = Path(tmp) / "lang" / "gt-ZH.json"
            self.assertEqual(json.loads(saved.read_text(encoding="utf-8")), catalog)
            self.assertIn("/manifest", session.urls[0][0])
            self.assertIn("locale=gt", session.urls[1][0])

    def test_failed_download_never_overwrites_old_cache(self):
        old = {"texts": {"设置": "old"}}
        session = FakeSession([FakeResponse({"lang": {}, "project": {}}), RuntimeError("offline")])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            live_i18n.BLglobals, "datapath", tmp
        ), mock.patch.object(
            live_i18n, "_settings", return_value={
                "enabled": True,
                "baseUrl": "https://tr.bloret.net",
                "mode": "top_voted",
                "timeout": (1, 1),
            }
        ):
            path = Path(tmp) / "lang" / "en-GB.json"
            live_i18n.atomic_write_json(path, old)
            result = live_i18n.sync_language("en-GB", session=session)
            self.assertFalse(result["ok"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), old)

    def test_language_metadata_maps_manifest_contributors_and_update_time(self):
        manifest = {
            "lang": {
                "gt": {
                    "name": "梗体中文",
                    "contributor": ["Detrital", "Rhedar"],
                    "updatedAt": "2026-08-10T12:34:56.000Z",
                }
            },
            "project": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            live_i18n.atomic_write_json(live_i18n.manifest_cache_path(tmp), manifest)
            metadata = live_i18n.language_metadata("gt-ZH", tmp)
            self.assertEqual(metadata["contributors"], ["Detrital", "Rhedar"])
            self.assertEqual(metadata["updatedAt"], "2026-08-10T12:34:56.000Z")
            self.assertEqual(metadata["locale"], "gt")

    def test_source_language_metadata_is_marked_source(self):
        metadata = live_i18n.language_metadata("zh-cn")
        self.assertTrue(metadata["source"])
        self.assertEqual(metadata["contributors"], [])

    def test_manifest_failure_still_attempts_stable_translated_url(self):
        catalog = {"texts": {"设置": "Settings"}}
        session = FakeSession([RuntimeError("manifest down"), FakeResponse(catalog)])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            live_i18n.BLglobals, "datapath", tmp
        ), mock.patch.object(
            live_i18n, "_settings", return_value={
                "enabled": True,
                "baseUrl": "https://tr.bloret.net",
                "mode": "top_voted",
                "timeout": (1, 1),
            }
        ):
            result = live_i18n.sync_language("en-GB", session=session)
            self.assertTrue(result["ok"])
            self.assertEqual(len(session.urls), 2)

    def test_i18n_source_contains_nonempty_remote_merge_guard(self):
        source = (Path(__file__).parent / "modules" / "i18n.py").read_text(encoding="utf-8")
        self.assertIn("def _deep_merge_nonempty", source)
        self.assertIn('elif isinstance(value, str) and value == "":', source)


if __name__ == "__main__":
    unittest.main()
