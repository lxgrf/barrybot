# Tests

This directory contains unit tests for BarryBot to ensure code quality and prevent regressions.

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
python -m pytest tests/
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

This will generate an HTML coverage report in the `htmlcov/` directory.

### Run Specific Test Files

```bash
# Run only config tests
python -m pytest tests/test_config.py

# Run only utils tests
python -m pytest tests/test_utils.py
```

## Test Structure

- `test_config.py` - Tests for configuration validation (config.py)
- `test_utils.py` - Tests for utility functions (utils.py)
- `test_integration_examples.py` - Example integration tests (skipped by default)

## CI/CD Integration

Tests are automatically run on all pull requests via GitHub Actions. See `.github/workflows/tests.yml` for the CI configuration.

## Writing New Tests

When adding new functionality, please include corresponding tests:

1. Create test files with the `test_` prefix
2. Use descriptive test names that explain what is being tested
3. Follow the existing test structure with test classes
4. Use pytest fixtures for common test setup
5. Mock external dependencies (Discord API, Anthropic API, etc.)

## Test Coverage

We aim to maintain good test coverage for:
- Configuration validation
- Utility functions
- Core business logic
- Error handling

Note: Tests for Discord slash-command extensions are more complex and require significant mocking. The current test suite focuses on testable utility functions and configuration validation.
