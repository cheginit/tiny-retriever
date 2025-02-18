# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

## [0.1.2] - 2025-02-18

### Changed

- More robust handling of starting and stopping threads by lazy generation
    of a dedicated thread for the library and making `_AsyncLoopThread` a singleton.
    This can avoid issues that might arise from using TinyRetriever with other
    libraries that also use threads such as `shapely`.

## [0.1.1] - 2025-02-12

### Added

- Add support for passing single URL/key to both `fetch` and `download` functions. This
    makes using the function easier when there's just one query to be made. The result
    is returned as a single item too.

### Changed

- Check the validity of the input `request_kwargs` in `fetch` function based on the
    acceptable args for `aiohttp.ClientSession.request` method.

## [0.1.0] - 2025-02-11

Initial release.
