# Contributing

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[core,dev]"     # no ML deps needed to run tests
```

## Before opening a PR

```
ruff check src tests
pytest
```

CI (`.github/workflows/ci.yml`) runs lint, tests, and the security/license
checks below on every push and PR — matching them locally first saves a
round trip.

## Security and license scanning

These aren't installed by default (they're not needed to run or test `vmt`
day to day); install them ad hoc when touching dependencies or anything
security-sensitive:

```
pip install bandit pip-audit pip-licenses detect-secrets
bandit -r src
pip-audit
pip-licenses --format=plain-vertical
```

[`gitleaks`](https://github.com/gitleaks/gitleaks) (via `brew install
gitleaks`) scans full git history for accidentally committed secrets:

```
gitleaks detect --source . --log-opts="--all"
```

## Reporting a vulnerability instead of contributing a fix

See [`SECURITY.md`](SECURITY.md) — please report privately rather than
opening a public PR/issue for anything security-sensitive.

## Scope of automated tests

See [`docs/test-plan.md`](docs/test-plan.md) for what's covered by CI vs.
what requires manual verification against real Voice Memos audio (ASR/
diarization itself needs gated models and real audio, so it isn't mocked in
CI — see that doc for the reasoning).
