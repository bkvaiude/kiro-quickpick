# Contributing to AI Shopping Assistant

Thank you for your interest in contributing to the AI Shopping Assistant! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Follow the setup instructions in the [README](README.md)
4. Create a new branch for your feature or bug fix

## Development Workflow

### Frontend Development
```bash
cd ai-shopping-assistant/frontend
npm install
npm run dev
```

### Backend Development
```bash
cd ai-shopping-assistant/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Code Style

- **Frontend**: Follow TypeScript and React best practices
- **Backend**: Follow PEP 8 Python style guidelines
- Use meaningful commit messages
- Add tests for new features

## Testing

Before submitting a pull request:

```bash
# Frontend tests
cd ai-shopping-assistant/frontend
npm test

# Backend tests
cd ai-shopping-assistant/backend
pytest
```

## Submitting Changes

1. Ensure all tests pass
2. Update documentation if needed
3. Submit a pull request with a clear description
4. Reference any related issues

## License

By contributing, you agree that your contributions will be licensed under the Mozilla Public License 2.0.

## Questions?

Feel free to open an issue for any questions or suggestions!