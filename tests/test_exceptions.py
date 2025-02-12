# pyright: reportMissingParameterType=false,reportArgumentType=false,reportCallIssue=false
from __future__ import annotations

import pytest

from tiny_retriever import download, fetch, unique_filename
from tiny_retriever.exceptions import InputTypeError, InputValueError, ServiceError


def test_unique_filename_invalid_params():
    """Test that unique_filename raises InputTypeError for invalid params type."""
    with pytest.raises(InputTypeError, match="dict or multidict.MultiDict"):
        unique_filename("http://wrong.url", params=["invalid"])


def test_unique_filename_invalid_data():
    """Test that unique_filename raises InputTypeError for invalid data type."""
    with pytest.raises(InputTypeError, match="dict or str"):
        unique_filename("http://wrong.url", data=["invalid"])


def test_fetch_invalid_urls_type():
    """Test that fetch raises InputTypeError when urls is not an Iterable."""
    with pytest.raises(InputTypeError, match="Iterable or Sequence"):
        fetch(123, "text")


def test_fetch_invalid_urls_content():
    """Test that fetch raises InputTypeError when urls contains non-string elements."""
    with pytest.raises(InputTypeError, match="list of str"):
        fetch([1, 2, 3], "text")


def test_fetch_invalid_request_kwargs_length():
    """Test that fetch raises InputTypeError when request_kwargs length doesn't match urls."""
    urls = ["http://wrong.url/1", "http://wrong.url/2"]
    kwargs = [{"param": "value"}]

    with pytest.raises(InputTypeError, match="list of the same length as urls"):
        fetch(urls, "text", request_kwargs=kwargs)


def test_fetch_invalid_request_kwargs_type():
    """Test that fetch raises InputTypeError when request_kwargs contains non-dict elements."""
    urls = ["http://wrong.url/1"]
    kwargs = ["invalid"]

    with pytest.raises(InputTypeError, match="list of dict"):
        fetch(urls, "text", request_kwargs=kwargs)


def test_fetch_invalid_request_kwargs_keys():
    """Test that fetch raises InputTypeError when request_kwargs contains non-dict elements."""
    urls = ["http://wrong.url/1"]
    kwargs = [{"invalid": "value"}]

    with pytest.raises(InputValueError, match="(invalid)"):
        fetch(urls, "text", request_kwargs=kwargs)


def test_fetch_invalid_return_type():
    """Test that fetch raises InputValueError for invalid return_type."""
    with pytest.raises(InputValueError, match="Given return_type"):
        fetch(["http://wrong.url"], "invalid")


def test_fetch_invalid_request_method():
    """Test that fetch raises InputValueError for invalid request_method."""
    with pytest.raises(InputValueError, match="Given request_method"):
        fetch(["http://wrong.url"], "text", request_method="invalid")


def test_service_error():
    with pytest.raises(ServiceError):
        fetch(["http://wrong.url/api"], "text")

    with pytest.raises(ServiceError):
        download(["http://wrong.url/file.txt"], ["downloaded.txt"])


def test_download_invalid_length():
    """Test that fetch raises InputTypeError when request_kwargs length doesn't match urls."""
    urls = ["http://wrong.url/1", "http://wrong.url/2"]
    files = ["file1.txt"]

    with pytest.raises(InputTypeError, match="lists of the same size"):
        download(urls, files)
