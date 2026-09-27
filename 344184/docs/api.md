# API

OpenAPI is available at `/docs` while the backend runs. Major endpoints are `/api/auth/*`, `/api/users/me`, `/api/resumes/*`, `/api/jobs`, `/api/skills/gaps`, `/api/roadmap/*`, `/api/interviews/*`, `/api/assistant/chat`, and `/api/dashboard`.

Protected routes require `Authorization: Bearer <access token>`. Errors use `{ success: false, error: { code, message } }` and never return internal stack traces.
