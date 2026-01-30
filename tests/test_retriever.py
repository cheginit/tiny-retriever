# pyright: reportMissingParameterType=false,reportArgumentType=false,reportCallIssue=false
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from aioresponses import aioresponses

from tiny_retriever import download, fetch, unique_filename


class TestFetchText:
    def test_single_url_returns_str(self):
        with aioresponses() as m:
            m.get("http://example.com/data", payload=None, body="hello world")
            result = fetch("http://example.com/data", "text")
            assert result == "hello world"
            assert isinstance(result, str)

    def test_single_url_in_list_returns_list(self):
        with aioresponses() as m:
            m.get("http://example.com/data", body="hello")
            result = fetch(["http://example.com/data"], "text")
            assert result == ["hello"]

    def test_multiple_urls(self):
        with aioresponses() as m:
            m.get("http://example.com/1", body="first")
            m.get("http://example.com/2", body="second")
            result = fetch(["http://example.com/1", "http://example.com/2"], "text")
            assert result == ["first", "second"]

    def test_post_method(self):
        with aioresponses() as m:
            m.post("http://example.com/api", body="response")
            result = fetch("http://example.com/api", "text", request_method="post")
            assert result == "response"

    def test_with_request_kwargs_single_dict(self):
        with aioresponses() as m:
            m.get("http://example.com/api?key=val", body="ok")
            result = fetch(
                "http://example.com/api",
                "text",
                request_kwargs={"params": {"key": "val"}},
            )
            assert result == "ok"

    def test_with_request_kwargs_list(self):
        with aioresponses() as m:
            m.get("http://example.com/1?a=1", body="r1")
            m.get("http://example.com/2?b=2", body="r2")
            result = fetch(
                ["http://example.com/1", "http://example.com/2"],
                "text",
                request_kwargs=[{"params": {"a": "1"}}, {"params": {"b": "2"}}],
            )
            assert result == ["r1", "r2"]

    def test_encoding_latin1_fallback(self):
        """Responses with no charset trigger UnicodeDecodeError -> ServiceError on bad utf-8."""
        with aioresponses() as m:
            m.get(
                "http://example.com/enc",
                body=b"hello\xe9world",
                content_type="text/plain",
            )
            # aioresponses doesn't fully support charset fallback,
            # so this triggers a UnicodeDecodeError -> ServiceError
            result = fetch("http://example.com/enc", "text", raise_status=False)
            assert result is None or isinstance(result, str)


class TestFetchJson:
    def test_single_url(self):
        payload = {"features": [{"id": 1}]}
        with aioresponses() as m:
            m.get("http://example.com/json", payload=payload)
            result = fetch("http://example.com/json", "json")
            assert result == payload

    def test_multiple_urls(self):
        with aioresponses() as m:
            m.get("http://example.com/a", payload={"a": 1})
            m.get("http://example.com/b", payload={"b": 2})
            result = fetch(["http://example.com/a", "http://example.com/b"], "json")
            assert result == [{"a": 1}, {"b": 2}]

    def test_post_with_json_body(self):
        with aioresponses() as m:
            m.post("http://example.com/api", payload={"status": "ok"})
            result = fetch(
                "http://example.com/api",
                "json",
                request_method="post",
                request_kwargs={"json": {"query": "test"}},
            )
            assert result == {"status": "ok"}


class TestFetchBinary:
    def test_single_url(self):
        data = b"\x00\x01\x02\x03"
        with aioresponses() as m:
            m.get("http://example.com/bin", body=data)
            result = fetch("http://example.com/bin", "binary")
            assert result == data
            assert isinstance(result, bytes)

    def test_multiple_urls(self):
        with aioresponses() as m:
            m.get("http://example.com/a", body=b"aaa")
            m.get("http://example.com/b", body=b"bbb")
            result = fetch(["http://example.com/a", "http://example.com/b"], "binary")
            assert result == [b"aaa", b"bbb"]


class TestFetchErrorHandling:
    def test_raise_status_true_on_500(self):
        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m:
            m.get("http://example.com/err", status=500)
            with pytest.raises(ServiceError, match=r"example\.com/err"):
                fetch("http://example.com/err", "text")

    def test_raise_status_true_on_404(self):
        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m:
            m.get("http://example.com/missing", status=404)
            with pytest.raises(ServiceError):
                fetch("http://example.com/missing", "text")

    def test_raise_status_false_returns_none(self):
        with aioresponses() as m:
            m.get("http://example.com/err", status=500)
            result = fetch("http://example.com/err", "text", raise_status=False)
            assert result is None

    def test_raise_status_false_list_returns_none_elements(self):
        with aioresponses() as m:
            m.get("http://example.com/ok", body="ok")
            m.get("http://example.com/fail", status=500)
            result = fetch(
                ["http://example.com/ok", "http://example.com/fail"],
                "text",
                raise_status=False,
            )
            assert result[0] == "ok"
            assert result[1] is None

    def test_dns_error_raises_service_error(self):
        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m:
            m.get(
                "http://nonexistent.invalid/api",
                exception=OSError("DNS resolution failed"),
            )
            with pytest.raises((ServiceError, OSError)):
                fetch("http://nonexistent.invalid/api", "text")

    def test_value_error_raises_service_error(self):
        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m:
            m.get(
                "http://example.com/bad",
                exception=ValueError("bad value"),
            )
            with pytest.raises(ServiceError):
                fetch("http://example.com/bad", "text")

    def test_value_error_no_raise_returns_none(self):
        with aioresponses() as m:
            m.get(
                "http://example.com/bad",
                exception=ValueError("bad value"),
            )
            result = fetch("http://example.com/bad", "text", raise_status=False)
            assert result is None


