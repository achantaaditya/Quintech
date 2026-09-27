# Deployment

Build locally with `docker compose up --build`. Deploy Next.js and FastAPI separately or as containers, backed by managed PostgreSQL and object storage. Set long random JWT secrets, `CORS_ORIGINS`, a production `DATABASE_URL`, and external provider credentials. Run migrations before serving traffic and expose `/health` to the platform health check.
