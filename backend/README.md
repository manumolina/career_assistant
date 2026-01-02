# Career Assistant Backend

Backend API developed with FastAPI and Poetry.

## Requirements

- Python 3.11+
- Poetry

## Installation

1. Install Poetry (if you don't have it):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Activate virtual environment:
```bash
poetry shell
```

## Execution

### Development

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Production

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8080
```

## Dependency Management

### Add a dependency

```bash
poetry add package-name
```

### Add a development dependency

```bash
poetry add --group dev package-name
```

### Update dependencies

```bash
poetry update
```

### Export to requirements.txt (if needed)

```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Useful Scripts

### List available Gemini models

```bash
poetry run python list_models.py
```

## Linting

The project uses Ruff for linting and formatting:

```bash
# Check code
poetry run ruff check .

# Format code
poetry run ruff format .
```
