# fetch_overloads.py
from typing import overload, Literal, TYPE_CHECKING, TypeVar, Any
from collections.abc import Iterable

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence
    from ssl import SSLContext
    from aiohttp.typedefs import StrOrURL

    T = TypeVar("T")
    ResponseT = TypeVar("ResponseT", str, bytes, dict[str, Any])
    ReturnType = Literal["text", "json", "binary"]
    RequestMethod = Literal["get", "post"]

def download(
    urls: StrOrURL | Sequence[StrOrURL],
    file_paths: Path | str | Sequence[Path | str],
    *,
    chunk_size: int = ...,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: bool = True,
    retries: int = ...,
) -> None: ...

def check_downloads(
    urls: StrOrURL | Sequence[StrOrURL],
    file_paths: Path | str | Sequence[Path | str],
    *,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    retries: int = ...,
) -> dict[Path, int]: ...

def unique_filename(
    url: StrOrURL,
    *,
    params: dict[str, Any] | Iterable[tuple[str, Any]] | None = None,
    data: dict[str, Any] | str | None = None,
    prefix: str | None = None,
    file_extension: str = "",
) -> str: ...


@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> str | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> str: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> dict[str, Any] | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> dict[str, Any]: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> bytes | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> bytes: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> list[str | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> list[str]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> list[dict[str, Any] | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> list[dict[str, Any]]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[False],
    retries: int = ...,
) -> list[bytes | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: float = ...,
    ssl: bool | SSLContext = ...,
    raise_status: Literal[True] = True,
    retries: int = ...,
) -> list[bytes]: ...
