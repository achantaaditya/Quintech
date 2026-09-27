# CareerOS — Your AI Career Engineer

CareerOS is a full-stack career intelligence workspace for students and early-career professionals. It turns a resume, saved skills and a target role into transparent resume feedback, skill-gap analysis, a learning roadmap, job compatibility views, interview practice and grounded career guidance.

> Demo mode is intentionally useful without paid AI services. Its jobs are labelled demo data and its readiness, resume, interview and match scores are advisory signals—not hiring predictions.

## What is implemented

- Next.js App Router frontend with responsive landing page and protected-workspace style dashboard
- FastAPI REST API, automatic OpenAPI docs, Argon2 password hashing, JWT access/refresh tokens and user-scoped authorization
- SQLAlchemy relational persistence for profiles, skills, resumes, analyses, jobs, roadmaps and interviews
- PDF/DOCX text extraction and hybrid-style deterministic resume analysis
- Deterministic skill extraction, transparent job compatibility, skill gaps, roadmaps and career assistant for demo mode
- Resume upload, roadmap completion, interview answer evaluation, data deletion and useful analytics empty state
- Docker, Compose, CI workflow, environment template, tests and focused architecture documentation

## Architecture

```text
Next.js frontend → FastAPI API → PostgreSQL (SQLite for local demo)
                              ├→ resume processing
                              ├→ matching / roadmap services
                              └→ constrained agent + future RAG providers
```

See [architecture documentation](docs/architecture.md), [database design](docs/database.md), [AI system](docs/ai-system.md), [security](docs/security.md), and [deployment](docs/deployment.md).

## Repository layout

```text
careerOS/
├── frontend/       Next.js TypeScript client
├── backend/        FastAPI service and SQLAlchemy models
├── ml/             Evaluation utilities
├── docs/           Architecture and operations docs
├── .github/        CI workflow
└── docker-compose.yml
```

## Run locally

Prerequisites: Python 3.12+ and Node 22+ (or Docker).

```bash
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt pytest httpx
cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`; choose **Build My Career Profile** to create a fresh demo account. API docs are at `http://localhost:8000/docs`.

## Docker

```bash
docker compose up --build
```

Compose provisions Postgres, frontend and backend health checks. In production, replace the example JWT secrets and database credentials.

## Environment

Copy `.env.example`. Required production values are `DATABASE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `CORS_ORIGINS`, and `NEXT_PUBLIC_API_URL`. Keep `DEMO_MODE=true` to use seeded jobs and deterministic responses. LLM, embeddings and storage environment variables are provider boundaries; no API key is needed in demo mode.

## Testing

```bash
cd backend && ../.venv/bin/python -m pytest app/tests -q
cd frontend && pnpm build
```

## Production notes

Use PostgreSQL with Alembic migrations, object storage for upload files, HTTPS, a strict CORS allowlist, secret management, rate limiting, secure refresh-cookie handling and authenticated email-verification/reset flows. The current project supplies the core architecture and demo workflow; email delivery, external job APIs, a populated pgvector knowledge base, asynchronous workers and full historical analytics remain planned integrations.

## Team boundaries

- AI/ML: extraction, matching evaluation and embeddings
- GenAI: RAG, prompts, agent provider integrations
- Backend: data model, FastAPI, auth and authorization
- Frontend: Next.js dashboard and accessible workflows
- DevOps/integration: Docker, CI, monitoring, deployment

## License

MIT. See [LICENSE](LICENSE).
