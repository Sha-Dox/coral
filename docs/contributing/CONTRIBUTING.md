# Contributing to CORAL

Thank you for your interest in contributing to CORAL!

## 🚀 Quick Start

```bash
git clone <repository-url>
cd coral
cd coral && pip3 install -r requirements.txt && cd ..
./start_all.sh
```

## 📝 Code Style

- Follow PEP 8 for Python
- Use 4 spaces for indentation
- Add docstrings to functions
- Keep functions focused

## �� Adding a New Platform

### 1. Create Monitor Directory
```bash
mkdir twitter_monitor
cd twitter_monitor
```

### 2. Integrate with CORAL

```python
from coral.coral_notifier import CORALNotifier

# Auto-detects CORAL availability
notifier = CORALNotifier('twitter')

# Send events
notifier.send_event(
    username='johndoe',
    event_type='new_tweet',
    summary='Posted new tweet',
    data={'tweet_id': '123', 'content': 'Hello!'}
)
```

### 3. Add to config.yaml

```yaml
twitter:
  enabled: true
  standalone: false
  port: 8002
  webhook:
    enabled: true
    url: "http://localhost:3333/api/webhook/twitter"
  trigger_url: "http://localhost:8002/api/check-now"
```

### 4. Update Database

```bash
cd coral
python3 update_config.py
cd ..
```

### 5. Test

```bash
./start_all.sh  # Test integrated mode
./start_monitor.sh twitter  # Test standalone
```

See [AI_AGENT_INTEGRATION.md](../integration/AI_AGENT_INTEGRATION.md) for detailed AI-assisted integration guide.

## 🧪 Testing

- **Auto-detection**: `python3 demo_auto_detection.py`
- **Integrated mode**: `./start_all.sh`
- **Standalone mode**: `./start_monitor.sh <platform>`
- **Web UI**: http://localhost:3333

## 📚 Documentation

- Update README.md for major features
- Add examples to guides
- Keep inline comments clear

## 💾 Commit Guidelines

### Format
```
<type>: <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **style**: Formatting
- **refactor**: Code restructure
- **chore**: Maintenance

### Example
```
feat: Add Twitter monitor integration

- Added Twitter monitor with auto-detection
- Updated config.yaml
- Added trigger endpoint
- Updated documentation

Closes #42
```

## 🔍 Pull Request Process

1. Fork repository
2. Create feature branch: `git checkout -b feat/twitter-monitor`
3. Make changes
4. Test thoroughly (all modes)
5. Update documentation
6. Commit with clear messages
7. Push: `git push origin feat/twitter-monitor`
8. Open pull request
9. Address review feedback

## 📋 Pre-Commit Checklist

Before committing:

- [ ] Code runs without errors
- [ ] Tested in integrated mode
- [ ] Tested in standalone mode
- [ ] Updated documentation
- [ ] No debug statements
- [ ] No sensitive data
- [ ] Follows code style
- [ ] Git ignore updated if needed

## 🚀 Publishing New Release

### Pre-Release Checklist

**Code Quality:**
- [ ] All tests passing
- [ ] No syntax errors
- [ ] No debug/console statements
- [ ] Functions documented
- [ ] PEP 8 compliant

**Files:**
- [ ] Remove `__pycache__`, `.pyc`, `.DS_Store`
- [ ] No API keys/secrets in code
- [ ] config.yaml has no credentials
- [ ] .gitignore comprehensive
- [ ] No log files

**Documentation:**
- [ ] README.md up to date
- [ ] CHANGELOG.md updated
- [ ] All guides reviewed
- [ ] Examples work

**Testing:**
- [ ] Integrated mode works
- [ ] Standalone mode works
- [ ] Auto-detection works
- [ ] Manual triggers work
- [ ] Demo script runs

### Release Process

1. **Update version**
   ```bash
   # Update version in relevant files
   git add .
   git commit -m "chore: Bump version to v1.1.0"
   ```

2. **Tag release**
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

3. **Create GitHub release**
   ```bash
   gh release create v1.1.0 \
     --title "CORAL v1.1.0" \
     --notes "See CHANGELOG.md"
   ```

4. **Announce**
   - Update README.md with release notes
   - Post to relevant communities
   - Update documentation site (if any)

## ❓ Questions?

- Check [README.md](../../README.md)
- Review [STANDALONE_USAGE.md](../guides/STANDALONE_USAGE.md)
- See [AI_AGENT_INTEGRATION.md](../integration/AI_AGENT_INTEGRATION.md)
- Open an issue on GitHub
- Check existing issues/discussions

## 📄 License

By contributing, you agree your contributions will be licensed under the MIT License.

---

**Need help integrating?** See [AI_AGENT_INTEGRATION.md](../integration/AI_AGENT_INTEGRATION.md) for detailed prompts!