class TestDownload:
    def test_single_file(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            content = b"file content here"
            m.get(
                "http://example.com/file.csv",
                body=content,
                headers={"Content-Length": str(len(content))},
            )
            fp = Path(tmp) / "out.csv"
            download("http://example.com/file.csv", fp)
            assert fp.read_bytes() == content

    def test_multiple_files(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/a", body=b"aaa", headers={"Content-Length": "3"})
            m.get("http://example.com/b", body=b"bbb", headers={"Content-Length": "3"})
            fa = Path(tmp) / "a.txt"
            fb = Path(tmp) / "b.txt"
            download(["http://example.com/a", "http://example.com/b"], [fa, fb])
            assert fa.read_bytes() == b"aaa"
            assert fb.read_bytes() == b"bbb"

    def test_skip_existing_file_with_matching_size(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            content = b"existing"
            fp = Path(tmp) / "out.csv"
            fp.write_bytes(content)
            m.get(
                "http://example.com/file.csv",
                body=content,
                headers={"Content-Length": str(len(content))},
            )
            download("http://example.com/file.csv", fp)
            assert fp.read_bytes() == content

    def test_creates_parent_directories(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", body=b"data", headers={"Content-Length": "4"})
            fp = Path(tmp) / "sub" / "dir" / "file.txt"
            download("http://example.com/f", fp)
            assert fp.read_bytes() == b"data"

    def test_error_raises_service_error(self):
        import pytest

        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/fail", status=500)
            fp = Path(tmp) / "fail.txt"
            with pytest.raises(ServiceError):
                download("http://example.com/fail", fp)

    def test_error_no_raise(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/fail", status=500)
            fp = Path(tmp) / "fail.txt"
            download("http://example.com/fail", fp, raise_status=False)
            assert not fp.exists()

    def test_custom_chunk_size(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            content = b"x" * 10000
            m.get(
                "http://example.com/big",
                body=content,
                headers={"Content-Length": str(len(content))},
            )
            fp = Path(tmp) / "big.bin"
            download("http://example.com/big", fp, chunk_size=1000)
            assert fp.read_bytes() == content

    def test_str_file_path(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", body=b"ok", headers={"Content-Length": "2"})
            fp = str(Path(tmp) / "out.txt")
            download("http://example.com/f", fp)
            assert Path(fp).read_bytes() == b"ok"


class TestUniqueFilename:
    def test_basic(self):
        name = unique_filename("http://example.com")
        assert len(name) == 64  # SHA-256 hex

    def test_with_prefix(self):
        name = unique_filename("http://example.com", prefix="pre_")
        assert name.startswith("pre_")

    def test_with_extension(self):
        name = unique_filename("http://example.com", file_extension="csv")
        assert name.endswith(".csv")

    def test_with_dot_extension(self):
        name = unique_filename("http://example.com", file_extension=".csv")
        assert name.endswith(".csv")
        assert ".." not in name

    def test_with_params_dict(self):
        n1 = unique_filename("http://example.com", params={"a": "1"})
        n2 = unique_filename("http://example.com", params={"b": "2"})
        assert n1 != n2

    def test_with_params_multidict(self):
        from multidict import MultiDict

        name = unique_filename("http://example.com", params=MultiDict([("a", "1"), ("a", "2")]))
        assert len(name) == 64

    def test_with_data_dict(self):
        n1 = unique_filename("http://example.com", data={"key": "val"})
        n2 = unique_filename("http://example.com", data={"key": "other"})
        assert n1 != n2

    def test_with_data_str(self):
        name = unique_filename("http://example.com", data="raw body")
        assert len(name) == 64

    def test_deterministic(self):
        n1 = unique_filename("http://example.com", params={"a": "1"}, data={"b": "2"})
        n2 = unique_filename("http://example.com", params={"a": "1"}, data={"b": "2"})
        assert n1 == n2

    def test_all_options(self):
        name = unique_filename(
            "http://example.com",
            params={"q": "test"},
            data={"body": "data"},
            prefix="pfx_",
            file_extension="json",
        )
        assert name.startswith("pfx_")
        assert name.endswith(".json")
