# 🛍️ Cymbal Customer Desk
### A real-world multi-agent system with RAG + custom MCP server on Google Cloud
Built with **ADK** (Agent Development Kit) · **Vertex AI RAG Engine** · **Model Context Protocol** · **Agent Engine** · **Cloud Run** — designed as a complete corporate training project for GCP trial accounts.

**Business scenario:** Cymbal Retail's AI support desk. A coordinator agent routes customers to a **policy expert** (RAG over official documents), an **operations specialist** (live orders/inventory/returns via a custom MCP server with hard guardrails), or an **escalation agent** (human-handoff tickets).

```
user → coordinator ─┬→ knowledge_agent  ── Vertex AI RAG Engine (3 policy docs)
                    ├→ operations_agent ── MCP server (orders, stock, shipments, returns)
                    └→ escalation_agent ── function tools (ticket queues + SLAs)
```

## ⚡ Quickstart (local, ~15 minutes)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # set GOOGLE_CLOUD_PROJECT

gcloud auth application-default login
bash setup/01_enable_apis.sh YOUR_PROJECT_ID
python setup/seed_database.py             # fake OMS/WMS data (SQLite)
python setup/02_create_rag_corpus.py      # prints RAG_CORPUS → paste into .env

python tests/test_local.py                # free smoke test (DB + MCP, no LLM)
adk web                                   # open http://localhost:8000
```

Try: *"Track order ORD-78002"* · *"What's the return window for Plus members?"* · *"Return ORD-78001, it's defective"* (triggers the ₹20,000 approval guardrail → escalation ticket).

## 📁 What's where

| Path | Purpose |
|---|---|
| `STEP_BY_STEP_GUIDE.md` | **Start here** — full 8-module trainer guide (business case → local build → Cloud Run → Agent Engine → teardown) |
| `LEARNER_LAB_EXERCISES.md` | 6 graded hands-on labs with rubric |
| `customer_desk/` | The ADK multi-agent package (`agent.py` = root coordinator; `sub_agents/` = RAG, MCP, escalation agents; `prompts.py` = all instructions) |
| `mcp_server/retail_ops_server.py` | Custom MCP server: 6 tools over SQLite, stdio **and** streamable-HTTP transports, guardrails in code |
| `data/knowledge_base/` | 3 policy documents ingested into the RAG corpus |
| `setup/` | API enablement, DB seeding, RAG corpus creation |
| `deployment/` | Cloud Run deploy (MCP server) + Agent Engine deploy (agents) |
| `eval/smoke.evalset.json` | ADK evaluation suite (`adk eval customer_desk eval/smoke.evalset.json`) |
| `tests/test_local.py` | Offline smoke test of DB + MCP layer |

## 💡 What this project teaches
1. **Multi-agent orchestration** — LLM-driven delegation with a coordinator + specialist sub-agents.
2. **Managed RAG** — Vertex AI RAG Engine corpus creation, retrieval tuning (`top_k`, distance threshold), grounded answers.
3. **MCP end-to-end** — building a server (FastMCP), consuming it (`McpToolset`), and promoting stdio → remote HTTP on Cloud Run.
4. **All three ADK tool patterns** — built-in retrieval tool, MCP toolset, plain function tools.
5. **Production guardrails** — deterministic policy enforcement in tool code, not prompts.
6. **Path to production** — Agent Engine deployment, IAM, tracing, evaluation, teardown discipline.

## Requirements
Python 3.10–3.12 · gcloud CLI (or Cloud Shell) · a GCP project with billing (trial credits are ample; local modules cost cents).

*Cymbal Retail is a fictional company; all data is synthetic. Apache-2.0-style classroom use encouraged.*
