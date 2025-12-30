# Engineering Guidelines

This document outlines the engineering standards and best practices for the `chinese-calligraphy` project. We aim to maintain a high-quality, Pythonic codebase through rigorous linting, static analysis, and automated testing.

## Tool Stack

| Category | Tool | Why? |
|----------|------|------|
| **Environment** | [uv](https://github.com/astral-sh/uv) | Extremely fast Python package installer and virtual environment manager. |
| **Linting** | [Ruff](https://docs.astral.sh/ruff/) | Blazing fast linter that replaces flake8, isort, and others. |
| **Formatting** | [Ruff](https://docs.astral.sh/ruff/formatter/) | Drop-in replacement for Black, integrated into the same tool. |
| **Type Checking** | [MyPy](https://mypy.readthedocs.io/) | Standard static type checker for Python. We enforce strict typing. |
| **Testing** | [Pytest](https://docs.pytest.org/) | Powerful and flexible testing framework. |
| **CI/CD** | GitHub Actions | Automated checks on every push and pull request. |

## Development Workflow

### 1. Environment Setup

We use `uv` for managing the virtual environment.

```bash
# Create virtual environment
uv venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies (including dev tools)
uv pip install -e '.[dev,fonttools]'
```

### 2. Linting & Formatting

We use **Ruff** for both linting and formatting. configuration is in `pyproject.toml`.

**Commands:**
```bash
# Check for linting errors
ruff check .

# Fix auto-fixable linting errors
ruff check --fix .

# Check formatting
ruff format --check .

# Format code
ruff format .
```

**Key Rules:**
- **Imports:** Auto-sorted (like isort).
- **Style:** Adheres to PEP 8 standards.
- **Complexity:** Checks for overly complex functions.
- **Modern Python:** Encourages usage of modern Python features (e.g., `list` instead of `List`).

### 3. Type Checking

We use **MyPy** to enforce type safety. This project is fully typed.

**Command:**
```bash
mypy .
```

**Best Practices:**
- **Strict Annotations:** All functions should have type hints for arguments and return values.
- **No `Any`:** Avoid using `Any` wherever possible.
- **Runtime Assertions:** Use `assert x is not None` to help MyPy narrow down optional types when you are certain a value exists.

### 4. Testing

We use **Pytest** for our test suite.

**Command:**
```bash
pytest
```

**Guidelines:**
- **Unit Tests:** Place unit tests in the `tests/` directory.
- **Integration:** Ensure existing examples (in `examples/`) continue to run correctly.

## Continuous Integration (CI)

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every Pull Request to `main`. It executes:

1. **Linting:** Fails if `ruff check` finds errors.
2. **Formatting:** Fails if `ruff format --check` finds unformatted code.
3. **Type Checking:** Fails if `mypy` finds type errors.
4. **Testing:** Fails if `pytest` reports failures.

**Note:** You must resolve all CI failures before merging.
