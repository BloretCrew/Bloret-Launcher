"""Download source URL rewriting (BMCLAPI / official / plugin hooks)."""

import modules.globals as BLglobals


def _apply_download_resolve_hooks(kind: str, original_url: str, urls: list) -> list:
    """Allow plugins to rewrite/append mirror URLs via download.resolve_url."""
    try:
        from modules.plugin_host.hook_util import fire, merge_url_lists

        results = fire(
            "download.resolve_url",
            {
                "kind": kind,
                "original_url": original_url,
                "urls": list(urls or []),
            },
        )
        return merge_url_lists(list(urls or []), results)
    except Exception:
        return list(urls or [])


def dl_source_launcher_or_meta_get(original_url):
    """
    Return launcher/meta download URL candidates.
    BMCLAPI first (unless official), then original.
    """
    if not original_url:
        raise Exception("无对应的 json 下载地址")
    if BLglobals.download_source == "official":
        return _apply_download_resolve_hooks("launcher_meta", original_url, [original_url])

    official_urls = [original_url]
    mirror_urls = [
        original_url.replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://launcher.mojang.com", "https://bmclapi2.bangbang93.com")
        .replace("https://launchermeta.mojang.com", "https://bmclapi2.bangbang93.com")
    ]
    return _apply_download_resolve_hooks("launcher_meta", original_url, mirror_urls + official_urls)


def dl_source_library_get(original_url):
    """Return library/maven URL candidates with BMCL mirrors when enabled."""
    if BLglobals.download_source == "official":
        return _apply_download_resolve_hooks("library", original_url, [original_url])
    replacements = (
        ("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/maven"),
        ("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/maven"),
        ("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/maven"),
        ("https://launcher.mojang.com", "https://bmclapi2.bangbang93.com/maven"),
        ("https://launchermeta.mojang.com", "https://bmclapi2.bangbang93.com/maven"),
        ("https://maven.minecraftforge.net", "https://bmclapi2.bangbang93.com/maven"),
        ("https://maven.neoforged.net/releases", "https://bmclapi2.bangbang93.com/maven"),
        ("https://maven.fabricmc.net", "https://bmclapi2.bangbang93.com/maven"),
    )
    mirror = original_url
    for src, dst in replacements:
        if src in mirror:
            mirror = mirror.replace(src, dst)
            break
    if mirror != original_url:
        return _apply_download_resolve_hooks("library", original_url, [mirror, original_url])
    return _apply_download_resolve_hooks("library", original_url, [original_url])


def dl_source_assets_get(original_url):
    """Return asset object URL candidates."""
    original_url = original_url.replace(
        "http://resources.download.minecraft.net",
        "https://resources.download.minecraft.net",
    )
    if BLglobals.download_source == "official":
        return _apply_download_resolve_hooks("assets", original_url, [original_url])
    official_urls = [original_url]
    mirror_urls = [
        original_url.replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com/assets")
        .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com/assets")
        .replace("https://resources.download.minecraft.net", "https://bmclapi2.bangbang93.com/assets")
    ]
    return _apply_download_resolve_hooks("assets", original_url, mirror_urls + official_urls)
