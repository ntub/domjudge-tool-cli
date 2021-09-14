# Domjudge Tool CLI

- Python 3.8.7
- [poetry](https://python-poetry.org/docs/cli/)


## Install

```shell
$ pip install --user poetry

$ git clone 
$ cd 

$ poetry install
$ poetry shell
# Activating the virtual environment

$ poetry add <package>
# Add dependencies

$  poetry add --dev <package>
# Add package as development dependency
```


## Use

```shell
$ domjudge-tool-cli general config https://domjudge.example.dev

$ domjudge-tool-cli general check                                            
Success connect API v4.

$ domjudge-tool-cli users user-list
```

## Python packages

- [typer](https://typer.tiangolo.com/): CLI framework
- [httpx](https://www.python-httpx.org): asyncio http client
- [pydantic](https://pydantic-docs.helpmanual.io/): Data validation
- [tablib](https://tablib.readthedocs.io): Import and export data


