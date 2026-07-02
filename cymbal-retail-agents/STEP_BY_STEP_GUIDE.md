# 🏗️ Cymbal Customer Desk — Step-by-Step Build Guide
### Multi-Agent System with RAG + Custom MCP Server on Google Cloud
*(Gemini Enterprise Agent Platform: ADK · Vertex AI RAG Engine · Agent Engine · Cloud Run)*

**Audience:** learners on a GCP trial account · **Time:** ~4–6 hours (or 2 half-day sessions)
**Naming note:** Google rebranded Vertex AI Agent Builder to the **Gemini Enterprise Agent Platform** at Cloud Next 2026. The building blocks are unchanged: **ADK** (code-first framework), **Agent Studio** (low-code visual builder), **Agent Engine** (managed runtime). This project uses ADK because it teaches transferable engineering skills; Module 8 shows where Agent Studio fits.

---

## 📋 Business Requirement (share this with learners first)

> **Cymbal Retail** (fictional omnichannel retailer, 4M customers) receives 60,000 support contacts/month. 70% fall into two buckets: **policy questions** ("what's the return window?") answered from static documents, and **operational requests** ("where's my order?", "start a return") requiring live system access. Human agents average 8 minutes per contact and frequently quote outdated policies.
>
> **Goal:** an AI support desk that (1) answers policy questions **grounded in official documents only** — no hallucinated policies, (2) executes operational tasks against **live systems of record** with hard guardrails (e.g., refunds > ₹20,000 need supervisor approval), and (3) **escalates to humans** with well-formed tickets when required.
>
> **Success criteria:** grounded answers with sources · zero unauthorized high-value refunds · full audit trail of every tool call · deployable to a managed, scalable runtime.

**Why this architecture maps to the requirement:**

| Requirement | Component |
|---|---|
| Grounded policy answers | `knowledge_agent` + **Vertex AI RAG Engine** corpus |
| Live system actions with guardrails | `operations_agent` + **custom MCP server** (guardrails in code) |
| Human handoff | `escalation_agent` + function tools (ticket queues + SLAs) |
| One front door, right specialist | root **coordinator** `LlmAgent` with LLM-driven delegation |
| Managed, scalable runtime | **Agent Engine** + MCP server on **Cloud Run** |

```
                    ┌───────────────────────────┐
     Customer ────► │ customer_desk_coordinator │  root agent (Gemini 2.5 Flash)
                    └────────────┬──────────────┘
          ┌──────────────────────┼───────────────────────┐
          ▼                      ▼                        ▼
  knowledge_agent         operations_agent          escalation_agent
  RAG retrieval tool      MCP toolset               Python function tools
          │                      │                        │
  Vertex AI RAG Engine    Retail Ops MCP Server     Ticket queues (in-mem →
  (3 policy documents)    (SQLite: orders, stock,   Jira/ServiceNow in prod)
                          shipments, returns)
```

The project deliberately shows **all three ADK tool patterns** — a built-in retrieval tool (RAG), an MCP toolset, and plain function tools — in one coherent business scenario.

---

## Module 0 — Prerequisites & trial-account hygiene (20 min)

1. **GCP trial account** with billing enabled (your 120-day trial credits cover everything here; a full run of all modules typically consumes only a few dollars of credit — Gemini Flash calls, one small RAG corpus, and short-lived Cloud Run/Agent Engine instances).
2. **Python 3.10–3.12**, `git`, and the **gcloud CLI** — or simply use **Cloud Shell**, which has all three preinstalled (recommended for classrooms: zero laptop setup).
3. Authenticate for Application Default Credentials:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

> **Trainer tips for trial accounts**
> - Keep everything in **us-central1** — best model/RAG availability.
> - `gemini-2.5-flash` is the default model here; it's cheap and fast. Compare against `gemini-2.5-pro` only in a short demo.
> - Modules 1–5 run **locally** (only model + RAG calls bill). Cloud Run and Agent Engine start in Modules 6–7 — and Module 8 tears them down.
> - Set a **budget alert** at ₹1,000/$15 in Billing → Budgets on day one. Good habit, good teaching moment.

