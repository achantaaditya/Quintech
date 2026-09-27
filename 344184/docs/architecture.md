# Architecture

```mermaid
flowchart LR
 Browser[Next.js client] --> API[FastAPI API]
 API --> DB[(PostgreSQL / SQLite demo)]
 API --> Resume[Resume processor]
 API --> Career[Matching and roadmap services]
 API --> Agent[Constrained career orchestrator]
 Agent --> RAG[RAG provider interface]
```

The Next.js client makes authenticated REST calls. FastAPI owns authorization, business logic and persistence. Demo mode uses deterministic local services; a provider boundary is reserved for LLM, embeddings, storage and job providers.
