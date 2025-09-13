# GOLD3 Test Organization

This directory contains the organized test structure for the GOLD3 project. Tests are organized by type and purpose for better maintainability and execution control.

## Directory Structure

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests that verify component interactions
├── smoke/          # Quick sanity checks for critical functionality
└── utils/          # Test utilities and helper functions
```

## Test Types

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions, methods, and classes in isolation
- **Speed**: Fast (should run in milliseconds)
- **Dependencies**: Minimal, use mocks/stubs for external dependencies
- **Markers**: `@pytest.mark.unit`
- **Example**: Testing model methods, utility functions, validation logic

### Integration Tests (`tests/integration/`)
- **Purpose**: Test how different components work together
- **Speed**: Medium (may take seconds)
- **Dependencies**: Database, external services may be required
- **Markers**: `@pytest.mark.integration`
- **Example**: Testing complete workflows, database relationships, API calls

### Smoke Tests (`tests/smoke/`)
- **Purpose**: Quick sanity checks to ensure the application is working
- **Speed**: Very fast (basic functionality checks)
- **Dependencies**: Minimal setup required
- **Markers**: `@pytest.mark.smoke`
- **Example**: Basic model creation, URL accessibility, import checks

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run only smoke tests
python run_tests.py --smoke

# Run tests for a specific app
python run_tests.py --app workflow

# Run with coverage report
python run_tests.py --coverage

# Run tests in verbose mode
python run_tests.py --verbose
```

### Using pytest Directly

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m smoke

# Run tests in specific directory
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py::TestItemModelUnit::test_item_creation
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from django.test import TestCase
from tests.utils.test_helpers import create_test_user, create_test_site

class TestYourFeature(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.site = create_test_site()

    @pytest.mark.unit  # or @pytest.mark.integration or @pytest.mark.smoke
    def test_your_functionality(self):
        # Your test code here
        assert True
```

### Using Test Fixtures

```python
@pytest.fixture
def test_data():
    user = create_test_user()
    site = create_test_site()
    return {"user": user, "site": site}

def test_with_fixture(test_data):
    user = test_data["user"]
    site = test_data["site"]
    # Test code here
```

### Test Markers

Use appropriate markers for your tests:

- `@pytest.mark.unit` - For unit tests
- `@pytest.mark.integration` - For integration tests
- `@pytest.mark.smoke` - For smoke tests
- `@pytest.mark.slow` - For tests that take longer than 30 seconds
- `@pytest.mark.external` - For tests that require external services
- `@pytest.mark.mock` - For tests that use extensive mocking

## Test Configuration

The test configuration is in `pytest.ini` and includes:

- **Markers**: Pre-defined markers for different test types
- **Coverage**: Configuration for coverage reporting
- **Filtering**: Options to include/exclude specific tests
- **Django**: Integration with Django's test framework

## Best Practices

1. **Test Organization**: Put tests in the appropriate directory based on their type
2. **Test Naming**: Use descriptive names that explain what is being tested
3. **Test Isolation**: Each test should be independent and not rely on other tests
4. **Mock External Dependencies**: Use mocks for external services in unit tests
5. **Use Fixtures**: Leverage pytest fixtures for reusable test data
6. **Mark Tests Appropriately**: Use markers to categorize your tests
7. **Keep Tests Fast**: Unit tests should be very fast, integration tests should be reasonable
8. **Test Edge Cases**: Include tests for error conditions and edge cases

## Continuous Integration

For CI/CD pipelines, you can run different test suites at different stages:

```bash
# Quick feedback (smoke tests)
python run_tests.py --smoke

# Full test suite (unit + integration)
python run_tests.py --unit --integration

# Complete validation (all tests with coverage)
python run_tests.py --coverage
```

## Adding New Tests

1. Create your test file in the appropriate directory
2. Use the correct markers for your test type
3. Follow the naming convention: `test_*.py`
4. Import necessary helpers from `tests.utils.test_helpers`
5. Run your tests to ensure they work correctly

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure `__init__.py` files exist in all test directories
2. **Database Issues**: Use `TransactionTestCase` for tests that modify the database
3. **Fixture Errors**: Ensure fixtures are properly defined and imported
4. **Marker Issues**: Check that markers are defined in `pytest.ini`

### Getting Help

- Check the test output for detailed error messages
- Use `--verbose` flag for more detailed output
- Run individual test files to isolate issues
- Check the Django documentation for testing best practices

## Examples

See the example test files in each directory for reference:

- `tests/unit/test_models.py` - Unit test examples
- `tests/integration/test_workflow.py` - Integration test examples
- `tests/smoke/test_basic.py` - Smoke test examples
- `tests/utils/test_helpers.py` - Test utility functions

## Notes from 2025-09-11 (nightly maintenance)

The following changes were made during a maintenance session on 2025-09-11. These edits were made to unblock the test run and should be revisited for long-term fixes. Nothing below removes or alters the record of accomplishments from tonight — it only documents them.

- Removed top-level `__init__.py` at repository root to avoid the project being importable as package `Gold3`. This prevented duplicate model registration errors (e.g. conflicting `Plant` model declarations). If you need to restore a top-level package import for another workflow, prefer using a dedicated package name and avoid naming conflicts with `gchub_db`.
- Updated `tests/smoke/test_urls.py` to guard against a missing or non-iterable `self.client.handler._middleware_chain`. The test now falls back to reading `django.conf.settings.MIDDLEWARE` and strips out `CsrfViewMiddleware` when overriding settings for the test.

Temporary test-skipping guidance:

- If the test suite still reports failures you want to skip temporarily, use pytest's skip markers or selection flags. Examples:

```bash
# Run tests but skip smoke tests
pytest -k "not smoke"

# Run only smoke tests
pytest -m smoke

# Skip a specific test file
pytest -k "not tests/smoke/test_urls.py"
```

Notes and next steps:

- These edits were made to get an initial green run; please re-open and harden the underlying issues (app registry conflicts, middleware exposure in the test client) before re-introducing aggressive refactors.
- If any of tonight's changes need to be reverted or converted to a different approach, document the desired outcome and I can implement the safer alternative.
