# fetch_overloads.py
from typing import overload, Literal, TYPE_CHECKING, TypeVar, Any
from collections.abc import Iterable

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence
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
    timeout: int = ...,
    raise_status: bool = True,
) -> None: ...

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
    timeout: int = ...,
    raise_status: Literal[False],
) -> str | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> str: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[False],
) -> dict[str, Any] | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> dict[str, Any]: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[False],
) -> bytes | None: ...

@overload
def fetch(
    urls: StrOrURL,
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: dict[str, Any] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> bytes: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[False],
) -> list[str | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["text"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> list[str]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[False],
) -> list[dict[str, Any] | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["json"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> list[dict[str, Any]]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[False],
) -> list[bytes | None]: ...

@overload
def fetch(
    urls: Iterable[StrOrURL],
    return_type: Literal["binary"],
    *,
    request_method: RequestMethod = "get",
    request_kwargs: Iterable[dict[str, Any]] | None = None,
    limit_per_host: int = ...,
    timeout: int = ...,
    raise_status: Literal[True] = True,
) -> list[bytes]: ...
