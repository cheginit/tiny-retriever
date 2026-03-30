"""Core async functions."""

from __future__ import annotations

import asyncio
import atexit
import hashlib
import importlib.util
import json
import os
import random
from collections.abc import Iterable, Sequence
from inspect import signature
from pathlib import Path
from threading import Event, Lock, Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypeVar,
    cast,
    overload,
)

import aiofiles
import aiofiles.os
import aiofiles.ospath
from aiohttp import (
    ClientConnectorDNSError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    TCPConnector,
)
from multidict import MultiDict
from yarl import URL

from tiny_retriever.exceptions import InputTypeError, InputValueError, ServiceError

HAS_ORJSON = importlib.util.find_spec("orjson") is not None


def _json_serialize(obj: Any) -> str:
    """Serialize an object to a JSON string, using orjson when available."""
    if HAS_ORJSON:
        import orjson

        return orjson.dumps(obj).decode()
    return json.dumps(obj)


if TYPE_CHECKING:
    from collections.abc import Coroutine
    from ssl import SSLContext

    from aiohttp import ClientResponse
    from aiohttp.typedefs import StrOrURL

    from tiny_retriever.tiny_retriever import RequestMethod, ResponseT, ReturnType

    T = TypeVar("T")

__all__ = ["check_downloads", "download", "fetch", "unique_filename"]

# Maximum number of overall concurrent requests
MAX_CONCURRENT_CALLS = int(os.getenv("MAX_CONCURRENT_CALLS", "10"))
CHUNK_SIZE = 1024 * 1024  # Default chunk size (1 MB)
MAX_HOSTS = 4  # Maximum connections to a single host (rate-limited service)
TIMEOUT = 2 * 60  # Per-request timeout for in seconds (2 minutes)
MAX_RETRIES = 3  # Default number of retry attempts


_HANDLED_EXCEPTIONS = (
    ClientResponseError,
    ClientConnectorDNSError,
    OSError,
    UnicodeDecodeError,
    ValueError,
)


def _is_retryable(exc: Exception) -> bool:
    """Check if an exception is transient and worth retrying."""
    if isinstance(exc, ClientResponseError) and exc.status >= 500:
        return True
    return isinstance(exc, (ClientConnectorDNSError, asyncio.TimeoutError, OSError))


async def _backoff_sleep(attempt: int, factor: float = 0.5, maximum: float = 30.0) -> None:
    """Sleep with exponential backoff and jitter."""
    timeout = min(factor * (2.0**attempt), maximum)
    timeout += random.uniform(0, timeout * 0.5)  # noqa: S311
    await asyncio.sleep(timeout)


async def _try_once(coro: Coroutine[Any, Any, T]) -> tuple[T, None] | tuple[None, Exception]:
    """Execute a coroutine once, returning ``(result, None)`` on success or ``(None, exc)`` on handled failure."""
    try:
        return await coro, None
    except _HANDLED_EXCEPTIONS as ex:
        return None, ex


async def _get_filesize_once(
    session: ClientSession,
    url: StrOrURL,
    timeout: ClientTimeout,
) -> int:
    """Single attempt to get remote file size from Content-Length header."""
    async with session.get(url, timeout=timeout) as response:
        return int(response.headers.get("Content-Length", -1))


async def _stream_file_once(
    session: ClientSession,
    url: StrOrURL,
    filepath: Path,
    chunk_size: int,
    timeout: ClientTimeout,
) -> None:
    """Single attempt to stream a response to a file.

    Validation strategy:
    - When ``Content-Length`` is provided by the server, the local file
      size is compared against it **both** before downloading (skip
      check) and after (integrity check).
    - Bytes written are tracked during streaming so the integrity check
      does not depend on filesystem flush timing.
    - When ``Content-Length`` is absent the download is accepted as-is
      because no server-side reference is available.
    """
    async with session.get(url, timeout=timeout) as response:
        remote_size = int(response.headers.get("Content-Length", -1))
        if remote_size > 0 and await aiofiles.ospath.exists(filepath):
            stat = await aiofiles.os.stat(filepath)
            if stat.st_size == remote_size:
                return

        written = 0
        async with aiofiles.open(filepath, "wb") as file:
            async for chunk in response.content.iter_chunked(chunk_size):
                await file.write(chunk)
                written += len(chunk)
        if remote_size > 0 and written != remote_size:
            await aiofiles.os.unlink(filepath)
            msg = f"Downloaded file size does not match expected size ({written} != {remote_size})"
            raise ServiceError(
                msg,
                str(url),
            )


