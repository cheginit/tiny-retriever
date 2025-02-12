# TinyRetriever: HTTP Requests Made Easy

[![PyPi](https://img.shields.io/pypi/v/tiny-retriever.svg)](https://pypi.python.org/pypi/tiny-retriever)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/tiny-retriever.svg)](https://anaconda.org/conda-forge/tiny-retriever)
[![CodeCov](https://codecov.io/gh/cheginit/tiny-retriever/branch/main/graph/badge.svg)](https://codecov.io/gh/cheginit/tiny-retriever)
[![Python Versions](https://img.shields.io/pypi/pyversions/tiny-retriever.svg)](https://pypi.python.org/pypi/tiny-retriever)

[![Downloads](https://static.pepy.tech/badge/tiny-retriever)](https://pepy.tech/project/tiny-retriever)
[![CodeFactor](https://www.codefactor.io/repository/github/cheginit/tiny-retriever/badge)](https://www.codefactor.io/repository/github/cheginit/tiny-retriever)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/cheginit/tiny-retriever/HEAD?labpath=docs%2Fexamples)

TinyRetriever is a lightweight synchronous wrapper for
[AIOHTTP](https://docs.aiohttp.org/en/stable/) that abstracts away the complexities of
making asynchronous HTTP requests. It is designed to be simple, easy to use, and
efficient. TinyRetriever is built on top of AIOHTTP and
[AIOFiles](https://github.com/Tinche/aiofiles), which are popular asynchronous HTTP
client and file management libraries for Python.

📚 Full documentation is available [here](https://tiny-retriever.readthedocs.io).

## Features

TinyRetriever provides the following features:

- **Concurrent Downloads**: Efficiently download multiple files simultaneously
- **Flexible Response Types**: Get responses as text, JSON, or binary data
- **Rate Limiting**: Built-in per-host connection limiting to respect server constraints
- **Streaming Support**: Stream large files efficiently with customizable chunk sizes
- **Unique Filenames**: Generate unique filenames based on query parameters
- **Works in Jupyter Notebooks**: Easily use TinyRetriever in Jupyter notebooks without
    any additional setup or dependencies
- **Robust Error Handling**: Optional status raising and comprehensive error messages
- **Performance Optimized**: Uses [`orjson`](https://github.com/ijl/orjson) when
    available for up to 14x faster JSON parsing

TinyRetriever does not use `nest-asyncio`, instead it creates and manages a dedicated
thread for running the event loop. This allows you to use TinyRetriever in Jupyter
notebooks and other environments where the event loop is already running.

There are three main functions in TinyRetriever:

- `download`: Download files concurrently;
- `fetch`: Fetch queries concurrently and return responses as text, JSON, or binary;
- `unique_filename`: Generate unique filenames based on query parameters.

## Installation

Choose your preferred installation method:

### Using `pip`

```console
pip install tiny-retriever
```

### Using `micromamba`

```console
micromamba install -c conda-forge tiny-retriever
```

Alternatively, you can use `conda` or `mamba`.

## Quick Start Guide

Please refer to the [documentation](https://tiny-retriever.readthedocs.io) for detailed
usage instructions and more elaborate examples.

### Downloading Files

```python
from pathlib import Path
import tiny_retriever as terry

urls = ["https://example.com/file1.pdf", "https://example.com/file2.pdf"]
paths = [Path("downloads/file1.pdf"), Path("downloads/file2.pdf")]
# or generate unique filenames
paths = (terry.unique_filename(u) for u in urls)
paths = [Path("downloads", p) for p in paths]

# Download files concurrently
terry.download(urls, paths)
```

### Fetching Data

```python
urls = ["https://api.example.com/data1", "https://api.example.com/data2"]

# Get JSON responses
json_responses = terry.fetch(urls, "json")

# Get text responses
text_responses = terry.fetch(urls, "text")

# Get binary responses
binary_responses = terry.fetch(urls, "binary")
```

### Generate Unique Filenames

```python
url = "https://api.example.com/data"
params = {"key": "value"}

# Generate unique filename based on URL and parameters
filename = terry.unique_filename(url, params=params, file_extension=".json")
```

## Advanced Usage

### Custom Request Parameters

Note that you can also pass a single url and a dictionary of request parameters to the
`fetch` function. The default network related parameters are conservative and can be
modified as needed.

```python
urls = "https://api.example.com/data"
kwargs = {"headers": {"Authorization": "Bearer token"}}

responses = terry.fetch(
    urls,
    return_type="json",
    request_method="post",
    request_kwargs=kwargs,
    limit_per_host=2,
    timeout=30,
)
```

### Error Handling

```python
from tiny_retriever import fetch, ServiceError

try:
    responses = fetch(urls, return_type="json", raise_status=True)
except ServiceError as e:
    print(f"Request failed: {e}")
```

## Configuration

TinyRetriever can be configured through environment variables:

- `MAX_CONCURRENT_CALLS`: Maximum number of concurrent requests (default: 10)
- Default chunk size for downloads: 1MB
- Default timeout: 5 minutes
- Default connections per host: 4

## Contributing

We welcome contributions! Please see the
[contributing](https://tiny-retriever.readthedocs.io/en/latest/CONTRIBUTING/) section
for guidelines and instructions.

## License

This project is licensed under the terms of the MIT license.
