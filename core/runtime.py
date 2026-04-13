"""Runtime helpers."""

import os
import sys


def resource_path(relative_path):
    """Return the absolute path for a bundled resource.

    :param relative_path: Relative resource path.
    :type relative_path: str
    :return: Absolute path.
    :rtype: str
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def is_pyinstaller_environment():
    """Return whether the app is running from PyInstaller.

    :return: ``True`` when bundled by PyInstaller.
    :rtype: bool
    """
    try:
        sys._MEIPASS
        return True
    except Exception:
        return False
