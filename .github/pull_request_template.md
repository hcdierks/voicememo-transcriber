## What does this change

## Why

## Checklist

- [ ] `ruff check src tests` passes
- [ ] `pytest` passes
- [ ] If touching dependencies: `pip-audit` and `pip-licenses` were checked (see `CONTRIBUTING.md`)
- [ ] If touching the viewer web server or anything filesystem-path-related: considered whether user-controllable input reaches a path or is rendered into HTML/JS unescaped
