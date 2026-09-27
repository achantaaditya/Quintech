# Security

Passwords use Argon2 through `pwdlib`; access and refresh JWTs use separate secrets. Every personal-data query is filtered by the authenticated user. File uploads allow only PDF/DOCX and apply a size cap. Configure a strict production CORS allowlist, HTTPS, secure HTTP-only refresh cookies, rate limiting and a secret manager before deployment.
