# ICF AI Copilot

> AI-powered Decision Intelligence platform for the IBM AI Builders Challenge
> Wildcard — Intelligent Systems for the Future of Work

---

## What it does

ICF AI Copilot helps people make better personal and professional decisions by:

1. **Assessing** the user across three evidence-informed domains: **Mind** (Big Five, perceived stress), **Goal** (priority clarity, SDT), and **Work Capacity** (burnout indicators)
2. **Building** a multidimensional AI profile synthesized by IBM Granite
3. **Answering** decision-support questions in a streaming AI chat powered by RAG + watsonx.ai
4. **Generating** prioritized action plans with explainable AI rationale
5. **Monitoring** AI interactions through watsonx.governance with full audit trails

---

## IBM Technologies

| Technology | Role |
|---|---|
| **IBM watsonx.ai + Granite-13b-chat-v2** | All LLM generation: profile synthesis, copilot responses, action plans |
| **IBM Granite Embeddings** | Vector encoding for pgvector semantic search |
| **Watson Discovery** | RAG knowledge corpus (psychology, burnout, SDT research) |
| **watsonx.governance** | Per-response explainability, bias monitoring, audit log |

---

## Architecture

```
Next.js 14 (Vercel)
    │ HTTPS / REST + SSE
FastAPI (Railway)
    ├── PostgreSQL + pgvector
    └── IBM watsonx.ai + Watson Discovery + watsonx.governance
```

See [`icf-ai-copilot-plan.md`](../icf-ai-copilot-plan.md) for the full architecture design.

---

## Platform Surfaces

- **User App** — Individual assessment, AI Copilot, profile, action plans
- **Org Workspace** — Aggregated anonymized insights, member management
- **Coach Portal** — Consent-gated member summaries, cohort insights

---

## Local Development

### Prerequisites

- Node.js ≥ 20
- Python 3.12
- Docker Desktop

### 1. Start the database

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### 2. Start the API

```bash
cd apps/api
cp ../../infrastructure/.env.example .env
# Fill in your IBM watsonx and Clerk credentials in .env
pip install -r requirements.txt
# Run migrations
cd ../..
alembic upgrade head
# Start the server
cd apps/api
uvicorn main:app --reload --port 8000
```

### 3. Start the web app

```bash
cd apps/web
cp ../../infrastructure/.env.example .env.local
# Fill in NEXT_PUBLIC_* values
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

All variables documented in [`infrastructure/.env.example`](infrastructure/.env.example).

Key variables:

| Variable | Description |
|---|---|
| `WATSONX_API_KEY` | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID |
| `CLERK_SECRET_KEY` | Clerk backend secret |
| `CLERK_WEBHOOK_SECRET` | svix webhook signing secret |
| `DATABASE_URL` | PostgreSQL+asyncpg connection string |

---

## Safety & Ethics

- The platform does **not** diagnose medical or mental health conditions
- Every AI response in wellbeing domains includes a clinical disclaimer
- A crisis safety gate runs before every LLM call
- Aggregate org/coach insights require a minimum of 5 users
- Full AI audit log via watsonx.governance

See [`docs/safety/non-diagnostic-guidelines.md`](docs/safety/non-diagnostic-guidelines.md)

---

## Project Structure

```
icf-ai-copilot/
├── apps/
│   ├── web/          # Next.js 14 (Vercel)
│   └── api/          # FastAPI (Railway)
├── packages/
│   └── shared-types/ # Shared TypeScript contracts
├── infrastructure/
│   ├── docker-compose.yml
│   ├── .env.example
│   └── migrations/   # Alembic
└── docs/
    ├── adr/          # Architecture Decision Records
    └── safety/
```

---

## Competition

**IBM AI Builders Challenge — Wildcard: Intelligent Systems for the Future of Work**

Demonstrates: AI Co-worker · Decision Intelligence · Workflow Orchestration · Personalized Recommendations · Explainable AI · Human-AI Collaboration
