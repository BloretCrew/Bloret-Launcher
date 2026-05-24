import json
import os
from pathlib import Path


class PackAnalyzer:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self._mcmeta_cache = None

    def is_valid_pack(self):
        return (self.root_path / "pack.mcmeta").exists()

    def read_mcmeta(self):
        if self._mcmeta_cache:
            return self._mcmeta_cache
        path = self.root_path / "pack.mcmeta"
        if not path.exists():
            return {"error": "pack.mcmeta not found"}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._mcmeta_cache = data
            return data
        except Exception as e:
            return {"error": str(e)}

    def save_mcmeta(self, data):
        path = self.root_path / "pack.mcmeta"
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            self._mcmeta_cache = data
            return True
        except Exception:
            return False

    def get_file_tree(self, git_statuses=None):
        if git_statuses is None:
            git_statuses = {}
        items = []
        self._walk_dir(self.root_path, "", items, git_statuses)
        return items

    def _walk_dir(self, base_path, relative_path, items, git_statuses, depth=0):
        try:
            entries = sorted(
                os.listdir(base_path / relative_path),
                key=lambda x: (not (base_path / relative_path / x).is_dir(), x.lower()),
            )
        except PermissionError:
            return

        for entry in entries:
            if entry.startswith("."):
                continue
            entry_rel = os.path.join(relative_path, entry) if relative_path else entry
            entry_path = base_path / entry_rel
            is_dir = entry_path.is_dir()
            status = git_statuses.get(entry_rel, "")
            items.append(
                {
                    "name": entry,
                    "path": entry_rel,
                    "type": "dir" if is_dir else "file",
                    "gitStatus": status,
                    "depth": depth,
                }
            )
            if is_dir:
                self._walk_dir(base_path, entry_rel, items, git_statuses, depth + 1)

    def get_textures(self):
        textures = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return textures
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            textures_dir = namespace / "textures"
            if textures_dir.exists():
                for root, _dirs, files in os.walk(textures_dir):
                    for f in sorted(files):
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            rel = os.path.relpath(os.path.join(root, f), self.root_path)
                            textures.append(
                                {"path": rel, "name": f, "namespace": namespace.name}
                            )
        return textures

    def get_languages(self):
        languages = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return languages
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            lang_dir = namespace / "lang"
            if lang_dir.exists():
                for f in sorted(lang_dir.iterdir()):
                    if f.suffix == ".json":
                        languages.append(
                            {
                                "path": str(f.relative_to(self.root_path)),
                                "name": f.stem,
                                "namespace": namespace.name,
                            }
                        )
        return languages

    def read_language_file(self, lang_rel_path):
        path = self.root_path / lang_rel_path
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_language_file(self, lang_rel_path, data):
        path = self.root_path / lang_rel_path
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return True
        except Exception:
            return False

    def get_stats(self):
        stats = {"files": 0, "dirs": 0, "textures": 0, "languages": 0, "models": 0}
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for d in dirs:
                stats["dirs"] += 1
            for f in files:
                if f.startswith("."):
                    continue
                stats["files"] += 1
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    stats["textures"] += 1
                if f.endswith(".json") and "lang" in root:
                    stats["languages"] += 1
                if f.endswith(".json") and "models" in root:
                    stats["models"] += 1
        return stats

    def get_blockstates(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            bs_dir = namespace / "blockstates"
            if bs_dir.exists():
                for f in sorted(bs_dir.iterdir()):
                    if f.suffix == ".json":
                        rel = str(f.relative_to(self.root_path))
                        results.append({"path": rel, "name": f.stem, "namespace": namespace.name})
        return results

    def get_models(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            for sub in ("models",):
                models_dir = namespace / sub
                if not models_dir.exists():
                    continue
                for root, _dirs, files in os.walk(models_dir):
                    for f in sorted(files):
                        if f.endswith(".json"):
                            rel = os.path.relpath(os.path.join(root, f), self.root_path)
                            kind = "block" if "block" in rel else "item" if "item" in rel else "other"
                            results.append({"path": rel, "name": f, "namespace": namespace.name, "kind": kind})
        return results

    def get_sounds_json(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            sj = namespace / "sounds.json"
            if sj.exists():
                rel = str(sj.relative_to(self.root_path))
                results.append({"path": rel, "namespace": namespace.name})
        return results

    def get_sound_files(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            sounds_dir = namespace / "sounds"
            if not sounds_dir.exists():
                continue
            for root, _dirs, files in os.walk(sounds_dir):
                for f in sorted(files):
                    if f.lower().endswith((".ogg", ".mp3", ".wav")):
                        rel = os.path.relpath(os.path.join(root, f), self.root_path)
                        results.append({"path": rel, "name": f, "namespace": namespace.name})
        return results

    def get_fonts(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            font_dir = namespace / "font"
            if font_dir.exists():
                for f in sorted(font_dir.iterdir()):
                    if f.suffix == ".json":
                        rel = str(f.relative_to(self.root_path))
                        results.append({"path": rel, "name": f.stem, "namespace": namespace.name})
        return results

    def get_texts(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            texts_dir = namespace / "texts"
            if texts_dir.exists():
                for f in sorted(texts_dir.iterdir()):
                    rel = str(f.relative_to(self.root_path))
                    ftype = "json" if f.suffix == ".json" else "txt"
                    results.append({"path": rel, "name": f.name, "namespace": namespace.name, "type": ftype})
        return results

    def get_particles(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            p_dir = namespace / "particles"
            if p_dir.exists():
                for f in sorted(p_dir.iterdir()):
                    if f.suffix == ".json":
                        rel = str(f.relative_to(self.root_path))
                        results.append({"path": rel, "name": f.stem, "namespace": namespace.name})
        return results

    def get_optifine_cem(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            cem_dir = namespace / "optifine" / "cem"
            if cem_dir.exists():
                for f in sorted(cem_dir.iterdir()):
                    if f.suffix in (".jem", ".jpm"):
                        rel = str(f.relative_to(self.root_path))
                        results.append({"path": rel, "name": f.name, "namespace": namespace.name, "kind": f.suffix[1:]})
        return results

    def get_optifine_cit(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if not namespace.is_dir():
                continue
            cit_dir = namespace / "optifine" / "cit"
            if not cit_dir.exists():
                continue
            for root, _dirs, files in os.walk(cit_dir):
                for f in sorted(files):
                    rel = os.path.relpath(os.path.join(root, f), self.root_path)
                    ftype = "properties" if f.endswith(".properties") else "texture" if f.endswith(".png") else "other"
                    results.append({"path": rel, "name": f, "namespace": namespace.name, "type": ftype})
        return results

    def get_special_files(self):
        results = []
        mc = self.root_path / "assets" / "minecraft"
        if not mc.exists():
            return results
        special = ["regional_compliancies.json", "gpu_warnlist.json"]
        for name in special:
            p = mc / name
            if p.exists():
                rel = str(p.relative_to(self.root_path))
                results.append({"path": rel, "name": name})
        lang_dir = mc / "lang"
        if lang_dir.exists():
            dep = lang_dir / "deprecated.json"
            if dep.exists():
                results.append({"path": str(dep.relative_to(self.root_path)), "name": "deprecated.json"})
        return results

    def get_namespaces(self):
        results = []
        assets_dir = self.root_path / "assets"
        if not assets_dir.exists():
            return results
        for namespace in assets_dir.iterdir():
            if namespace.is_dir():
                subdirs = [d.name for d in namespace.iterdir() if d.is_dir()]
                results.append({"name": namespace.name, "directories": subdirs})
        return results
