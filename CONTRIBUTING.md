# Contributing to Claude Builder Hacks

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Claude-Builder-Hacks.git
   cd Claude-Builder-Hacks
   ```
3. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

### Local Development
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the helper script
./docker-start.sh
```

## 📝 Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

Example:
```python
def calculate_task_deadline(estimated_hours: int, start_date: datetime) -> str:
    """
    Calculate task deadline based on estimated hours.
    
    Args:
        estimated_hours: Number of hours estimated for the task
        start_date: Start date for the task
        
    Returns:
        Formatted deadline string (e.g., "Dec 15")
    """
    estimated_days = max(1, estimated_hours // 8)
    deadline_date = start_date + timedelta(days=estimated_days)
    return deadline_date.strftime("%b %d")
```

## 🧪 Testing

Before submitting a PR, ensure:
- Your code runs without errors
- All existing tests pass
- New features have appropriate tests
- Manual testing has been performed

```bash
# Run tests
python test_intelligent_assignment.py

# Test specific functionality
python -m pytest tests/test_your_feature.py
```

## 📤 Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what was changed and why
   - Screenshots for UI changes
   - Reference to any related issues

## 🐛 Reporting Bugs

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Error messages/logs

## 💡 Feature Requests

For feature requests:
- Explain the use case
- Describe the desired behavior
- Suggest implementation approach (optional)
- Note if you're willing to implement it

## 🏗️ Project Structure

```
app.py                  # Main Flask application
mcp_server/            # Model Context Protocol server
├── server.py          # Core MCP server logic
└── flask_integration.py  # Flask Blueprint
static/                # Frontend JavaScript
templates/             # HTML templates
```

## 🔍 Code Review Process

All submissions require review. We aim to:
- Review PRs within 48 hours
- Provide constructive feedback
- Merge approved changes promptly

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

Open an issue with the `question` label or reach out to the maintainers.

---

Thank you for contributing! 🎉
