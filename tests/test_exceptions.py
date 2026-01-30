# pyright: reportMissingParameterType=false,reportArgumentType=false,reportCallIssue=false
from __future__ import annotations

import pytest
from aioresponses import aioresponses

from tiny_retriever import download, fetch, unique_filename
from tiny_retriever.exceptions import InputTypeError, InputValueError, ServiceError


class TestInputValidation:
    def test_fetch_invalid_urls_type(self):
        with pytest.raises(InputTypeError, match="Iterable or Sequence"):
            fetch(123, "text")

    def test_fetch_invalid_urls_content(self):
        with pytest.raises(InputTypeError, match="list of str"):
            fetch([1, 2, 3], "text")

    def test_fetch_invalid_return_type(self):
        with pytest.raises(InputValueError, match="Given return_type"):
            fetch(["http://example.com"], "invalid")

    def test_fetch_invalid_request_method(self):
        with pytest.raises(InputValueError, match="Given request_method"):
            fetch(["http://example.com"], "text", request_method="invalid")

    def test_fetch_request_kwargs_length_mismatch(self):
        with pytest.raises(InputTypeError, match="list of the same length as urls"):
            fetch(
                ["http://example.com/1", "http://example.com/2"],
                "text",
                request_kwargs=[{"params": {"a": "1"}}],
            )

    def test_fetch_request_kwargs_not_dict(self):
        with pytest.raises(InputTypeError, match="list of dict"):
            fetch(["http://example.com/1"], "text", request_kwargs=["invalid"])

    def test_fetch_request_kwargs_invalid_keys(self):
        with pytest.raises(InputValueError, match="invalid"):
            fetch(["http://example.com/1"], "text", request_kwargs=[{"invalid": "value"}])

    def test_download_length_mismatch(self):
        with pytest.raises(InputTypeError, match="lists of the same size"):
            download(["http://example.com/1", "http://example.com/2"], ["file1.txt"])

    def test_unique_filename_invalid_params(self):
        with pytest.raises(InputTypeError, match=r"dict or multidict\.MultiDict"):
            unique_filename("http://example.com", params=["invalid"])

    def test_unique_filename_invalid_data(self):
        with pytest.raises(InputTypeError, match="dict or str"):
            unique_filename("http://example.com", data=["invalid"])


class TestServiceError:
    def test_http_500(self):
        with aioresponses() as m:
            m.get("http://example.com/error", status=500)
            with pytest.raises(ServiceError):
                fetch(["http://example.com/error"], "text")

    def test_http_404(self):
        with aioresponses() as m:
            m.get("http://example.com/missing", status=404)
            with pytest.raises(ServiceError):
                fetch(["http://example.com/missing"], "text")

    def test_service_error_message_contains_url(self):
        with aioresponses() as m:
            m.get("http://example.com/fail", status=500)
            with pytest.raises(ServiceError, match=r"example\.com/fail"):
                fetch("http://example.com/fail", "text")

    def test_download_http_error(self):
        with aioresponses() as m:
            m.get("http://example.com/file", status=503)
            with pytest.raises(ServiceError):
                download("http://example.com/file", "test_dl_err.txt")


class TestExceptionClasses:
    def test_service_error_attrs(self):
        err = ServiceError("connection refused", "http://example.com")
        assert "connection refused" in err.message
        assert "http://example.com" in err.message

    def test_input_value_error_message(self):
        err = InputValueError("method", ("get", "post"))
        assert "method" in err.message
        assert "get" in str(err)

    def test_input_type_error_message(self):
        err = InputTypeError("urls", "list of str")
        assert "urls" in err.message
        assert "list of str" in str(err)
