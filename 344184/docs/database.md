# Database

The SQLAlchemy schema includes normalized users, profiles, skills, user skills, resumes and analyses, demo jobs, roadmaps/items, and interview sessions/questions/answers. Foreign keys cascade from a user to personal career data. `users.email` and `skills.name` are unique; user-skill pairs are unique.

SQLite is deliberately the zero-config local default. Set `DATABASE_URL` to PostgreSQL for deployed environments and use Alembic migrations from `backend/alembic`.
