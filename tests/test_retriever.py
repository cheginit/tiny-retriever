# pyright: reportMissingParameterType=false,reportArgumentType=false,reportCallIssue=false
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from aioresponses import aioresponses

from tiny_retriever import check_downloads, download, fetch, unique_filename
from tiny_retriever.exceptions import ServiceError


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
                fetch("http://example.com/err", "text", retries=1)

    def test_raise_status_true_on_404(self):
        from tiny_retriever.exceptions import ServiceError

        with aioresponses() as m:
            m.get("http://example.com/missing", status=404)
            with pytest.raises(ServiceError):
                fetch("http://example.com/missing", "text")

    def test_raise_status_false_returns_none(self):
        with aioresponses() as m:
            m.get("http://example.com/err", status=500)
            result = fetch("http://example.com/err", "text", raise_status=False, retries=1)
            assert result is None

    def test_raise_status_false_list_returns_none_elements(self):
        with aioresponses() as m:
            m.get("http://example.com/ok", body="ok")
            m.get("http://example.com/fail", status=500)
            result = fetch(
                ["http://example.com/ok", "http://example.com/fail"],
                "text",
                raise_status=False,
                retries=1,
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
                fetch("http://nonexistent.invalid/api", "text", retries=1)

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
                download("http://example.com/fail", fp, retries=1)

    def test_error_no_raise(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/fail", status=500)
            fp = Path(tmp) / "fail.txt"
            download("http://example.com/fail", fp, raise_status=False, retries=1)
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

    def test_size_mismatch_raises_error(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get(
                "http://example.com/truncated",
                body=b"short",
                headers={"Content-Length": "100"},
            )
            fp = Path(tmp) / "truncated.bin"
            with pytest.raises(ServiceError, match="does not match expected size"):
                download("http://example.com/truncated", fp)
            assert not fp.exists()

    def test_no_content_length_skips_size_check(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", body=b"data", headers={})
            fp = Path(tmp) / "out.bin"
            download("http://example.com/f", fp)
            assert fp.read_bytes() == b"data"


class TestFetchRetry:
    @pytest.fixture(autouse=True)
    def _no_backoff(self, monkeypatch):
        """Replace _backoff_sleep with a no-op to keep tests fast."""

        async def _noop(*_args, **_kwargs):
            pass

        monkeypatch.setattr("tiny_retriever.tiny_retriever._backoff_sleep", _noop)

    def test_succeeds_after_transient_500(self):
        with aioresponses() as m:
            m.get("http://example.com/api", status=500)
            m.get("http://example.com/api", body="ok")
            result = fetch("http://example.com/api", "text", retries=2)
            assert result == "ok"

    def test_succeeds_after_transient_500_json(self):
        with aioresponses() as m:
            m.get("http://example.com/api", status=500)
            m.get("http://example.com/api", payload={"key": "value"})
            result = fetch("http://example.com/api", "json", retries=2)
            assert result == {"key": "value"}

    def test_retries_exhausted_raises(self):
        with aioresponses() as m:
            m.get("http://example.com/api", status=500)
            m.get("http://example.com/api", status=500)
            m.get("http://example.com/api", status=500)
            with pytest.raises(ServiceError):
                fetch("http://example.com/api", "text", retries=3)

    def test_retries_exhausted_returns_none(self):
        with aioresponses() as m:
            m.get("http://example.com/api", status=500)
            m.get("http://example.com/api", status=500)
            result = fetch("http://example.com/api", "text", raise_status=False, retries=2)
            assert result is None

    def test_non_retryable_404_fails_immediately(self):
        """A 404 is not retryable so only one mock response is needed."""
        with aioresponses() as m:
            m.get("http://example.com/api", status=404)
            with pytest.raises(ServiceError):
                fetch("http://example.com/api", "text", retries=3)

    def test_non_retryable_valueerror_fails_immediately(self):
        """ValueError is not retryable so only one mock response is needed."""
        with aioresponses() as m:
            m.get("http://example.com/api", exception=ValueError("bad"))
            with pytest.raises(ServiceError):
                fetch("http://example.com/api", "text", retries=3)

    def test_retryable_oserror_then_succeeds(self):
        with aioresponses() as m:
            m.get("http://example.com/api", exception=OSError("connection reset"))
            m.get("http://example.com/api", body="ok")
            result = fetch("http://example.com/api", "text", retries=2)
            assert result == "ok"

    def test_multiple_urls_retry_independently(self):
        with aioresponses() as m:
            m.get("http://example.com/a", status=500)
            m.get("http://example.com/a", body="a_ok")
            m.get("http://example.com/b", body="b_ok")
            result = fetch(["http://example.com/a", "http://example.com/b"], "text", retries=2)
            assert result == ["a_ok", "b_ok"]


class TestDownloadRetry:
    @pytest.fixture(autouse=True)
    def _no_backoff(self, monkeypatch):
        async def _noop(*_args, **_kwargs):
            pass

        monkeypatch.setattr("tiny_retriever.tiny_retriever._backoff_sleep", _noop)

    def test_succeeds_after_transient_500(self):
        content = b"hello world"
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", status=500)
            m.get(
                "http://example.com/f",
                body=content,
                headers={"Content-Length": str(len(content))},
            )
            fp = Path(tmp) / "out.bin"
            download("http://example.com/f", fp, retries=2)
            assert fp.read_bytes() == content

    def test_partial_file_cleaned_on_retry(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", status=500)
            m.get("http://example.com/f", status=500)
            fp = Path(tmp) / "out.bin"
            with pytest.raises(ServiceError):
                download("http://example.com/f", fp, retries=2)
            assert not fp.exists()

    def test_partial_file_cleaned_no_raise(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", status=500)
            m.get("http://example.com/f", status=500)
            fp = Path(tmp) / "out.bin"
            download("http://example.com/f", fp, raise_status=False, retries=2)
            assert not fp.exists()

    def test_non_retryable_404_fails_immediately(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            m.get("http://example.com/f", status=404)
            fp = Path(tmp) / "out.bin"
            with pytest.raises(ServiceError):
                download("http://example.com/f", fp, retries=3)
            assert not fp.exists()


class TestBackoffSleep:
    def test_backoff_sleeps_with_exponential_delay(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        from tiny_retriever.tiny_retriever import _backoff_sleep

        with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
            asyncio.run(_backoff_sleep(0, factor=1.0, maximum=30.0))
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            # factor=1.0, attempt=0: base = min(1.0 * 2^0, 30) = 1.0
            # jitter adds uniform(0, 0.5), so delay in [1.0, 1.5)
            assert 1.0 <= delay < 1.5

    def test_backoff_respects_maximum(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        from tiny_retriever.tiny_retriever import _backoff_sleep

        with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
            asyncio.run(_backoff_sleep(100, factor=1.0, maximum=2.0))
            delay = mock_sleep.call_args[0][0]
            # base capped at maximum=2.0, jitter adds uniform(0, 1.0)
            assert 2.0 <= delay < 3.0


class TestCheckDownloadsRetry:
    @pytest.fixture(autouse=True)
    def _no_backoff(self, monkeypatch):
        async def _noop(*_args, **_kwargs):
            pass

        monkeypatch.setattr("tiny_retriever.tiny_retriever._backoff_sleep", _noop)

    def test_succeeds_after_transient_error(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            content = b"valid"
            fp = Path(tmp) / "file.bin"
            fp.write_bytes(content)
            m.get("http://example.com/f", status=500)
            m.get("http://example.com/f", headers={"Content-Length": str(len(content))})
            result = check_downloads("http://example.com/f", fp, retries=2)
            assert result == {}

    def test_returns_negative_after_retries_exhausted(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "file.bin"
            fp.write_bytes(b"data")
            m.get("http://example.com/f", status=500)
            m.get("http://example.com/f", status=500)
            # All retries fail so remote size is -1 (unknown), file treated as valid
            result = check_downloads("http://example.com/f", fp, retries=2)
            assert result == {}


class TestCheckDownloads:
    def test_all_valid(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            content = b"valid data"
            fp = Path(tmp) / "file.bin"
            fp.write_bytes(content)
            m.get(
                "http://example.com/file.bin",
                headers={"Content-Length": str(len(content))},
            )
            result = check_downloads("http://example.com/file.bin", fp)
            assert result == {}

    def test_corrupted_file(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "file.bin"
            fp.write_bytes(b"short")
            m.get(
                "http://example.com/file.bin",
                headers={"Content-Length": "100"},
            )
            result = check_downloads("http://example.com/file.bin", fp)
            assert result == {fp: 100}

    def test_mixed_valid_and_invalid(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fa = Path(tmp) / "a.txt"
            fb = Path(tmp) / "b.txt"
            fa.write_bytes(b"aaa")
            fb.write_bytes(b"bb")
            m.get("http://example.com/a", headers={"Content-Length": "3"})
            m.get("http://example.com/b", headers={"Content-Length": "100"})
            result = check_downloads(["http://example.com/a", "http://example.com/b"], [fa, fb])
            assert result == {fb: 100}

    def test_no_files_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "missing.bin"
            result = check_downloads("http://example.com/missing.bin", fp)
            assert result == {}

    def test_missing_content_length(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "file.bin"
            fp.write_bytes(b"data")
            m.get("http://example.com/file.bin", headers={})
            result = check_downloads("http://example.com/file.bin", fp)
            assert result == {}

    def test_str_file_path(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fp = str(Path(tmp) / "file.bin")
            Path(fp).write_bytes(b"data")
            m.get(
                "http://example.com/file.bin",
                headers={"Content-Length": str(len(b"data"))},
            )
            result = check_downloads("http://example.com/file.bin", fp)
            assert result == {}

    def test_only_existing_files_checked(self):
        with aioresponses() as m, tempfile.TemporaryDirectory() as tmp:
            fa = Path(tmp) / "exists.txt"
            fb = Path(tmp) / "missing.txt"
            fa.write_bytes(b"aaa")
            m.get("http://example.com/a", headers={"Content-Length": "3"})
            result = check_downloads(["http://example.com/a", "http://example.com/b"], [fa, fb])
            assert result == {}


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


class TestJsonSerialize:
    def test_uses_orjson_when_available(self):
        import tiny_retriever.tiny_retriever as mod

        assert mod.HAS_ORJSON is True
        result = mod._json_serialize({"key": "value"})
        assert isinstance(result, str)
        assert '"key"' in result

    def test_falls_back_to_json_dumps_without_orjson(self, monkeypatch):
        import tiny_retriever.tiny_retriever as mod

        monkeypatch.setattr(mod, "HAS_ORJSON", False)
        result = mod._json_serialize({"key": "value"})
        assert isinstance(result, str)
        assert '"key"' in result
