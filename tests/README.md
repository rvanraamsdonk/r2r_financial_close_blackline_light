# R2R Financial Close - Test Architecture

This directory contains the comprehensive test suite for the R2R Financial Close system, designed with a layered testing strategy suitable for enterprise-grade financial software.

## Test Structure

```
tests/
├── unit/                    # Fast, isolated tests (<100ms each)
│   ├── engines/            # Individual engine logic tests
│   ├── ai/                 # AI module behavior tests (mocked)
│   ├── data/               # Data loading and validation tests
│   └── utils/              # Utility function tests
├── integration/            # Component interaction tests (<5s each)
│   ├── workflow/           # LangGraph node sequence tests
│   ├── data_flow/          # End-to-end data transformation tests
│   └── ai_integration/     # AI + deterministic combination tests
├── e2e/                    # Full system tests (<30s each)
│   ├── close_scenarios/    # Complete close workflow tests
│   ├── error_recovery/     # Exception handling tests
│   └── performance/        # Load and timing tests
└── fixtures/               # Shared test data and utilities
    ├── data/               # Test datasets (smaller than production)
    ├── mocks/              # AI and external service mocks
    └── helpers/            # Common test utilities
```

## Running Tests

### Prerequisites
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (pytest already in requirements.txt)
pip install -r requirements.txt
```

### Test Execution

```bash
# Run all tests
pytest

# Run by category
pytest -m unit          # Fast unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only

# Run by component
pytest tests/unit/engines/                    # Engine unit tests
pytest tests/integration/workflow/            # Workflow integration tests
pytest tests/e2e/close_scenarios/            # Full close scenarios

# Run with specific markers
pytest -m "unit and deterministic"           # Deterministic unit tests only
pytest -m "integration and ai"               # AI integration tests
pytest -m "not slow"                         # Exclude slow tests

# Verbose output
pytest -v

# Coverage reporting (if coverage installed)
pytest --cov=src/r2r --cov-report=html
```

## Test Categories and Markers

### Markers
- `unit`: Fast, isolated unit tests
- `integration`: Component interaction tests  
- `e2e`: End-to-end system tests
- `ai`: Tests involving AI components
- `deterministic`: Tests for deterministic calculations only
- `requires_data`: Tests that need test data files
- `slow`: Tests that take longer than 5 seconds

### Test Types

#### Unit Tests
- **Purpose**: Test individual functions and classes in isolation
- **Speed**: <100ms per test
- **Dependencies**: Mocked external dependencies
- **Focus**: Business logic, calculations, data transformations

#### Integration Tests  
- **Purpose**: Test component interactions and data flow
- **Speed**: <5s per test
- **Dependencies**: Real components, mocked external services
- **Focus**: LangGraph workflows, state transitions, audit trails

#### E2E Tests
- **Purpose**: Test complete system behavior
- **Speed**: <30s per test
- **Dependencies**: Full system with mocked AI (optional)
- **Focus**: Complete close scenarios, error recovery, performance

## Mock Framework

### AI Mocking
```python
from tests.fixtures.mocks import MockAIModule, create_ai_mock_suite

# Individual AI mock
ai_mock = MockAIModule()
ai_mock.configure_response("fx_narrative", MockAIResponse("FX analysis complete"))

# Complete AI mock suite
ai_mocks = create_ai_mock_suite()
```

### Data Mocking
```python
from tests.fixtures.mocks import MockStaticDataRepo, patch_data_loading

# Mock data repository
mock_repo = MockStaticDataRepo()

# Patch data loading functions
patch_data_loading(monkeypatch, mock_repo)
```

### State Building
```python
from tests.fixtures.helpers import StateBuilder, DataFrameBuilder

# Build test state
state = (StateBuilder(repo_root, temp_dir)
         .with_period("2025-08")
         .with_ai_mode("off")
         .with_tb_df(test_tb_df)
         .build())

# Build test DataFrames
tb_df = (DataFrameBuilder.trial_balance()
         .add_balance("2025-08", "ENT100", "1000", 100000.0)
         .build())
```

## Test Data Management

### Fixtures
- **Shared fixtures** in `conftest.py` for common test objects
- **Component-specific fixtures** in individual test files
- **Builder pattern** for complex test data construction

### Test Data Principles
- **Minimal realistic datasets** - not full production data
- **Scenario-specific fixtures** for different test cases  
- **Deterministic test data** with known expected outcomes
- **Isolated test environments** with proper cleanup

## Financial Assertions

```python
from tests.fixtures.helpers import assert_financial_balance, assert_fx_consistency

# Financial balance assertions
assert_financial_balance(debits=100000.0, credits=100000.0, tolerance=0.01)

# FX consistency assertions  
assert_fx_consistency(amount_local=100000.0, amount_usd=109200.0, fx_rate=1.092)

# Trial balance validation
assert_tb_balanced(tb_df, tolerance=0.01)
```

## Development Guidelines

### Writing New Tests

1. **Choose appropriate test level** (unit/integration/e2e)
2. **Use proper markers** to categorize tests
3. **Mock external dependencies** appropriately
4. **Follow naming conventions** (`test_<functionality>_<scenario>`)
5. **Include docstrings** explaining test purpose
6. **Use financial assertions** for monetary comparisons

### Test Isolation

- **No shared state** between tests
- **Clean up resources** in teardown
- **Use temporary directories** for file operations
- **Mock time-dependent operations** for consistency

### Performance Considerations

- **Keep unit tests fast** (<100ms)
- **Use appropriate test level** for what you're testing
- **Mock expensive operations** in lower-level tests
- **Profile slow tests** and optimize where possible

## CI/CD Integration

Tests are designed for automated execution in CI/CD pipelines:

```bash
# Fast feedback loop (unit tests only)
pytest -m unit --tb=short

# Full validation (all tests)  
pytest --tb=short --maxfail=5

# Performance regression detection
pytest -m "not slow" --durations=10
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `src/` is in Python path
2. **Mock not working**: Check patch target paths
3. **Slow tests**: Use appropriate markers and mocking
4. **Data dependencies**: Use fixtures instead of real files
5. **Flaky tests**: Check for shared state or timing issues

### Debug Mode
```bash
# Run with pdb on failure
pytest --pdb

# Verbose output with full tracebacks
pytest -vvv --tb=long

# Run specific failing test
pytest tests/unit/engines/test_bank_recon.py::TestBankReconciliation::test_duplicate_detection_basic -vvv
```

## Architecture Decisions

### Why This Structure?
- **Layered testing** provides appropriate feedback loops
- **Comprehensive mocking** enables fast, reliable tests
- **Financial-specific assertions** handle monetary precision
- **Builder patterns** create maintainable test data
- **Clear separation** between test types and concerns

### Future Enhancements
- **Property-based testing** for edge case discovery
- **Mutation testing** for test quality validation  
- **Performance benchmarking** with historical tracking
- **Contract testing** for API boundaries
- **Visual regression testing** for UI components (future)
