# Contributing to TinyRetriever

Thank you for your interest in contributing!

## Development Setup

1. Install [pixi](https://pixi.sh) and [gh](https://github.com/cli/cli#installation).

1. Fork and clone the repository:

    ```console
    git clone git@github.com:your_name_here/tiny-retriever.git
    cd tiny-retriever
    git remote add upstream git@github.com:cheginit/tiny-retriever.git
    ```

1. Set up the development environments:

    ```console
    pixi install -e dev
    pixi install -e typecheck
    ```

1. Install pre-commit hooks:

    ```console
    pixi r pcupdate  # optionally bump hooks to latest versions first
    pixi r lint      # installs hooks and runs them across the repo
    ```

## Commit Messages

This project uses
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). All commit
messages **must** follow this format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | When to use                            | Changelog section |
| ---------- | -------------------------------------- | ----------------- |
| `feat`     | A new feature                          | Added             |
| `fix`      | A bug fix                              | Fixed             |
| `perf`     | A performance improvement              | Changed           |
| `refactor` | Code restructuring, no behavior change | Changed           |
| `revert`   | Reverting a previous commit            | Fixed             |
| `docs`     | Documentation only                     | *(skipped)*       |
| `test`     | Adding or updating tests               | *(skipped)*       |
| `chore`    | Maintenance, dependencies, tooling     | *(skipped)*       |
| `ci`       | CI/CD changes                          | *(skipped)*       |
| `build`    | Build system or external dependencies  | *(skipped)*       |

### Breaking Changes

Append `!` after the type, or add `BREAKING CHANGE:` in the footer:

```text
feat!: drop support for Python 3.10
```

```text
feat: new API

BREAKING CHANGE: `old_function` has been removed.
```

### Examples

```text
feat: add retry with exponential backoff for transient errors
fix: handle missing Content-Length in download validation
chore: bump ruff to v0.15.8
docs: add example notebook for hydrology data
```

## Running Tests

```console
pixi r -e test310 test  # test against Python 3.10
pixi r -e test314 test  # test against Python 3.14
```

## Linting

```console
pixi r lint
```

## Type Checking

```console
pixi r typecheck
```

## Documentation

```console
pixi r -e docs docs-serve   # live preview at http://localhost:8000
pixi r -e docs docs-build   # build static site
```

## Managing the Changelog

The changelog is maintained by [git-cliff](https://git-cliff.org) and generated
automatically from conventional commit messages. You do not need to edit `CHANGELOG.md`
manually.

```console
pixi r -e dev changelog        # preview unreleased changes
pixi r -e dev changelog-update # write them to CHANGELOG.md
```

## Submitting Changes

1. Create a feature branch from `main`:

    ```console
    git checkout -b bugfix-or-feature/name-of-your-change
    ```

1. Make your changes with tests. If you are making breaking changes, update the
    documentation and `README.md` as well.

1. Fetch the latest upstream and resolve any merge conflicts:

    ```console
    git fetch upstream
    git merge upstream/main
    ```

1. Ensure all checks pass:

    ```console
    pixi r lint
    pixi r typecheck
    pixi r -e test314 test
    ```

1. Commit using conventional commits and push:

    ```console
    git add .
    git commit -m "feat: a detailed description of your changes"
    git push origin bugfix-or-feature/name-of-your-change
    ```

1. Submit a pull request through the GitHub website.

## Reporting Bugs

Before submitting a bug report, search existing
[issues](https://github.com/cheginit/tiny-retriever/issues) to avoid duplicates. When
filing a new issue:

- Provide a clear and descriptive title.
- Describe the expected behavior vs. the actual behavior.
- Include a minimal reproducible example.
- Include your Python version, OS, and relevant package versions.

> Security-related issues must be reported by email to <cheginit@gmail.com>, not through
> the public issue tracker.

## Suggesting Enhancements

Enhancement suggestions are tracked as
[GitHub issues](https://github.com/cheginit/tiny-retriever/issues). Please check for
existing suggestions before opening a new one, and explain why the enhancement would be
useful to the broader user base.