class _ResponseHandler(Protocol):
    async def __call__(self, response: ClientResponse) -> ResponseT: ...


async def _make_request_once(
    session: ClientSession,
    method: RequestMethod,
    url: StrOrURL,
    response_handler: _ResponseHandler,
    timeout: float,
    **kwargs: Any,
) -> ResponseT:
    """Single attempt to make an HTTP request and process the response."""
    async with session.request(method, url, timeout=ClientTimeout(timeout), **kwargs) as response:
        return await response_handler(response)


class _AsyncLoopThread(Thread):
    _instance: _AsyncLoopThread | None = None
    _lock = Lock()
    _cleanup_registered = False

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()
        self._running = Event()

    @classmethod
    def _cleanup(cls) -> None:
        """Safe cleanup method for atexit."""
        with cls._lock:
            instance = cls._instance
            if instance is not None:
                instance.stop()
                cls._instance = None

    @classmethod
    def get_instance(cls) -> _AsyncLoopThread:
        """Get or create the singleton instance of AsyncLoopThread."""
        if cls._instance is None or not cls._instance.is_alive():
            with cls._lock:
                # Check again in case another thread created instance
                if cls._instance is None or not cls._instance.is_alive():
                    instance = cls()
                    instance.start()
                    if not cls._cleanup_registered:
                        atexit.register(cls._cleanup)
                        cls._cleanup_registered = True
                    cls._instance = instance
        return cls._instance

    def run(self) -> None:
        """Run the event loop in this thread."""
        asyncio.set_event_loop(self.loop)
        self._running.set()
        try:
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()
            self._running.clear()

    def stop(self) -> None:
        """Stop the event loop thread."""
        if self._running.is_set():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self._running.wait()  # Wait for event to be cleared
            self.join()  # Wait for thread to finish


def _get_loop_handler() -> _AsyncLoopThread:
    """Get the global event loop thread handler, creating it if needed."""
    return _AsyncLoopThread.get_instance()


