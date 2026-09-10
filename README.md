# Domjudge Tool CLI

- Python >= 3.13
- [mise](https://mise.jdx.dev/)
- [uv](https://docs.astral.sh/uv/)

## Development

Prerequisites: install [mise](https://mise.jdx.dev/).

```shell
# Install tools (Python 3.13.15, uv 0.12.12)
$ mise install

# Install dependencies into virtual environment
$ mise run install

# Run linters, type checks, and tests
$ mise run check

# Format codebase
$ mise run format

# Build wheel and sdist
$ mise run build
```

## CLI Usage

```shell
$ domjudge-tool-cli general config https://domjudge.example.dev

$ domjudge-tool-cli general check
Success connect API v4.

$ domjudge-tool-cli users user-list
```

## Tech Stack

- [typer](https://typer.tiangolo.com/): CLI framework
- [httpx](https://www.python-httpx.org): asyncio HTTP client
- [pydantic](https://docs.pydantic.dev/): Data validation
- [tablib](https://tablib.readthedocs.io): Import and export data
