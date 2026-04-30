import os
import subprocess


def hidden_process_kwargs(**kwargs):
    """Return subprocess kwargs that hide child console windows on Windows."""
    if os.name != "nt":
        return kwargs

    startupinfo = kwargs.pop("startupinfo", None) or subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    kwargs["startupinfo"] = startupinfo
    kwargs["creationflags"] = kwargs.get("creationflags", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kwargs
