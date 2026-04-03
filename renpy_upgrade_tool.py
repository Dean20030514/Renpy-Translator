# renpy_upgrade_tool.py — shim, remove after migration
import importlib as _il, sys as _sys
_sys.modules[__name__] = _il.import_module("tools.renpy_upgrade_tool")
