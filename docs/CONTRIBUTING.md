# Contributing Guide

**File**: docs/CONTRIBUTING.md  
**Created**: 2026-01-28T11:09:00.123  
**Author**: David LECONTE, IBM WorldWide | Data & AI

---

## How to Contribute

We welcome contributions! This guide will help you get started.

## Ways to Contribute

- Report bugs
- Suggest features
- Improve documentation
- Submit code changes
- Add tests

---

## Before You Start

1. Read the CODE_OF_CONDUCT.md
2. Check existing issues and PRs
3. Discuss major changes in an issue first
4. Fork the repository

---

## Development Setup

### Clone Your Fork

git clone https://github.com/YOUR_USERNAME/hcd-janusgraph.git
cd hcd-janusgraph

### Add Upstream

git remote add upstream https://github.com/your-org/hcd-janusgraph.git

### Install Dependencies

pip install -r requirements.txt
pip install -r requirements-dev.txt

### Install Pre-commit Hooks

pip install pre-commit
pre-commit install

---

## Making Changes

### Create a Branch

git checkout -b feature/my-feature

Branch naming:
- feature/: New features
- fix/: Bug fixes
- docs/: Documentation
- refactor/: Code refactoring
- test/: Test additions

### Make Your Changes

Follow coding standards:
- Python: PEP 8 (enforced by black/flake8)
- Line length: 100 characters
- Type hints where possible

### Run Tests

make test

Or manually:

pytest tests/ -v

### Run Linters

make lint

Or manually:

black src/ tests/
flake8 src/ tests/
isort src/ tests/

### Commit Changes

Write clear commit messages:

feat: add new feature
fix: resolve bug in X
docs: update README
test: add tests for Y
refactor: improve code structure

Use conventional commits format.

---

## Submitting Changes

### Push to Your Fork

git push origin feature/my-feature

### Create Pull Request

Use GitHub UI or:

gh pr create --title "Add feature X" --body "Description"

### PR Checklist

- [ ] Tests added/updated
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Commit messages clear
- [ ] No breaking changes (or documented)
- [ ] Self-review completed

---

## Code Review Process

### What to Expect

1. CI checks run automatically
2. Maintainers review code
3. Feedback provided
4. Changes requested if needed
5. Approval and merge

### Timeline

- Initial review: 1-3 business days
- Follow-up: 1-2 business days

### After Merge

- Branch deleted automatically
- Changes appear in next release
- Credit in changelog

---

## Coding Standards

### Python Style

- Use black for formatting
- Follow PEP 8
- Type hints for functions
- Docstrings for public APIs

Example:

def process_data(input: str) -> dict:
    """Process input data.
    
    Args:
        input: Input string to process
        
    Returns:
        dict: Processed data
    """
    return {"result": input}

### Shell Scripts

- Use shellcheck
- Include error handling
- Add comments for complex logic

### Documentation

- Markdown for docs
- Code examples where helpful
- Keep QUICKSTART.md updated

---

## Testing Guidelines

### Test Types

- Unit tests: tests/unit/
- Integration tests: tests/integration/
- Performance tests: tests/performance/

### Writing Tests

Use pytest:

def test_feature():
    result = my_function()
    assert result == expected

### Test Coverage

Aim for 80%+ coverage. Run:

pytest --cov=src tests/

---

## Documentation

### Update README

When adding features, update:
- Feature list
- Usage examples
- Dependencies

### Update QUICKSTART

Add common commands for new features.

### Create Docs

For major features, add docs/*.md file.

---

## Issue Guidelines

### Reporting Bugs

Use bug report template. Include:
- Environment details
- Steps to reproduce
- Expected vs actual behavior
- Logs/screenshots

### Requesting Features

Use feature request template. Include:
- Use case
- Proposed solution
- Alternatives considered

---

## Review Checklist

### For Reviewers

- [ ] Code quality acceptable
- [ ] Tests comprehensive
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance acceptable
- [ ] Breaking changes documented

---

## Release Process

### Versioning

We use Semantic Versioning:
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Creating Releases

Maintainers only:

1. Update CHANGELOG.md
2. Tag version: git tag v1.2.3
3. Push tag: git push origin v1.2.3
4. GitHub Action creates release

---

## Getting Help

### Questions

- GitHub Discussions
- Issues (with question label)
- Email: support@example.com

### Community

- Be respectful
- Follow code of conduct
- Help others when you can

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!**

---

**Signature**: David LECONTE, IBM WorldWide | Data & AI
