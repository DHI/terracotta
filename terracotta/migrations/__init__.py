"""migrations/__init__.py

Define available migrations.
"""

import os
import glob
import importlib


MIGRATIONS = {}

glob_pattern = os.path.join(os.path.dirname(__file__), "v*_*.py")

for modpath in glob.glob(glob_pattern):
    modname = os.path.basename(modpath)[: -len(".py")]
    mod = importlib.import_module(f"{__name__}.{modname}")
    assert all(
        hasattr(mod, attr) for attr in ("up_version", "down_version", "upgrade_sql")
    )
    assert mod.down_version not in MIGRATIONS
    MIGRATIONS[mod.down_version] = mod