---

## Module 1 — Project setup (15 min)

```bash
# Unzip the project and enter it
cd cymbal-retail-agents

# Virtual environment
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# Dependencies (ADK, Vertex AI SDK, MCP SDK)
pip install -r requirements.txt

# Environment file
cp .env.example .env
# Edit .env → set GOOGLE_CLOUD_PROJECT to your trial project ID
```

**Checkpoint ✅** `adk --version` prints a version; `python -c "import mcp"` succeeds.

---

## Module 2 — Enable APIs & seed the "enterprise systems" (15 min)

```bash
# Enable Vertex AI, Storage, Cloud Run, Cloud Build, Artifact Registry
bash setup/01_enable_apis.sh YOUR_PROJECT_ID

# Create the SQLite database simulating the OMS/WMS/CRM
python setup/seed_database.py
```

The seed creates 4 customers, 6 orders, 7 SKUs, and shipments — including **ORD-78002**, a deliberately *DELAYED* shipment that triggers the goodwill-voucher policy. Teaching data is scripted so every learner sees identical, predictable behavior.

**Checkpoint ✅** `data/retail.db` exists; the script prints "Seeded operational database".

---

## Module 3 — Build the RAG layer (Vertex AI RAG Engine) (30 min)

**Concept (10 min whiteboard):** RAG Engine is Google's *managed* RAG pipeline — it handles chunking, embedding (`text-embedding-005`), vector storage, and retrieval behind one API. You bring documents; it returns relevant passages. Contrast with DIY RAG (you'd manage a vector DB, chunking strategy, and embedding pipeline yourself).

```bash
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
python setup/02_create_rag_corpus.py
```

The script creates corpus `cymbal-retail-policies`, uploads the three policy markdown files from `data/knowledge_base/`, and **prints a `RAG_CORPUS=` line — paste it into `.env`**.

Verify in the console: **Vertex AI → RAG Engine** → your corpus → 3 files.

**How the agent consumes it** — open `customer_desk/sub_agents/knowledge_agent.py`:
- `VertexAiRagRetrieval` is a prebuilt ADK tool pointed at the corpus.
- `similarity_top_k=5` → retrieve 5 chunks; `vector_distance_threshold=0.6` → drop weak matches. These two knobs are your precision/recall dials (Lab 2 tunes them).
- The instruction forces *"ALWAYS call the tool before answering"* — grounding by prompt **and** by tool design.

**Checkpoint ✅** `.env` contains a full `RAG_CORPUS=projects/.../ragCorpora/...` value.

---

## Module 4 — Build & understand the custom MCP server (45 min)

**Concept (15 min):** MCP (Model Context Protocol) is the open standard for exposing tools/data to AI clients — "USB-C for AI tools." Build the Retail Ops server **once**, and ADK agents, Claude Desktop, IDEs, or any MCP client can use it. This is the decoupling story enterprises care about: tool teams ship servers; agent teams consume them.

Open `mcp_server/retail_ops_server.py` and walk through:
- **FastMCP** turns decorated Python functions into MCP tools; **docstrings become tool descriptions** — this is prompt engineering for tools. Vague docstring ⇒ wrong tool selection.
- Six tools: `get_order_details`, `list_customer_orders`, `track_shipment`, `check_inventory`, `initiate_return`, `get_return_status`.
- **Guardrails live in code, not prompts**: `initiate_return` refuses non-DELIVERED orders, caps refunds at the order total, and forces refunds > ₹20,000 into `PENDING_APPROVAL`. An LLM cannot talk its way past deterministic checks.
- **Dual transport**: `stdio` (local subprocess — dev) and `streamable-http` (Cloud Run — prod). Same code, one flag.

