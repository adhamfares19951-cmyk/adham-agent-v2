"""Configuration package for adham-agent."""
from config.settings import settings

__all__ = ["settings"]

# Backward compatibility with modules expecting config.py attributes
try:
    import importlib.util
    from pathlib import Path
    _cfg_file = Path(__file__).resolve().parent.parent / "config.py"
    if _cfg_file.is_file():
        spec = importlib.util.spec_from_file_location("_legacy_config", _cfg_file)
        if spec and spec.loader:
            _mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_mod)
            for _k, _v in _mod.__dict__.items():
                if not _k.startswith("__"):
                    globals()[_k] = _v
except Exception:
    pass
