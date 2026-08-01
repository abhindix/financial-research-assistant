# Enterprise Financial Research Assistant

A runnable portfolio MVP featuring PDF ingestion, dense + BM25 hybrid retrieval, LangGraph orchestration, optional Neo4j graph analytics, LM Studio integration, citations, conversation memory, SSE streaming, confidence-based human review, Prometheus metrics, Docker, Kubernetes and CI.

## Architecture

```text
SEC filings / transcripts / research PDFs
  -> PDF extraction and chunking
  -> Sentence-transformer vectors + BM25 hybrid search
  -> Neo4j Company/Metric graph lookup
  -> LangGraph retrieval -> graph -> synthesis workflow
  -> OpenAI-compatible LLM (LM Studio)
  -> FastAPI REST/SSE -> Streamlit analyst UI
```

## Windows PowerShell setup

1. Load `openai/gpt-oss-20b` in LM Studio and start its Local Server on port 1234.
2. Run:

```powershell
cd financial-research-assistant
Copy-Item .env.example .env
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In a second PowerShell:

```powershell
cd financial-research-assistant
.\\.venv\\Scripts\\Activate.ps1
streamlit run ui\\streamlit\_app.py
```

Open UI `http://localhost:8501`, API docs `http://localhost:8000/docs`, and metrics `http://localhost:8000/metrics`.

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Docker connects to LM Studio through `host.docker.internal:1234`.

## Knowledge graph model

```cypher
MERGE (c:Company {ticker:'NVDA'}) SET c.name='NVIDIA'
MERGE (m:Metric {company:'NVDA',year:2025,name:'gross\_margin\_pct'})
SET m.value=75.0,m.source\_id='nvda-2025-10k'
MERGE (c)-\[:REPORTED]->(m)
```

Add comparable metrics for AMD, Intel, Broadcom and others. Questions mentioning “gross margin” automatically query these nodes and combine graph facts with document evidence.

## Production roadmap

* Replace local persistence with PostgreSQL metadata and Redis-backed conversation checkpoints.
* Replace local hybrid retrieval with OpenSearch BM25 + k-NN and reciprocal-rank fusion.
* Ingest structured SEC XBRL facts instead of relying only on regex ratio extraction.
* Add OAuth/OIDC, RBAC, document entitlements, immutable audit logs, encryption, PII controls and secrets management.
* Add source licences for Bloomberg/Reuters; do not scrape proprietary content.
* Add evaluation datasets, retrieval metrics, hallucination checks, load tests and canary deployment.

This is an engineering portfolio project, not an investment-advice product.

