# Changelog

## Unreleased

- Repo-maturity pass ahead of making the repository public: added `LICENSE`
  (MIT), `NOTICE.md` (third-party attribution), `SECURITY.md`,
  `CONTRIBUTING.md`, issue/PR templates, `CODEOWNERS`, Dependabot config, and
  a `security` CI job (bandit, pip-audit, pip-licenses, gitleaks).
- Fixed a path-traversal / reflected-script-injection issue in the local
  viewer web server (`vmt view`): `recording_id` is now validated against
  its expected sha256-hex shape at every entry point, and escaped when
  rendered into the HTML viewer.
- Added an `Origin` check to the viewer server's `POST /api/rename` endpoint.
- Fixed `SpeakerRegistry.merge()` leaving an orphaned `.npy` embedding file
  on disk for the absorbed speaker.

## 0.1.0

- Initial scaffold: SDLC docs, package skeleton, core pipeline, tests, CI.
- `vmt scan`/`process`/`review`/`view`, speaker registry (`list`/`rename`/`merge`).
