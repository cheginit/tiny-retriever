# fetch_overloads.py
from typing import overload, Literal, TYPE_CHECKING, TypeVar, Any, Protocol
from collections.abc import Iterable

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence
    from aiohttp import ClientResponse
    from aiohttp.typedefs import StrOrURL

    T = TypeVar("T")
    ResponseT = TypeVar("ResponseT", str, bytes, dict[str, Any])
    ReturnType = Literal["text", "json", "binary"]
    RequestMethod = Literal["get", "post"]


class ResponseHandler(Protocol):
    async def __call__(self, response: ClientResponse) -> ResponseT: ...

@overload
async def _batch_request(
    urls: list[StrOrURL],
    method: RequestMethod,
    response_handler: ResponseHandler,
    limit_per_host: int,
    timeout: int,
    request_kwargs: list[dict[str, Any]] | None,
    raise_status: Literal[False],
) -> list[ResponseT | None]: ...


@overload
async def _batch_request(
    urls: list[StrOrURL],
    method: RequestMethod,
    response_handler: ResponseHandler,
    limit_per_host: int,
    timeout: int,
    request_kwargs: list[dict[str, Any]] | None,
    raise_status: Literal[True],
) -> list[ResponseT]: ...

def download(
    urls: StrOrURL | Sequence[StrOrURL],
    file_paths: Sequence[Path | str],
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
