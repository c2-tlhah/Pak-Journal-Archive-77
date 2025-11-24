# Contributing to Pak News Journal Archive

Thank you for your interest in contributing to the Pak News Journal Archive project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Pull Request Process](#pull-request-process)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/Pak-Journal-Archive-77.git
   cd Pak-Journal-Archive-77
   ```
3. Set up the development environment (see Development Setup below)
4. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- FFmpeg
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure your database connection and JWT secret

5. Initialize the database:
   ```bash
   python database/setup_db.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Running the Full Application

1. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

2. In a new terminal, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at `http://localhost:5173`

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix existing issues
- **Features**: Add new functionality
- **Documentation**: Improve documentation
- **Tests**: Add or improve test coverage
- **UI/UX**: Improve user interface and experience

### Development Workflow

1. Choose an issue from the [GitHub Issues](https://github.com/c2-tlhah/Pak-Journal-Archive-77/issues) or create your own
2. Create a feature branch from `main`
3. Make your changes
4. Write or update tests
5. Ensure all tests pass
6. Update documentation if needed
7. Commit your changes
8. Push to your fork
9. Create a Pull Request

## Reporting Bugs

When reporting bugs, please include:

- **Clear title**: Describe the issue concisely
- **Steps to reproduce**: Detailed steps to reproduce the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, browser, Python/Node versions
- **Screenshots**: If applicable
- **Error logs**: Any relevant error messages

Use the [Bug Report Template](https://github.com/c2-tlhah/Pak-Journal-Archive-77/issues/new?template=bug_report.md) when creating issues.

## Suggesting Features

For feature requests:

- **Check existing issues**: Make sure the feature hasn't been requested
- **Clear description**: Explain the feature and why it's needed
- **Use cases**: Provide examples of how the feature would be used
- **Mockups**: If UI-related, include mockups or wireframes

Use the [Feature Request Template](https://github.com/c2-tlhah/Pak-Journal-Archive-77/issues/new?template=feature_request.md).

## Pull Request Process

1. **Update the README.md** with details of changes if needed
2. **Update documentation** for any new features
3. **Ensure tests pass** and add new tests for new features
4. **Follow code style guidelines**
5. **Write clear commit messages**
6. **Reference issues** in your PR description

### PR Template

```
## Description
Brief description of the changes made

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
```

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where possible
- Maximum line length: 88 characters (Black formatter default)
- Use descriptive variable names
- Add docstrings to functions and classes

### JavaScript/React (Frontend)

- Use ESLint and Prettier for code formatting
- Follow React best practices
- Use functional components with hooks
- Add PropTypes for component props
- Use meaningful component and variable names

### General

- Write clear, concise commit messages
- Use English for all comments and documentation
- Keep functions small and focused
- Add comments for complex logic

## Testing

### Backend Testing

```bash
cd backend
python -m pytest tests/
```

### Frontend Testing

```bash
cd frontend
npm test
```

### Test Coverage

Aim for high test coverage, especially for:
- API endpoints
- Business logic
- User authentication
- File upload/processing

## Documentation

- Keep README.md up to date
- Document API endpoints in code
- Add inline comments for complex logic
- Update this CONTRIBUTING.md as needed

## Getting Help

- Check existing [Issues](https://github.com/c2-tlhah/Pak-Journal-Archive-77/issues) and [Discussions](https://github.com/c2-tlhah/Pak-Journal-Archive-77/discussions)
- Join our community discussions
- Contact maintainers for guidance

## Recognition

Contributors will be recognized in the project README and GitHub's contributor insights. Thank you for helping preserve Pakistan's broadcast history!