"""Top-level package for TinyRetriever."""

from __future__ import annotations

import asyncio
import sys
from importlib.metadata import PackageNotFoundError, version

from tiny_retriever import exceptions
from tiny_retriever.tiny_retriever import download, fetch, unique_filename

try:
    __version__ = version("tiny_retriever")
except PackageNotFoundError:
    __version__ = "999"

if sys.platform == "win32":  # pragma: no cover
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

__all__ = [
    "__version__",
    "download",
    "exceptions",
    "fetch",
    "unique_filename",
]
