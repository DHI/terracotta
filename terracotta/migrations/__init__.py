"""migrations/__init__.py

Define available migrations.
"""

import os
import glob
import importlib


MIGRATIONS = {}

for modname in glob.glob("v*_*.py", root_dir=os.path.dirname(__file__)):
    mod = importlib.import_module(f"{__name__}.{modname[:-3]}")
    assert all(hasattr(mod, attr) for attr in ("up_version", "down_version", "upgrade_sql", "downgrade_sql"))
    assert mod.down_version not in MIGRATIONS
    MIGRATIONS[mod.down_version] = mod