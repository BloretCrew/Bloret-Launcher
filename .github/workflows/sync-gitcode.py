#!/usr/bin/env python3
"""Sync a GitHub release and its assets to GitCode (gitcode.com).

The script is idempotent:
  * the GitCode release is created when it is missing, updated when it exists
  * assets that already exist on GitCode are skipped

Environment:
  GITCODE_TOKEN   GitCode personal access token with write access to the repo
  GITCODE_REPO    GitCode repository path (default: Bloret/Bloret-Launcher)
  GITCODE_API     GitCode API base URL (default: https://gitcode.com/api/v5)
  GITCODE_BRANCH  Branch mirrored on GitCode (default: Windows)
  GH_TOKEN        GitHub token used by the `gh` CLI (read access to releases)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API = "https://gitcode.com/api/v5"
DEFAULT_REPO = "Bloret/Bloret-Launcher"
DEFAULT_BRANCH = "Windows"


def log(message: str) -> None:
    print(f"[sync-gitcode] {message}", flush=True)


def api(method: str, url: str, token: str, payload=None, timeout: int = 180):
    """Call the GitCode API and return (status, body). Body is parsed JSON when possible."""
    data = None
    headers = {
        "PRIVATE-TOKEN": token,
        "Accept": "application/json",
        "User-Agent": "bloret-launcher-sync",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(raw)
        except json.JSONDecodeError:
            return error.code, raw
    except urllib.error.URLError as error:
        return 0, str(error)


def gh_json(*args: str):
    result = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout or "{}")


def git_sha(tag: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "-n", "1", tag], capture_output=True, text=True
        )
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else None
    except OSError:
        return None


def ensure_release(base: str, tag: str, token: str, payload: dict) -> dict:
    """Create the GitCode release when missing, update it otherwise."""
    status, existing = api("GET", f"{base}/releases/{tag}", token)
    if status == 404:
        log(f"creating GitCode release {tag}")
        status, body = api("POST", f"{base}/releases", token, payload)
        if status not in (200, 201):
            raise RuntimeError(f"creating the release failed ({status}): {body}")
        return body
    if status != 200:
        raise RuntimeError(f"reading the release failed ({status}): {existing}")

    log(f"updating GitCode release {tag}")
    status, body = api("PATCH", f"{base}/releases/{tag}", token, payload)
    if status != 200:
        raise RuntimeError(f"updating the release failed ({status}): {body}")
    return body


def upload_asset(base: str, tag: str, token: str, path: str, name: str) -> None:
    """Upload one asset through the two step GitCode upload flow."""
    query = urllib.parse.urlencode({"file_name": name, "dir": "", "append": ""})
    status, response = api("GET", f"{base}/releases/{tag}/upload_url?{query}", token)
    if status != 200 or not isinstance(response, dict) or "url" not in response:
        raise RuntimeError(f"requesting an upload URL failed ({status}): {response}")

    command = [
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--retry",
        "3",
        "--retry-delay",
        "5",
        "--connect-timeout",
        "30",
        "--max-time",
        "7200",
        "--upload-file",
        path,
        "-X",
        "PUT",
    ]
    for key, value in (response.get("headers") or {}).items():
        command += ["-H", f"{key}: {value}"]
    command.append(response["url"])
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync a GitHub release to GitCode")
    parser.add_argument("--tag", required=True, help="Release tag, for example 27.2.2")
    parser.add_argument("--repo", default=os.environ.get("GITCODE_REPO", DEFAULT_REPO))
    parser.add_argument("--api", default=os.environ.get("GITCODE_API", DEFAULT_API))
    parser.add_argument("--branch", default=os.environ.get("GITCODE_BRANCH", DEFAULT_BRANCH))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download the assets but do not upload them",
    )
    args = parser.parse_args()

    token = os.environ.get("GITCODE_TOKEN", "").strip()
    if not token:
        log("GITCODE_TOKEN is not configured, aborting")
        return 1

    release = gh_json(
        "release",
        "view",
        args.tag,
        "--json",
        "tagName,name,body,isPrerelease,isDraft,assets",
    )
    if release.get("isDraft"):
        log(f"the GitHub release {args.tag} is a draft, nothing to sync")
        return 0

    # GitCode ignores the "prerelease" flag and only understands the release
    # status, so a pre-release keeps the "latest" slot for the stable release.
    is_prerelease = bool(release.get("isPrerelease"))
    payload = {
        "tag_name": release["tagName"],
        "name": release.get("name") or f"Bloret Launcher {release['tagName']}",
        "body": release.get("body") or "",
        "prerelease": is_prerelease,
        "release_status": "none" if is_prerelease else "latest",
    }
    sha = git_sha(args.tag)
    if sha:
        payload["target_commitish"] = sha

    base = f"{args.api.rstrip('/')}/repos/{args.repo}"
    release_on_gitcode = ensure_release(base, args.tag, token, payload)

    existing = {
        asset.get("name")
        for asset in (release_on_gitcode.get("assets") or [])
        if asset.get("type") == "attach"
    }
    wanted = [asset["name"] for asset in (release.get("assets") or [])]
    missing = [name for name in wanted if name not in existing]
    if not missing:
        log(f"all {len(wanted)} assets are already on GitCode")
        return 0

    log(f"uploading {len(missing)} of {len(wanted)} assets: {', '.join(missing)}")
    workdir = tempfile.mkdtemp(prefix="gitcode-sync-")
    try:
        for name in missing:
            log(f"downloading {name}")
            subprocess.run(
                [
                    "gh",
                    "release",
                    "download",
                    args.tag,
                    "--pattern",
                    name,
                    "--dir",
                    workdir,
                    "--clobber",
                ],
                check=True,
            )
            path = os.path.join(workdir, name)
            if args.dry_run:
                continue
            log(f"uploading {name}")
            upload_asset(base, args.tag, token, path, name)
            log(f"uploaded {name}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    log("done")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        log(f"command failed: {error}")
        sys.exit(1)
    except RuntimeError as error:
        log(str(error))
        sys.exit(1)
