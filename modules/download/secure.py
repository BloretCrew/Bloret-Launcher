"""HTTPS download with atomic publish, integrity checks, and Range resume."""

import hashlib
import logging
import os
import time
from urllib.parse import urlparse

import modules.globals as BLglobals
from modules.download.session import get_session
from modules.log import log


class DownloadCancelled(Exception):
    """Raised when the user cancels an in-flight download."""


def verify_file(path, expected_size=None, expected_sha1=None, fast=False):
    """
    Verify a local file.
    When fast=True and basename matches expected_sha1 (asset objects), skip full SHA1
    if size already matches.
    """
    try:
        actual_size = os.path.getsize(path)
        if expected_size is not None and actual_size != int(expected_size):
            return False, f"size mismatch: expected {expected_size}, got {actual_size}"
        if expected_sha1:
            sha1_str = str(expected_sha1).lower()
            if fast and expected_size is not None:
                base = os.path.basename(path).lower()
                if base == sha1_str:
                    return True, "ok-fast"
            digest = hashlib.sha1()
            with open(path, "rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual = digest.hexdigest()
            if actual != sha1_str:
                return False, f"sha1 mismatch: expected {expected_sha1}, got {actual}"
        return True, "ok"
    except (OSError, ValueError) as exc:
        return False, str(exc)


def strict_hash_verify_enabled():
    try:
        import modules.config as cfg

        return bool(cfg.read().get("StrictHashVerify", False))
    except Exception:
        return False


def secure_download(
    urls,
    destination,
    metadata=None,
    description="文件",
    retries=3,
    progress_callback=None,
    cancel_event=None,
    pause_event=None,
    resume_event=None,
    allow_resume=True,
    fast_verify=None,
    quiet=False,
):
    """Download via HTTPS to .part, verify size/sha1, then atomically replace destination."""
    metadata = metadata or {}
    expected_size = metadata.get("size")
    expected_sha1 = metadata.get("sha1") or metadata.get("hash")
    if fast_verify is None:
        fast_verify = (
            expected_sha1 is not None
            and expected_size is not None
            and not strict_hash_verify_enabled()
            and os.path.basename(destination).lower() == str(expected_sha1).lower()
        )

    if os.path.exists(destination):
        valid, reason = verify_file(
            destination, expected_size, expected_sha1, fast=bool(fast_verify)
        )
        if valid:
            if not quiet:
                log(f"{description}已存在且校验通过，跳过下载: {destination}")
            return True
        if not quiet:
            log(
                f"{description}现有文件校验失败，将重新下载: {destination}; {reason}",
                logging.WARNING,
            )

    if isinstance(urls, str):
        urls = [urls]
    https_urls = []
    for url in urls or []:
        parsed = urlparse(str(url))
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            log(f"拒绝非 HTTPS 下载地址: {url}", logging.ERROR)
            continue
        if url not in https_urls:
            https_urls.append(url)
    if not https_urls:
        log(f"{description}没有可用的 HTTPS 下载地址: {destination}", logging.ERROR)
        return False

    dest_dir = os.path.dirname(destination)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    part_path = destination + ".part"

    def _wait_if_paused():
        if pause_event is None:
            return
        while pause_event.is_set():
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled("用户取消了下载")
            if resume_event is not None:
                resume_event.wait(timeout=0.5)
                resume_event.clear()
            else:
                time.sleep(0.2)

    for url in https_urls:
        for attempt in range(1, retries + 1):
            if cancel_event is not None and cancel_event.is_set():
                log(f"{description}下载已取消: {destination}", logging.WARNING)
                return False
            try:
                _wait_if_paused()
                existing = 0
                if allow_resume and os.path.exists(part_path):
                    try:
                        existing = os.path.getsize(part_path)
                    except OSError:
                        existing = 0
                if not allow_resume or (
                    expected_size is not None and existing > int(expected_size)
                ):
                    try:
                        os.remove(part_path)
                    except FileNotFoundError:
                        pass
                    existing = 0

                headers = {}
                mode = "wb"
                if allow_resume and existing > 0:
                    headers["Range"] = f"bytes={existing}-"
                    mode = "ab"
                    if not quiet:
                        log(
                            f"续传{description} (尝试 {attempt}/{retries}): {url} from {existing}"
                        )
                else:
                    if not quiet:
                        log(
                            f"安全下载{description} (尝试 {attempt}/{retries}): {url} -> {part_path}"
                        )

                response = get_session().get(
                    url,
                    stream=True,
                    headers=headers,
                    proxies=BLglobals.get_proxies(),
                    timeout=(15, 60),
                )
                if existing > 0 and response.status_code == 200:
                    try:
                        os.remove(part_path)
                    except FileNotFoundError:
                        pass
                    existing = 0
                    mode = "wb"
                elif existing > 0 and response.status_code not in (206, 200):
                    response.raise_for_status()
                else:
                    response.raise_for_status()

                total = int(response.headers.get("content-length", 0) or 0)
                if response.status_code == 206 and existing > 0:
                    content_range = response.headers.get("content-range") or ""
                    if "/" in content_range:
                        try:
                            total = int(content_range.rsplit("/", 1)[-1])
                        except ValueError:
                            total = existing + total
                    else:
                        total = existing + total
                downloaded = existing
                with open(part_path, mode) as stream:
                    for chunk in response.iter_content(chunk_size=128 * 1024):
                        if cancel_event is not None and cancel_event.is_set():
                            raise DownloadCancelled("用户取消了下载")
                        _wait_if_paused()
                        if chunk:
                            stream.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total if total else 0)
                    stream.flush()
                    try:
                        os.fsync(stream.fileno())
                    except OSError:
                        pass
                valid, reason = verify_file(
                    part_path, expected_size, expected_sha1, fast=False
                )
                if not valid:
                    raise ValueError(reason)
                os.replace(part_path, destination)
                if not quiet:
                    log(
                        f"{description}下载并校验成功: {destination} ({downloaded} bytes)"
                    )
                return True
            except DownloadCancelled:
                log(f"{description}下载已取消: {destination}", logging.WARNING)
                return False
            except Exception as exc:
                log(
                    f"{description}下载失败 (尝试 {attempt}/{retries}) {url}: {exc}",
                    logging.WARNING,
                )
                if not allow_resume:
                    try:
                        os.remove(part_path)
                    except OSError:
                        pass
                if attempt < retries:
                    time.sleep(min(2 * attempt, 5))
    log(f"{description}所有 HTTPS 地址均下载失败: {destination}", logging.ERROR)
    return False


def download_file(url, file_path, metadata=None):
    return secure_download(url, file_path, metadata, "文件")