def _run_in_event_loop(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine in the dedicated asyncio event loop."""
    handler = _get_loop_handler()
    return asyncio.run_coroutine_threadsafe(coro, handler.loop).result()


async def _get_filesize(
    session: ClientSession,
    url: StrOrURL,
    timeout: ClientTimeout,
    retries: int,
) -> int:
    """Get remote file size with retries."""
    for attempt in range(retries):
        result, error = await _try_once(_get_filesize_once(session, url, timeout))
        if error is None:
            return result  # type: ignore[return-value]
        if attempt < retries - 1 and _is_retryable(error):
            await _backoff_sleep(attempt)
            continue
        return -1
    return -1


async def _filesize_session(
    urls: Sequence[StrOrURL],
    limit_per_host: int,
    timeout: float,
    ssl: bool | SSLContext,
    retries: int,
) -> list[int]:
    """Download files concurrently."""
    client_timeout = ClientTimeout(
        total=timeout,  # total timeout
        connect=60,  # 60 seconds to establish connection
        sock_read=300,  # 5 minutes for socket read timeout
    )
    connector = TCPConnector(
        limit_per_host=limit_per_host,
        ssl=ssl,
        limit=MAX_CONCURRENT_CALLS,
    )
    async with ClientSession(
        connector=connector,
        loop=_get_loop_handler().loop,
        json_serialize=_json_serialize,
        trust_env=True,
        raise_for_status=True,
    ) as session:
        tasks = [
            asyncio.create_task(_get_filesize(session, url, client_timeout, retries))
            for url in urls
        ]
        return await asyncio.gather(*tasks)


async def _stream_file(
    session: ClientSession,
    url: StrOrURL,
    filepath: Path,
    chunk_size: int,
    raise_status: bool,
    timeout: ClientTimeout,
    retries: int,
) -> None:
    """Stream the response to a file with retries.

    Partial files from failed attempts are removed before retrying.
    """
    for attempt in range(retries):
        _, error = await _try_once(_stream_file_once(session, url, filepath, chunk_size, timeout))
        if error is None:
            return
        if await aiofiles.ospath.exists(filepath):
            await aiofiles.os.unlink(filepath)
        if attempt < retries - 1 and _is_retryable(error):
            await _backoff_sleep(attempt)
            continue
        if raise_status:
            raise ServiceError(str(error), str(url)) from error
        return


async def _download_session(
    urls: Sequence[StrOrURL],
    files: Sequence[Path],
    limit_per_host: int,
    timeout: float,
    ssl: bool | SSLContext,
    chunk_size: int,
    raise_status: bool,
    retries: int,
) -> None:
    """Download files concurrently."""
    client_timeout = ClientTimeout(
        total=timeout,  # total timeout
        connect=60,  # 60 seconds to establish connection
        sock_read=300,  # 5 minutes for socket read timeout
    )
    connector = TCPConnector(
        limit_per_host=limit_per_host,
        ssl=ssl,
        limit=MAX_CONCURRENT_CALLS,
    )
    async with ClientSession(
        connector=connector,
        loop=_get_loop_handler().loop,
        json_serialize=_json_serialize,
        trust_env=True,
        raise_for_status=True,
    ) as session:
        tasks = [
            asyncio.create_task(
                _stream_file(
                    session, url, filepath, chunk_size, raise_status, client_timeout, retries
                )
            )
            for url, filepath in zip(urls, files, strict=False)
        ]
        await asyncio.gather(*tasks)


def download(
    urls: StrOrURL | Sequence[StrOrURL],
    file_paths: Path | str | Sequence[Path | str],
    *,
    chunk_size: int = CHUNK_SIZE,
    limit_per_host: int = MAX_HOSTS,
    timeout: float = 600,
    ssl: bool | SSLContext = True,
    raise_status: bool = True,
    retries: int = MAX_RETRIES,
) -> None:
    """Download multiple files concurrently by streaming their content to disk.

    Parameters
    ----------
    urls : list of str
        URLs to download.
    file_paths : list of pathlib.Path
        Paths to save the downloaded files.
    chunk_size : int, optional
        Size of the chunks to download, by default 1 MB.
    limit_per_host : int, optional
        Maximum number of concurrent connections per host, by default 4.
    timeout : int, optional
        Request timeout in seconds, by default 10 minutes.
    ssl : bool or ssl.SSLContext, optional
        SSL configuration for the requests, by default True.
    raise_status : bool, optional
        Raise an exception if a request fails, by default True.
        Otherwise, the exception is logged and the function continues.
    retries : int, optional
        Number of retry attempts for transient errors, by default 3.

    Raises
    ------
    InputTypeError
        If urls and file_paths are not lists of the same size.
    ServiceError
        If the request fails or response cannot be processed.
    """
    file_paths = [file_paths] if isinstance(file_paths, (str, Path)) else list(file_paths)
    file_paths = [Path(filepath) for filepath in file_paths]
    urls = [urls] if isinstance(urls, (str, URL)) else list(urls)
    if len(urls) != len(file_paths):
        msg = "urls/files_paths"
        raise InputTypeError(msg, "lists of the same size")

    for parent_dir in {f.parent for f in file_paths}:
        parent_dir.mkdir(parents=True, exist_ok=True)

    _run_in_event_loop(
        _download_session(
            urls, file_paths, limit_per_host, timeout, ssl, chunk_size, raise_status, retries
        )
    )


def check_downloads(
    urls: StrOrURL | Sequence[StrOrURL],
    file_paths: Path | str | Sequence[Path | str],
    *,
    limit_per_host: int = MAX_HOSTS,
    timeout: float = 600,
    ssl: bool | SSLContext = True,
    retries: int = MAX_RETRIES,
) -> dict[Path, int]:
    """Check whether existing downloaded files match the remote file size.

    Only files that already exist on disk are checked. Files that
    are missing or whose local size matches the remote ``Content-Length``
    are *not* included in the returned dictionary.

    .. note::

        Some servers do not provide a ``Content-Length`` header. In
        those cases the remote size cannot be determined and the
        corresponding file is silently skipped (treated as valid).

    Parameters
    ----------
    urls : str or list of str
        URLs corresponding to the downloaded files.
    file_paths : pathlib.Path, str, or list of those
        Local paths to the downloaded files.
    limit_per_host : int, optional
        Maximum number of concurrent connections per host, by default 4.
    timeout : float, optional
        Request timeout in seconds, by default 10 minutes.
    ssl : bool or ssl.SSLContext, optional
        SSL configuration for the requests, by default True.
    retries : int, optional
        Number of retry attempts for transient errors, by default 3.

    Returns
    -------
    dict of pathlib.Path to int
        Mapping of file paths whose local size does **not** match the
        remote size to the expected remote size. An empty dictionary
        means all existing files are valid.

    Raises
    ------
    InputTypeError
        If ``urls`` and ``file_paths`` are not lists of the same size.
    """
    file_paths = [file_paths] if isinstance(file_paths, (str, Path)) else list(file_paths)
    file_paths = [Path(fp) for fp in file_paths]
    urls = [urls] if isinstance(urls, (str, URL)) else list(urls)
    if len(urls) != len(file_paths):
        msg = "urls/files_paths"
        raise InputTypeError(msg, "lists of the same size")

    existing = [(i, fp) for i, fp in enumerate(file_paths) if fp.exists()]
    if not existing:
        return {}

    existing_urls = [urls[i] for i, _ in existing]
    remote_sizes = _run_in_event_loop(
        _filesize_session(existing_urls, limit_per_host, timeout, ssl, retries)
    )
    return {
        fp: remote
        for (_, fp), remote in zip(existing, remote_sizes, strict=False)
        if remote >= 0 and fp.stat().st_size != remote
    }


def unique_filename(
    url: StrOrURL,
    *,
    params: dict[str, Any] | Iterable[tuple[str, Any]] | None = None,
    data: dict[str, Any] | str | None = None,
    prefix: str | None = None,
    file_extension: str = "",
) -> str:
    """Generate a unique filename using SHA-256 from a query.

    Parameters
    ----------
    url : str
        The URL for the request.
    params : dict, multidict.MultiDict, optional
        Query parameters for the request, default is ``None``.
    data : dict, str, optional
        Data or JSON to include in the hash, default is ``None``.
    prefix : str, optional
        A custom prefix to attach to the filename, default is ``None``.
    file_extension : str, optional
        The file extension to append to the filename, default is ``""``.

    Returns
    -------
    str
        A unique filename with the SHA-256 hash, optional prefix, and
        the file extension.
    """
    url_obj = URL(url)

    if params is not None and not isinstance(params, (dict, MultiDict)):
        msg = "params"
        raise InputTypeError(msg, "dict or multidict.MultiDict.")

    if not isinstance(data, (dict, str, type(None))):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "data"
        raise InputTypeError(msg, "dict or str.")

    if params:
        params_obj = MultiDict(params)  # pyright: ignore[reportUnknownArgumentType]
        url_obj = url_obj.with_query(params_obj)
    params_str = str(url_obj.query or "")

    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    else:
        data_str = str(data or "")

    prefix_part = prefix or ""
    hash_input = f"{url_obj.human_repr()}{params_str}{data_str}"
    hash_digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
    file_extension = file_extension.lstrip(".")
    file_extension = f".{file_extension}" if file_extension else ""
    return f"{prefix_part}{hash_digest}{file_extension}"


async def _make_request(
    session: ClientSession,
    method: RequestMethod,
    url: StrOrURL,
    response_handler: _ResponseHandler,
    raise_status: bool,
    timeout: float,
    retries: int,
    **kwargs: Any,
) -> ResponseT | None:
    """Make a single HTTP request with retries."""
    for attempt in range(retries):
        result, error = await _try_once(  # pyright: ignore[reportUnknownVariableType]
            _make_request_once(session, method, url, response_handler, timeout, **kwargs)  # pyright: ignore[reportUnknownArgumentType]
        )
        if error is None:
            return result  # pyright: ignore[reportUnknownVariableType]
        if attempt < retries - 1 and _is_retryable(error):
            await _backoff_sleep(attempt)
            continue
        if raise_status:
            raise ServiceError(str(error), str(url)) from error
        return None
    return None


@overload
async def _batch_request(
    urls: list[StrOrURL],
    method: RequestMethod,
    response_handler: _ResponseHandler,
    limit_per_host: int,
    timeout: float,
    ssl: bool | SSLContext,
    request_kwargs: list[dict[str, Any]] | None,
    raise_status: Literal[False],
    retries: int = MAX_RETRIES,
) -> list[ResponseT | None]: ...


@overload
async def _batch_request(
    urls: list[StrOrURL],
    method: RequestMethod,
    response_handler: _ResponseHandler,
    limit_per_host: int,
    timeout: float,
    ssl: bool | SSLContext,
    request_kwargs: list[dict[str, Any]] | None,
    raise_status: Literal[True],
    retries: int = MAX_RETRIES,
) -> list[ResponseT]: ...


async def _batch_request(
    urls: list[StrOrURL],
    method: RequestMethod,
    response_handler: _ResponseHandler,
    limit_per_host: int,
    timeout: float,
    ssl: bool | SSLContext,
    request_kwargs: list[dict[str, Any]] | None,
    raise_status: bool,
    retries: int = MAX_RETRIES,
) -> list[ResponseT] | list[ResponseT | None]:
    """Execute multiple HTTP requests in parallel."""
    connector = TCPConnector(limit_per_host=limit_per_host, limit=MAX_CONCURRENT_CALLS, ssl=ssl)
    async with ClientSession(
        connector=connector,
        loop=_get_loop_handler().loop,
        json_serialize=_json_serialize,
        trust_env=True,
        raise_for_status=True,
        fallback_charset_resolver=lambda r, _: r.charset or "latin1",
    ) as session:
        if request_kwargs is None:
            tasks = [
                asyncio.create_task(
                    _make_request(
                        session, method, url, response_handler, raise_status, timeout, retries
                    )
                )
                for url in urls
            ]
        else:
            tasks = [
                asyncio.create_task(
                    _make_request(
                        session,
                        method,
                        url,
                        response_handler,
                        raise_status,
                        timeout,
                        retries,
                        **kwargs,
                    )
                )
                for url, kwargs in zip(urls, request_kwargs, strict=False)
            ]
        return await asyncio.gather(*tasks)  # pyright: ignore[reportReturnType]


def _check_url_kwargs(
    urls: StrOrURL | Iterable[StrOrURL],
    request_kwargs: dict[str, Any] | Iterable[dict[str, Any]] | None,
) -> tuple[list[StrOrURL], list[dict[str, Any]] | None]:
    """Check the input types for URLs and request_kwargs."""
    urls = [urls] if isinstance(urls, (str, URL)) else urls
    if not isinstance(urls, (Iterable, Sequence)):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = "urls"
        raise InputTypeError(msg, "Iterable or Sequence")

    url_list = list(urls)
    if any(not isinstance(url, str) for url in url_list):
        msg = "urls"
        raise InputTypeError(msg, "list of str")

    if request_kwargs is None:
        kwargs_list = None
    elif isinstance(request_kwargs, dict) and all(isinstance(k, str) for k in request_kwargs):
        kwargs_list = cast("list[dict[str, Any]]", [request_kwargs])
    elif isinstance(request_kwargs, Iterable) and all(isinstance(k, dict) for k in request_kwargs):  # pyright: ignore[reportUnnecessaryIsInstance]
        kwargs_list = cast("list[dict[str, Any]]", list(request_kwargs))  # pyright: ignore[reportUnknownArgumentType]
        if len(kwargs_list) != len(url_list):
            msg = "request_kwargs"
            raise InputTypeError(msg, "list of the same length as urls")
    else:
        msg = "request_kwargs"
        raise InputTypeError(msg, "list of dict, dict, or None")
    return url_list, kwargs_list


def fetch(
    urls: StrOrURL | Iterable[StrOrURL],
    return_type: ReturnType,
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = MAX_HOSTS,
    timeout: float = TIMEOUT,
    ssl: bool | SSLContext = True,
    raise_status: bool = True,
    retries: int = MAX_RETRIES,
) -> (
    str
    | None
    | bytes
    | dict[str, Any]
    | list[str]
    | list[str | None]
    | list[bytes]
    | list[bytes | None]
    | list[dict[str, Any]]
    | list[dict[str, Any] | None]
):
    """Fetch data from multiple URLs asynchronously.

    Parameters
    ----------
    urls : str, list of str
        URL(s) to fetch data from.
    return_type : {"text", "json", "binary"}
        Desired response format, which can be ``text``, ``json``, or ``binary``.
    request_method : {"get", "post"}, optional
        HTTP method to use, by default ``get``.
    request_kwargs : dict, list of dict, optional
        Keyword argument(s) for (each) request, by default ``None``.
        If provided, must be the same length as ``urls``.
    limit_per_host : int, optional
        Maximum number of concurrent connections per host, by default 4
    timeout : int, optional
        Request timeout in seconds, by default 2 minutes.
    ssl : bool or ssl.SSLContext, optional
        SSL configuration for the requests, by default True.
    raise_status : bool, optional
        Raise an exception if a request fails, by default True.
        Otherwise, the exception is logged and the function continues.
        The queries that failed will return ``None``.
    retries : int, optional
        Number of retry attempts for transient errors, by default 3.

    Returns
    -------
    list of str, list of bytes, or list of dicts
        The response data from the requests

    Raises
    ------
    InputTypeError
        If urls is not a str or iterable
        If request_kwargs is provided and its length doesn't match urls
        If request_kwargs is provided and is not a dict or list of dict
    InputValueError
        If request_method is not ``get`` or ``post``
        If return_type is not ``text``, ``json``, or ``binary``
    ServiceError
        If the request fails or response cannot be processed when ``raise_status=True``
    """
    if request_method not in ("get", "post"):
        msg = "request_method"
        raise InputValueError(msg, ("get", "post"))

    handlers: dict[ReturnType, _ResponseHandler] = {  # pyright: ignore[reportAssignmentType]
        "text": lambda r: r.text(),
        "json": lambda r: r.json(),
        "binary": lambda r: r.read(),
    }

    if return_type not in handlers:
        msg = "return_type"
        raise InputValueError(msg, tuple(handlers))

    url_list, kwargs_list = _check_url_kwargs(urls, request_kwargs)

    if kwargs_list is not None:
        # Check if the request kwargs are valid
        valid_kwds = signature(ClientSession._request)  # pyright: ignore[reportPrivateUsage]
        not_found = [p for kwds in kwargs_list for p in kwds if p not in valid_kwds.parameters]
        if not_found:
            invalids = f"request_kwds ({', '.join(not_found)})"
            raise InputValueError(invalids, list(valid_kwds.parameters))

    if raise_status:
        resp: list[Any] = _run_in_event_loop(
            _batch_request(
                url_list,
                request_method,
                handlers[return_type],
                limit_per_host=limit_per_host,
                timeout=timeout,
                ssl=ssl,
                request_kwargs=kwargs_list,
                raise_status=True,
                retries=retries,
            )
        )
    else:
        resp = _run_in_event_loop(
            _batch_request(
                url_list,
                request_method,
                handlers[return_type],
                limit_per_host=limit_per_host,
                timeout=timeout,
                ssl=ssl,
                request_kwargs=kwargs_list,
                raise_status=False,
                retries=retries,
            )
        )
    if isinstance(urls, (str, URL)):
        return resp[0]
    return resp
