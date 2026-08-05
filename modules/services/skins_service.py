"""本地皮肤库（保存 / 列表 / 装备到微软账号）。"""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from modules.services.base import ServiceResult, err, ok

try:
    import modules.globals as BLglobals
except Exception:  # pragma: no cover
    BLglobals = None  # type: ignore


def _skins_root() -> str:
    base = ""
    if BLglobals is not None:
        base = getattr(BLglobals, "datapath", "") or ""
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".Bloret-Launcher")
    path = os.path.join(base, "skins")
    os.makedirs(path, exist_ok=True)
    return path


def _index_path() -> str:
    return os.path.join(_skins_root(), "index.json")


def _load_index() -> Dict[str, Any]:
    path = _index_path()
    if not os.path.isfile(path):
        return {"skins": [], "updated_at": 0}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"skins": [], "updated_at": 0}
        data.setdefault("skins", [])
        return data
    except Exception:
        return {"skins": [], "updated_at": 0}


def _save_index(data: Dict[str, Any]) -> None:
    data["updated_at"] = int(time.time())
    path = _index_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def list_skins() -> ServiceResult[List[Dict[str, Any]]]:
    data = _load_index()
    skins = list(data.get("skins") or [])
    # 校验文件还在
    out = []
    for s in skins:
        if not isinstance(s, dict):
            continue
        p = s.get("path") or ""
        if p and os.path.isfile(p):
            out.append(s)
    return ok(out)


def import_skin_file(
    file_path: str,
    *,
    name: str = "",
    variant: str = "classic",  # classic | slim
) -> ServiceResult[Dict[str, Any]]:
    if not file_path or not os.path.isfile(file_path):
        return err("file not found", "not_found")
    if not str(file_path).lower().endswith(".png"):
        return err("仅支持 PNG 皮肤", "invalid_format")
    skin_id = uuid.uuid4().hex[:12]
    dest_name = f"{skin_id}.png"
    dest = os.path.join(_skins_root(), dest_name)
    try:
        with open(file_path, "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
    except Exception as e:
        return err(str(e), "copy_failed")
    entry = {
        "id": skin_id,
        "name": name or Path(file_path).stem,
        "path": dest,
        "variant": variant if variant in ("classic", "slim") else "classic",
        "created_at": int(time.time()),
    }
    data = _load_index()
    skins = list(data.get("skins") or [])
    skins.insert(0, entry)
    data["skins"] = skins
    _save_index(data)
    return ok(entry)


def delete_skin(skin_id: str) -> ServiceResult[bool]:
    data = _load_index()
    skins = list(data.get("skins") or [])
    kept = []
    removed = None
    for s in skins:
        if isinstance(s, dict) and s.get("id") == skin_id:
            removed = s
            continue
        kept.append(s)
    if not removed:
        return err("not found", "not_found")
    data["skins"] = kept
    _save_index(data)
    try:
        p = removed.get("path")
        if p and os.path.isfile(p):
            os.remove(p)
    except OSError:
        pass
    return ok(True)


def _get_minecraft_access_token() -> Optional[str]:
    """从 config / globals 尽量拿到 Minecraft 访问令牌。"""
    try:
        import modules.config as cfg

        conf = cfg.read() or {}
        # 常见字段
        for key in ("mc_access_token", "minecraft_token", "access_token"):
            if conf.get(key):
                return str(conf.get(key))
        accounts = conf.get("accounts") or conf.get("microsoft_accounts") or []
        if isinstance(accounts, list):
            for acc in accounts:
                if not isinstance(acc, dict):
                    continue
                if acc.get("selected") or acc.get("active"):
                    tok = acc.get("access_token") or acc.get("mc_token") or acc.get("token")
                    if tok:
                        return str(tok)
            for acc in accounts:
                if isinstance(acc, dict):
                    tok = acc.get("access_token") or acc.get("mc_token") or acc.get("token")
                    if tok:
                        return str(tok)
        # 单账号
        acc = conf.get("account") or conf.get("microsoft_account") or {}
        if isinstance(acc, dict):
            tok = acc.get("access_token") or acc.get("mc_token") or acc.get("token")
            if tok:
                return str(tok)
    except Exception:
        pass
    return None


def equip_skin(skin_id: str, variant: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    """
    通过 Mojang API 装备本地皮肤。
    需要有效的 Minecraft access token；失败时仍保留本地库条目。
    """
    data = _load_index()
    entry = next((s for s in (data.get("skins") or []) if isinstance(s, dict) and s.get("id") == skin_id), None)
    if not entry:
        return err("skin not found", "not_found")
    path = entry.get("path") or ""
    if not os.path.isfile(path):
        return err("skin file missing", "not_found")
    token = _get_minecraft_access_token()
    if not token:
        return err("未找到微软/Minecraft 登录令牌，请先登录正版账号", "no_token")

    var = variant or entry.get("variant") or "classic"
    if var not in ("classic", "slim"):
        var = "classic"
    try:
        with open(path, "rb") as f:
            png = f.read()
        # POST https://api.minecraftservices.com/minecraft/profile/skins
        files = {
            "file": ("skin.png", png, "image/png"),
        }
        form = {"variant": var}
        resp = requests.post(
            "https://api.minecraftservices.com/minecraft/profile/skins",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=form,
            timeout=30,
        )
        if resp.status_code not in (200, 204):
            return err(f"Mojang API HTTP {resp.status_code}: {resp.text[:200]}", "api_error")
        entry["equipped_at"] = int(time.time())
        entry["variant"] = var
        # 写回
        skins = []
        for s in data.get("skins") or []:
            if isinstance(s, dict) and s.get("id") == skin_id:
                skins.append(entry)
            else:
                skins.append(s)
        data["skins"] = skins
        _save_index(data)
        return ok({"id": skin_id, "variant": var, "status": "equipped"})
    except Exception as e:
        return err(str(e), "equip_failed")


def query_player_textures(uuid_or_name: str) -> ServiceResult[Dict[str, Any]]:
    """查询玩家皮肤/披风 URL（不装备）。"""
    import re

    session = requests.Session()
    session.headers["User-Agent"] = "Bloret-Launcher/skins"
    uid = uuid_or_name.strip().replace("-", "")
    try:
        if not re.fullmatch(r"[0-9a-fA-F]{32}", uid):
            # name -> uuid
            r = session.get(f"https://api.mojang.com/users/profiles/minecraft/{uuid_or_name.strip()}", timeout=10)
            if r.status_code != 200:
                return err("player not found", "not_found")
            uid = r.json().get("id") or ""
        if not uid:
            return err("player not found", "not_found")
        profile = session.get(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{uid}",
            timeout=10,
        )
        if profile.status_code != 200:
            return err("profile not found", "not_found")
        props = profile.json().get("properties") or []
        skin = cape = ""
        for p in props:
            if p.get("name") != "textures":
                continue
            raw = base64.b64decode(p.get("value") or "")
            tex = json.loads(raw.decode("utf-8", errors="replace"))
            textures = (tex.get("textures") or {})
            skin = (textures.get("SKIN") or {}).get("url") or ""
            cape = (textures.get("CAPE") or {}).get("url") or ""
        return ok({"uuid": uid, "skin": skin, "cape": cape})
    except Exception as e:
        return err(str(e), "query_failed")
