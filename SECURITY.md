# Security Policy

## Supported versions

This project is in **alpha (0.x)**. Only the latest `0.x` release receives fixes.

| Version      | Supported |
| ------------ | --------- |
| latest `0.x` | ✅        |
| older        | ❌        |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Instead, report privately via
[GitHub Security Advisories](https://github.com/Lee-Dongwook/E2E-Self-Heal/security/advisories/new)
or email the maintainer at `dlehddnr0713@gmail.com`. We aim to acknowledge within a few days.

## API keys & secrets

The engine calls an LLM provider (NVIDIA NIM by default), so it needs an API key.

- **Bring your own key.** Set `E2E_HEALER_NVIDIA_API_KEY` via a local `.env` (gitignored) or
  a CI secret. The key is never committed, logged, or embedded in the package.
- **In CI**, pass the key through a repository/organization **secret**
  (`secrets.NVIDIA_API_KEY`), never inline in a workflow file.
- **`.env` is gitignored** and must stay that way; only `.env.example` (placeholders) is tracked.
- If a key is ever exposed, **rotate it** at [build.nvidia.com](https://build.nvidia.com/) and
  replace it locally — do not paste live keys into issues, PRs, or chat.

## Scope guardrail

By design the engine only edits **failing selectors and wait conditions** — never assertions
or test logic — and every patch is human-reviewable before it lands.