Test the server **without any LLM** (free):
```bash
python tests/test_local.py
```
This lists the tools over stdio and calls two of them directly — proving the MCP layer works independently of the agents. That separation is your debugging superpower.

**Checkpoint ✅** Smoke test prints 6 tools and two successful tool calls.

---

## Module 5 — Wire the multi-agent system & run it (60 min)

**Concept (15 min):** ADK multi-agent patterns. This project uses **LLM-driven delegation**: the coordinator's `sub_agents=[...]` list plus each sub-agent's `description` lets Gemini decide who handles each turn (agent transfer). Mention the alternatives for contrast — `SequentialAgent`/`ParallelAgent` for fixed pipelines, and `AgentTool` for using an agent as a callable tool.

Walk the code, bottom-up:
1. `customer_desk/prompts.py` — every instruction in one file. Routing rules are *explicit* ("policy → knowledge_agent…").
2. `sub_agents/knowledge_agent.py` — RAG tool (Module 3).
3. `sub_agents/operations_agent.py` — `McpToolset`: if `MCP_SERVER_URL` is empty it **spawns the local server over stdio automatically**; if set, it connects over streamable HTTP. One env var flips dev → prod.
4. `sub_agents/escalation_agent.py` — plain Python functions as tools; type hints + docstrings are the tool schema.
5. `agent.py` — the root `LlmAgent` exposing `root_agent` (the name `adk web` looks for).

**Run it:**
```bash
adk web        # from the project root; open http://localhost:8000
```
Select **customer_desk** and run the demo script:

| Prompt | Expected route | Watch for (Events tab) |
|---|---|---|
| "What's your return policy for electronics?" | knowledge_agent | RAG retrieval call + retrieved chunks |
| "Track order ORD-78002" | operations_agent | MCP `track_shipment` + the DELAYED `agent_hint` |
| "Is the AeroBook laptop in stock in Delhi?" | operations_agent | `check_inventory` (Delhi stock = 1) |
| "I want to return ORD-78001, it's defective" | knowledge → operations → escalation | ₹24,999 > ₹20,000 ⇒ `PENDING_APPROVAL` ⇒ ticket |
| "My toaster is sparking!" | escalation_agent | `PRIORITY_SAFETY` ticket, 2-hour SLA |

The **Events tab** is the teaching star: every agent transfer, tool call, and tool response is inspectable. Have learners screenshot the trace for prompt 4 — it shows all three sub-agents cooperating on one request.

**Also demo:** `adk eval customer_desk eval/smoke.evalset.json` — ADK's built-in evaluation harness with two regression cases (extend it in class).

**Checkpoint ✅** All five demo prompts route correctly; learners can explain the trace.

---

## Module 6 — Productionize the MCP server on Cloud Run (30 min)

Stdio subprocesses don't exist in a managed runtime, so promote the MCP server to a remote service:

```bash
bash deployment/deploy_mcp_cloudrun.sh YOUR_PROJECT_ID
```

This builds the root `Dockerfile` (server + freshly seeded demo DB baked in) and deploys with `--no-allow-unauthenticated` — then prints the IAM command granting Agent Engine's service agent `run.invoker`. For a quick classroom demo you *may* redeploy with `--allow-unauthenticated`, but teach the authenticated path as the default posture.

Then:
```bash
# .env → MCP_SERVER_URL=https://retail-ops-mcp-....run.app/mcp
adk web   # restart; ask "track ORD-78003" and watch Cloud Run logs stream
```

**Checkpoint ✅** Order queries now hit Cloud Run (visible in its Logs tab).

---

## Module 7 — Deploy the agents to Agent Engine (45 min)

Agent Engine is the managed runtime: autoscaling, sessions, IAM identity, tracing — no servers.

```bash
# One-time staging bucket
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-agent-staging
# .env → STAGING_BUCKET=gs://YOUR_PROJECT_ID-agent-staging

python deployment/deploy_agent_engine.py
```

