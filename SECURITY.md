# Security Policy

## Reporting a vulnerability

If you find a security issue in this project, please **do not open a public
GitHub issue**. Instead, report it privately via
[GitHub Security Advisories](https://github.com/hcdierks/voicememo-transcriber/security/advisories/new)
("Report a vulnerability" under the Security tab of this repo).

Please include:
- A description of the issue and its potential impact.
- Steps to reproduce, or a proof-of-concept if available.
- Any suggested fix, if you have one.

You should expect an initial response within a few days. This is a
personal/hobby project maintained in spare time, so please be patient.

## Scope

This tool runs entirely locally: it transcribes and diarizes audio files on
your own machine and talks to Hugging Face only to download pretrained
models. The most relevant attack surface is the local viewer web server
(`vmt view`), which binds to `127.0.0.1` only but is reachable from any local
process or from a browser tab pointed at `localhost`.

## Supported versions

This project does not yet have tagged releases; security fixes land on
`main`. There is no LTS/backport policy at this stage.
