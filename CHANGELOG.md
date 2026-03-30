# Changelog

All notable changes to this project will be documented in this file. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add retry with exponential backoff for transient errors

## [0.2.1] - 2026-02-09

### Added

- Add a new function to check for corrupted download files.

## [0.2.0] - 2026-01-30

### Added

- Rewrite all tests using aioresponses.
- Add support for toggling ssl verification.

## [0.1.3] - 2025-02-20

### Added

- Change the timeout from session to request level.

## [0.1.2] - 2025-02-18

### Fixed

- Make \_AsyncLoopThread a singleton
- More robust handling of thread starting/stopping to avoid issues with other threadsafe
    libraries.

## [0.1.1] - 2025-02-12

### Added

- Check if the input query parameters that are apssed to aiohttp are valid

## [0.1.0] - 2025-02-12

### Added

- Add support for passing a single url/kwargs instead of a list.

### Fixed

- If the input is a single url/kwargs return a response instead of list.

### New Contributors

- @ made their first contribution
- @cheginit made their first contribution

[0.1.1]: https://github.com/cheginit/tiny-retriever/compare/v0.1.0...v0.1.1
[0.1.2]: https://github.com/cheginit/tiny-retriever/compare/v0.1.1...v0.1.2
[0.1.3]: https://github.com/cheginit/tiny-retriever/compare/v0.1.2...v0.1.3
[0.2.0]: https://github.com/cheginit/tiny-retriever/compare/v0.1.3...v0.2.0
[0.2.1]: https://github.com/cheginit/tiny-retriever/compare/v0.2.0...v0.2.1
[unreleased]: https://github.com/cheginit/tiny-retriever/compare/v0.2.1...HEAD
