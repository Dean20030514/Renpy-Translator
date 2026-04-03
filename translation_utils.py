# translation_utils.py — shim, remove after migration
import importlib as _il, sys as _sys
_sys.modules[__name__] = _il.import_module("core.translation_utils")
