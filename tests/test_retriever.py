from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

from tiny_retriever import download, fetch


def test_encoding():
    url = "https://api.epa.gov/StreamCat/streams/variable_info"
    resp = fetch(url, "text")
    assert resp[:3] == "IND"


def test_binary():
    west, south, east, north = (-69.77, 45.07, -69.31, 45.45)
    base_url = "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1299"
    dates_itr = [(datetime(y, 1, 1), datetime(y, 1, 31)) for y in range(2000, 2005)]
    urls, kwds = zip(
        *(
            (
                f"{base_url}/MCD13.A{s.year}.unaccum.nc4",
                {
                    "params": {
                        "var": "NDVI",
                        "north": str(north),
                        "west": str(west),
                        "east": str(east),
                        "south": str(south),
                        "disableProjSubset": "on",
                        "horizStride": "1",
                        "time_start": s.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "time_end": e.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "timeStride": "1",
                        "addLatLon": "true",
                        "accept": "netcdf",
                    },
                },
            )
            for s, e in dates_itr
        ),
    )

    r = fetch(urls, "binary", request_kwargs=kwds)
    assert sys.getsizeof(r[0]) == 986161

    r = fetch(urls[0], "binary", request_kwargs=kwds[0])
    assert sys.getsizeof(r) == 986161


def test_json():
    urls = ["https://api.water.usgs.gov/nldi/linked-data/comid/position"]
    kwds = [
        {
            "params": {
                "f": "json",
                "coords": "POINT(-68.325 45.0369)",
            },
        },
    ]
    resp = fetch(urls, "json", request_kwargs=kwds, raise_status=False)
    resp = [r for r in resp if r is not None]
    r_id = resp[0]["features"][0]["properties"]["identifier"]
    assert r_id == "2675320"


def test_text_post():
    base = "https://waterservices.usgs.gov/nwis/site/?"
    station_id = "01646500"
    urls = [
        "&".join([base, "format=rdb", f"sites={','.join([station_id] * 20)}", "siteStatus=all"])
    ]

    r = fetch(urls, "text", request_method="post")
    r_id = r[0].split("\n")[-2].split("\t")[1]

    assert r_id == station_id


def test_stream():
    url = "https://freetestdata.com/wp-content/uploads/2021/09/Free_Test_Data_500KB_CSV-1.csv"
    with tempfile.TemporaryDirectory(dir=".") as temp:
        file = Path(temp) / "test.csv"
        download([url], [file])
        assert file.stat().st_size == 512789
        download(url, file)
        assert file.stat().st_size == 512789


def test_stream_chunked():
    url = "https://freetestdata.com/wp-content/uploads/2021/09/Free_Test_Data_500KB_CSV-1.csv"
    with tempfile.TemporaryDirectory(dir=".") as temp:
        file = Path(temp) / "test.csv"
        download([url], [file], chunk_size=5000)
        assert file.stat().st_size == 512789


def test_ordered_return():
    stations = ["11073495", "08072300", "01646500"]
    url = "https://waterservices.usgs.gov/nwis/site"
    urls, kwds = zip(
        *((url, {"params": {"format": "rdb", "sites": s, "siteStatus": "all"}}) for s in stations),
    )
    resp = fetch(urls, "text", request_kwargs=kwds)
    assert [r.split("\n")[-2].split("\t")[1] for r in resp] == stations


def test_fetch_invalid_response():
    """Test that fetch raises InputTypeError when request_kwargs contains non-dict elements."""
    urls = ["http://wrong.url/1"]
    kwargs = [{"params": "value"}]

    resp = fetch(urls, "text", request_kwargs=kwargs, raise_status=False)
    assert resp[0] is None
