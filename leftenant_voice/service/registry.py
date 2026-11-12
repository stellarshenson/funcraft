"""The engines this deployment serves, by name: S2 Pro always, AuK-Flash where `.venv-auk` is installed."""
from pathlib import Path
from typing import Callable

from engine import Engine
from engine_auk import AUK_PYTHON, AukEngine
from engine_s2pro import S2ProEngine


class UnknownEngineError(LookupError):
    """The request named an engine that is not installed here."""


def available_engines(voices_dir: Path,
                      token: Callable[[], str | None] | None = None) -> dict[str, Engine]:
    """The engines installed on this machine, by name.

    Args:
        voices_dir: folder of `<voice>.wav` + `<voice>.txt` pairs, shared by the engines.
        token: returns the Hugging Face token the S2 Pro download uses, read at load time; the AuK engine
            needs none.

    Returns:
        Engine instances by name; constructing one does not load its model.
    """
    engines: dict[str, Engine] = {
        "s2pro": S2ProEngine(voices_dir, token if token is not None else lambda: None)}
    if AUK_PYTHON.is_file():
        engines["auk-flash"] = AukEngine(voices_dir)
    return engines


def get_engine(engines: dict[str, Engine], name: str) -> Engine:
    """The engine named `name`.

    Args:
        engines: the installed engines, from `available_engines`.
        name: engine name from the request or the ENGINE setting.

    Returns:
        The engine.

    Raises:
        UnknownEngineError: no installed engine has that name; the message lists the known ones.
    """
    if name not in engines:
        raise UnknownEngineError(f"unknown engine {name!r}; available: {sorted(engines)}")
    return engines[name]
