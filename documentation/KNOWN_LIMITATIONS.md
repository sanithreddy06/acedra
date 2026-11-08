# Smart Campus Intelligence — Known Limitations & Future Horizons

As part of responsible software engineering and architectural transparency, the following technical limitations and operational boundaries are documented for the current prototype release (v0.1):

---

## 1. Storage & Vector Database Fallbacks

1. **Local SQLite vs Production PostgreSQL with pgvector**:
   - In local development mode, the application defaults to SQLite with JSON-based vector embeddings for ease of evaluation and zero-dependency testing.
   - For production clustering, `docker-compose.prod.yml` deploys PostgreSQL 16 with native `pgvector` HNSW indexes. When running under SQLite, semantic vector search falls back to exact cosine distance calculation in Python memory, which is performant for <10,000 document chunks but requires migration to pgvector for millions of institutional chunks.

2. **File Storage Backend**:
   - Ingested documents (PDFs, DOCX files) and exported reports are persisted to the local filesystem (`storage/documents` and `storage/reports`) or Docker volume mounts.
   - Production campus environments spanning multiple server nodes should attach an S3-compatible object store (e.g., AWS S3, MinIO, or Google Cloud Storage) using a pluggable storage adapter.

---

## 2. LLM Orchestration & Inference

1. **Heuristic & Grounded Fallback**:
   - When external LLM API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`) are not provided in `.env`, the system executes deterministic synthesis rules and grounded RAG passage extraction.
   - This ensures 100% offline functionality, testability, and deterministic unit test execution without external API billing dependencies, but lacks free-form creative prose compared to frontier LLM APIs.

2. **Prompt Injection Boundary**:
   - While regex pattern filtering and untrusted context sanitation neutralize known prompt injection and jailbreak directives, extreme multi-turn indirect jailbreaks remain an active research problem. An external safety model (such as Llama-Guard or Google Vertex AI Safety Filters) should be configured in enterprise deployments.

---

## 3. Real-Time Telemetry & Notification Delivery

1. **Browser In-App Notifications**:
   - In the prototype, alerts and notifications are delivered via polling and database state updates rather than full bi-directional WebSockets.
   - The conversational AI assistant provides Server-Sent Events (SSE) token streaming via `/api/v1/ai/conversations/{id}/messages/stream`. Real-time push notifications across other modules can be upgraded to WebSockets via Redis Pub/Sub in a future minor release.

2. **Email Delivery**:
   - Email dispatch is prepared via SMTP configuration in `.env.production.example`. In local development, email dispatches are logged to application audit logs to prevent accidental outbound mail transmission.

---

## 4. Synthetic Academic Datasets

1. **Cohort Scale**:
   - The seeded database contains 160+ synthetic student profiles spanning Computer Science & Engineering (CSE) across 8 semesters.
   - While large enough to test multi-page sorting, search filtering, and complex aggregation performance, institutional stress testing across 20,000+ students across multiple universities will require database sharding and read replicas.