The script wraps `root_agent` in an `AdkApp` (tracing on), uploads the `customer_desk` package, injects env vars (`RAG_CORPUS`, `MCP_SERVER_URL`, `MODEL`), deploys (~5–10 min), then runs a remote smoke query. It also **refuses to deploy if `MCP_SERVER_URL` is empty** — a deliberate guard reinforcing the Module 6 lesson.

If RAG queries fail remotely, grant the Reasoning Engine service agent access:
```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

Show learners the deployed agent under **Vertex AI → Agent Engine** in the console, including traces of the smoke query.

**Checkpoint ✅** Remote `stream_query` returns the ORD-78003 status via Cloud Run MCP + Agent Engine.

---

## Module 8 — Wrap-up: Agent Studio context, extensions, teardown (30 min)

**Where Agent Studio fits:** open the **Agent Studio** visual builder in the console and show how the same coordinator/sub-agent pattern can be prototyped low-code, then exported/hardened in ADK. Positioning: *Studio for prototyping and business users; ADK for production engineering.* (Also mention **Agent Garden** samples and the **A2A protocol** for cross-vendor agent interop as further reading.)

**Real-world extension ideas (assign as capstones):**
- Swap SQLite for **Cloud SQL/AlloyDB**; swap in-memory tickets for Firestore or a real Jira MCP server.
- Add **Memory Bank** so the agent remembers the customer across sessions.
- Add **Model Armor** / input screening in front of the coordinator.
- Add a fourth sub-agent (e.g., billing) and a payments FAQ to the corpus.

**Teardown (do this in class — trial discipline):**
```bash
python deployment/deploy_agent_engine.py --delete <RESOURCE_NAME>
gcloud run services delete retail-ops-mcp --region us-central1
# Delete the RAG corpus: console → Vertex AI → RAG Engine → corpus → Delete
gsutil rm -r gs://YOUR_PROJECT_ID-agent-staging
```

---

## 🩺 Troubleshooting quick reference

| Symptom | Likely cause → fix |
|---|---|
| `403 PERMISSION_DENIED` on model calls | ADC not set → `gcloud auth application-default login`; API not enabled → rerun Module 2 |
| Knowledge agent answers without sources / errors | `RAG_CORPUS` empty or wrong region in `.env` → rerun Module 3 and paste the printed value |
| Operations agent: "MCP session failed" | DB not seeded → `python setup/seed_database.py`; or stale `MCP_SERVER_URL` pointing at a deleted Cloud Run service → blank it for local mode |
| `adk web` shows no agent | Run from the **project root** (the folder *containing* `customer_desk/`), not inside it |
| Import errors on `McpToolset`/connection params | Old ADK → `pip install -U google-adk` (this project targets ADK ≥ 1.5) |
| Agent Engine deploy fails on packaging | Missing `STAGING_BUCKET` or bucket in wrong region → recreate in us-central1 |
| Cloud Run 403 when agent calls MCP | Run the `add-iam-policy-binding … roles/run.invoker` command printed by the deploy script |
| Trial credits draining | Check Billing → Reports; ensure Module 8 teardown ran; keep `min-instances 0` on Cloud Run |
| `vertexai.rag is deprecated` warning | Harmless — the module still works. Google is migrating RAG APIs to the new `agentplatform` client; a great 5-minute class discussion on API lifecycle. |

---

## 🎓 Suggested 2-session delivery plan

**Session 1 (theory + local build):** Business case & architecture (30m) → Modules 0–2 (30m) → Module 3 RAG (45m) → Module 4 MCP (45m) → Module 5 multi-agent demo (60m) → Labs 1–2.
**Session 2 (labs + production):** Labs 3–5 (75m) → Module 6 Cloud Run (30m) → Module 7 Agent Engine (45m) → Module 8 + teardown (30m) → Lab 6 / capstone briefing.
