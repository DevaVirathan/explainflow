# Contributing to ExplainFlow

Thank you for your interest in contributing to ExplainFlow! 🎉

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/explainflow.git
cd explainflow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[all]"
```

## Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=explainflow --cov-report=html
```

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run all checks:
```bash
black src tests
ruff check src tests
mypy src
```

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Add tests for any new functionality
3. Ensure all tests pass
4. Update documentation as needed
5. Submit a pull request

## Reporting Issues

Please use the GitHub issue tracker and include:
- Python version
- ExplainFlow version
- Minimal code to reproduce the issue
- Expected vs actual behavior

## Feature Requests

We welcome feature requests! Please check existing issues first to avoid duplicates.

## Code of Conduct

Be kind, respectful, and constructive. We're all here to learn and improve.
