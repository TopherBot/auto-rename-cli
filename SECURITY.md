# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please **do not** open a public issue. Instead, follow these steps:

1. **Email** the details to `security@topherbot.dev` (encrypted GPG: `0xDEADBEEF` – replace with real key).
2. Include a clear description, affected versions, and any proof‑of‑concept.
3. We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation promptly.

## Security Recommendations
- Keep your Telegram bot token and GitHub token in repository **secrets**, never in source code.
- Use branch protection rules (see CI best‑practices) to enforce status checks before merges.
- Regularly update dependencies; the CI pipeline includes a `pip‑compile` lock step.

---

*This project follows the “security by design” principle: all external calls (Telegram, GitHub) are wrapped in try/except blocks, and failures never expose secrets or cause crashes.*
