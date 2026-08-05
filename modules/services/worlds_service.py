"""世界列表 / 服务器 / Quick Play 参数。"""

from __future__ import annotations

import os
import struct
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules.services.base import ServiceResult, err, ok
from modules.services.paths_util import content_dir, safe_version_dir


# ---- 极简 NBT（改自 modules/versions.SimpleNBT，保持服务层独立） ----

class _NBT:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read_tag(self, include_name: bool = True):
        if self.pos >= len(self.data):
            return None, None, None
        tag_type = self.data[self.pos]
        self.pos += 1
        if tag_type == 0:
            return 0, None, None
        name = self.read_string() if include_name else ""
        payload = self.read_payload(tag_type)
        return tag_type, name, payload

    def read_payload(self, tag_type: int):
        if tag_type == 1:
            return self.read_byte()
        if tag_type == 2:
            return self.read_short()
        if tag_type == 3:
            return self.read_int()
        if tag_type == 4:
            return self.read_long()
        if tag_type == 5:
            return self.read_float()
        if tag_type == 6:
            return self.read_double()
        if tag_type == 7:
            length = self.read_int()
            val = self.data[self.pos : self.pos + length]
            self.pos += length
            return val
        if tag_type == 8:
            return self.read_string()
        if tag_type == 9:
            return self.read_list()
        if tag_type == 10:
            return self.read_compound()
        if tag_type == 11:
            length = self.read_int()
            val = [self.read_int() for _ in range(length)]
            return val
        if tag_type == 12:
            length = self.read_int()
            val = [self.read_long() for _ in range(length)]
            return val
        return None

    def read_byte(self):
        v = self.data[self.pos]
        self.pos += 1
        return v if v < 128 else v - 256

    def read_short(self):
        v = struct.unpack(">h", self.data[self.pos : self.pos + 2])[0]
        self.pos += 2
        return v

    def read_int(self):
        v = struct.unpack(">i", self.data[self.pos : self.pos + 4])[0]
        self.pos += 4
        return v

    def read_long(self):
        v = struct.unpack(">q", self.data[self.pos : self.pos + 8])[0]
        self.pos += 8
        return v

    def read_float(self):
        v = struct.unpack(">f", self.data[self.pos : self.pos + 4])[0]
        self.pos += 4
        return v

    def read_double(self):
        v = struct.unpack(">d", self.data[self.pos : self.pos + 8])[0]
        self.pos += 8
        return v

    def read_string(self):
        length = struct.unpack(">H", self.data[self.pos : self.pos + 2])[0]
        self.pos += 2
        s = self.data[self.pos : self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return s

    def read_list(self):
        tag_type = self.read_byte()
        if tag_type < 0:
            tag_type += 256
        length = self.read_int()
        return [self.read_payload(tag_type) for _ in range(max(0, length))]

    def read_compound(self):
        result = {}
        while True:
            tag_type, name, payload = self.read_tag(True)
            if tag_type == 0 or tag_type is None:
                break
            result[name] = payload
        return result


def _load_level_dat(path: Path) -> Dict[str, Any]:
    import gzip

    try:
        raw = path.read_bytes()
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
        nbt = _NBT(raw)
        tag_type, name, payload = nbt.read_tag(True)
        if isinstance(payload, dict):
            data = payload.get("Data") or payload
            if isinstance(data, dict):
                return data
        return {}
    except Exception:
        return {}


def list_worlds(version_name: str, mc_dir: Optional[str] = None) -> ServiceResult[List[Dict[str, Any]]]:
    saves = content_dir(version_name, "saves", mc_dir)
    if not saves:
        return err("invalid version", "invalid_version")
    if not os.path.isdir(saves):
        return ok([])
    items: List[Dict[str, Any]] = []
    try:
        for name in sorted(os.listdir(saves)):
            wdir = os.path.join(saves, name)
            if not os.path.isdir(wdir):
                continue
            level = Path(wdir) / "level.dat"
            meta = _load_level_dat(level) if level.is_file() else {}
            last_played = meta.get("LastPlayed")
            # LastPlayed 是毫秒
            try:
                last_played_s = int(last_played) / 1000.0 if last_played else os.path.getmtime(wdir)
            except Exception:
                last_played_s = os.path.getmtime(wdir)
            icon = os.path.join(wdir, "icon.png")
            items.append(
                {
                    "id": name,
                    "name": str(meta.get("LevelName") or name),
                    "folder": name,
                    "path": wdir,
                    "last_played": int(last_played_s),
                    "gamemode": meta.get("GameType"),
                    "hardcore": bool(meta.get("hardcore") or meta.get("Hardcore")),
                    "difficulty": meta.get("Difficulty"),
                    "icon": icon if os.path.isfile(icon) else "",
                    "type": "singleplayer",
                }
            )
        items.sort(key=lambda x: x.get("last_played") or 0, reverse=True)
        return ok(items)
    except Exception as e:
        return err(str(e), "worlds_list_failed")


def list_servers(version_name: str, mc_dir: Optional[str] = None) -> ServiceResult[List[Dict[str, Any]]]:
    """读取 versions/<name>/servers.dat（若有）；否则空。"""
    vdir = safe_version_dir(version_name, mc_dir)
    if not vdir:
        return err("invalid version", "invalid_version")
    path = os.path.join(vdir, "servers.dat")
    if not os.path.isfile(path):
        return ok([])
    try:
        # 复用 versions.parse_servers_dat 若可用
        try:
            from modules.versions import parse_servers_dat

            servers = parse_servers_dat(path) or []
        except Exception:
            servers = []
        out = []
        for s in servers:
            if not isinstance(s, dict):
                continue
            out.append(
                {
                    "name": s.get("name") or s.get("Name") or "",
                    "address": s.get("ip") or s.get("Ip") or s.get("address") or "",
                    "icon": s.get("icon") or "",
                    "type": "server",
                }
            )
        return ok(out)
    except Exception as e:
        return err(str(e), "servers_list_failed")


def quick_play_game_args(quick: Dict[str, Any]) -> List[str]:
    """
    生成 Minecraft Quick Play 游戏参数（1.20+ / 23w14a+）。
    quick: {type, world, server, port}
    """
    if not quick or not quick.get("type"):
        return []
    qtype = str(quick.get("type") or "").lower()
    args: List[str] = []
    if qtype in ("singleplayer", "world"):
        world = quick.get("world") or ""
        if world:
            args += ["--quickPlaySingleplayer", str(world)]
    elif qtype in ("multiplayer", "server"):
        server = quick.get("server") or ""
        if server:
            # 新版
            args += ["--quickPlayMultiplayer", str(server)]
            # 兼容旧 --server / --port
            host = server
            port = quick.get("port")
            if ":" in server and not str(server).startswith("["):
                host, _, p = server.rpartition(":")
                if p.isdigit():
                    port = port or int(p)
            args += ["--server", host]
            if port:
                args += ["--port", str(port)]
    return args


def set_quick_play_world(version_name: str, world_folder: str, mc_dir: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    from modules.services import instance_settings

    return instance_settings.save(
        version_name,
        {"quick_play": {"type": "singleplayer", "world": world_folder, "server": None, "port": None}},
        mc_dir=mc_dir,
    )


def set_quick_play_server(
    version_name: str,
    address: str,
    port: Optional[int] = None,
    mc_dir: Optional[str] = None,
) -> ServiceResult[Dict[str, Any]]:
    from modules.services import instance_settings

    return instance_settings.save(
        version_name,
        {"quick_play": {"type": "multiplayer", "world": None, "server": address, "port": port}},
        mc_dir=mc_dir,
    )


def clear_quick_play(version_name: str, mc_dir: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
    from modules.services import instance_settings

    return instance_settings.save(
        version_name,
        {"quick_play": {"type": None, "world": None, "server": None, "port": None}},
        mc_dir=mc_dir,
    )
