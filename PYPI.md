# Notes for publish to PyPi

## Environment setup

### Create virtual environment

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Install necessary packages for building and releasing

```bash
pip install setuptools wheel build
```

### Install package for secure upload

```bash
pip install twine
```

### Install dependencies

```bash
# Add dependency into pyproject.toml

# Run pip install
pip install -e .
```

## Build and release new version

### Update version number

* Update underdoc/version.py for version number
* Update version number in pyproject.toml

### Build package

```bash
python -m build
```

### Upload to Pypi

```bash
twine upload dist/*
```
