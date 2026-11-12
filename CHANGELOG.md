# Changelog

## 1.0.0-rc.1 — release candidate

Verification record: `documentation/RELEASE_VERIFICATION.md`.

### Security and production safety
- Production configuration is validated before the database is touched; development values are refused
  (built-in or weak secret, SQLite or development database password, wildcard or localhost origins, non-HTTPS
  public URL, `EMAIL_PROVIDER=log`, built-in sender address, sample-data seeding, the insecure-secret switch).
- The sample-data seed refuses to run in production.
- API documentation pages and the OpenAPI schema are not served in production.
- Dependencies: React Router 6 → 7, Vite 5 → 7, `@vitejs/plugin-react` 4 → 5, `minimatch` override for the
  linter. `npm audit` and `pip-audit` report no known vulnerabilities.
- Secret scanning: reviewed detect-secrets baseline, a Git-history scanner (`scripts/scan_git_history.py`),
  and gitleaks, all run in CI together with `pip-audit` and `npm audit`.

### Operations
- Backup script: dumps without ownership statements, owner-only permissions, archive verification, SHA-256
  file, clean failure. Restore script: checksum check, refuses a non-empty target, single transaction.
- The seed script now runs inside the container layout (the development Docker stack could not load sample
  data before).
- `scripts/make_release.sh` builds a clean release directory and archive with a manifest.
- Deployment guide: refused-settings table, backup and restore procedures, troubleshooting, release build.

### Earlier in this cycle
- REVA University client workspace (240 students, `@reva.in` accounts), dashboard fixes, paged placement lists,
  half credit for unverified skills.
- Permission gaps closed (reports, student records, placement officer scope), sign-in lockout, single-use
  refresh tokens, email outbox with retry, Redis-backed rate limiting, TLS-terminating Nginx configuration,
  pinned Python dependencies, CI.
