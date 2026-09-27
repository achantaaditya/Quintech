# Database migrations

For production PostgreSQL deployments, initialise Alembic from `backend/` and generate the first revision:

```bash
alembic init alembic
alembic revision --autogenerate -m "initial CareerOS schema"
alembic upgrade head
```

Demo mode creates its SQLite schema at startup so the full local workflow has no database prerequisite.
