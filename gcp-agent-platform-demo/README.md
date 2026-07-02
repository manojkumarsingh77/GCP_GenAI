# GCP Agent Platform — Single Agent & Multi-Agent Step-by-Step Guide

Built for a learner walkthrough. Covers:
1. One-time GCP setup (works fine on a free trial account)
2. Building + running a **single agent** locally
3. Deploying it to **Agent Engine** (the managed runtime on GCP's Agent Platform)
4. Building + running a **multi-agent system** (root agent + 3 specialists)
5. Deploying the multi-agent system

Platform used: **Vertex AI Agent Builder / Agent Platform**, built with the
**Agent Development Kit (ADK)** — Google's open-source, code-first agent
framework — and deployed to **Agent Engine**.

---

## PART 0 — One-time GCP setup (~10 minutes)

Run these in **Cloud Shell** (top-right icon in console.cloud.google.com) —
it already has `gcloud` and Python installed, so you avoid local setup issues.

```bash
# 1. Confirm you're logged in and see your trial project
gcloud auth login
gcloud projects list

# 2. Set your active project (replace with your trial project ID)
export PROJECT_ID="your-trial-project-id"
gcloud config set project $PROJECT_ID

# 3. Enable the required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com

# 4. Create a staging bucket (Agent Engine needs this for deployment artifacts)
export BUCKET_NAME="${PROJECT_ID}-agent-staging"
gcloud storage buckets create gs://$BUCKET_NAME --location=us-central1

# 5. Install Python + ADK
python3 -m venv venv
source venv/bin/activate
pip install google-adk "google-cloud-aiplatform[adk,agent_engines]"

# 6. Set default auth for the SDK
gcloud auth application-default login
```

> Trial account note: on a free trial, billing must still be linked to enable
> Vertex AI APIs (Google requires it even for free-tier usage) — your trial
> credits cover it. Agent Engine has a generous free tier on top of that, so
> a couple of demo agents won't meaningfully eat your 120-day window.

---

## PART 1 — Single Agent

Files: `single_agent/customer_support_agent/`

### What it does
A customer support agent with two tools: `get_order_status` and
`initiate_refund`. This is the simplest possible "real" agent — one model,
one instruction, a couple of tools.

### Step 1 — Get the files onto your machine/Cloud Shell
Upload the `single_agent/` folder (drag-and-drop into Cloud Shell, or `git`
push it to a repo and clone it there).

### Step 2 — Configure environment
```bash
cd single_agent
cp customer_support_agent/.env.example customer_support_agent/.env
# edit .env: set GOOGLE_CLOUD_PROJECT to your real project id
```

### Step 3 — Run it locally first (sanity check before deploying)
```bash
pip install -r requirements.txt
adk run customer_support_agent
```
Try typing: `What's the status of order ORD-1042?`
You should see the agent call `get_order_status` and answer using the result.

Or launch the visual dev UI:
```bash
adk web
```
Open the URL it prints — you get a chat UI plus a trace view showing every
tool call the agent made.

### Step 4 — Deploy to Agent Engine (GCP managed runtime)
Two equivalent options:

**Option A — single CLI command (fastest):**
```bash
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --staging_bucket=gs://$BUCKET_NAME \
  customer_support_agent
```

**Option B — Python deployment script (better for CI/CD):**
```bash
python deploy_single_agent.py \
  --project=$PROJECT_ID \
  --location=us-central1 \
  --bucket=gs://$BUCKET_NAME
```

Either way, after a few minutes you'll get a **resource name** like:
```
projects/123456789/locations/us-central1/reasoningEngines/987654321
```

### Step 5 — See it in the console
Go to **Vertex AI → Agent Builder → Agent Engine** in the GCP Console — your
`customer-support-agent` will be listed. Click in to test it from the
console Playground, see the API/Query URL, and view traces/metrics.

---

## PART 2 — Multi-Agent System

Files: `multi_agent/travel_concierge/`

### What it does
A `travel_concierge` **root agent** that delegates to three **specialist
sub-agents**:
- `flight_agent` (searches flights)
- `hotel_agent` (searches hotels)
- `weather_agent` (gives forecasts)

This demonstrates ADK's hierarchical multi-agent pattern: each sub-agent is
a complete agent in its own right (own model, own tools, own instruction),
and the root agent's LLM decides which one to hand the conversation to based
on each sub-agent's `description`. This is the natural "next step" after
single agents — same building blocks, just composed together.

### Step 1 — Configure environment
```bash
cd multi_agent
cp travel_concierge/.env.example travel_concierge/.env
# edit .env: set GOOGLE_CLOUD_PROJECT
pip install -r requirements.txt
```

### Step 2 — Run locally
```bash
adk run travel_concierge
```
Try: `I want to plan a trip from Bengaluru to Goa on 2026-08-10, back on
2026-08-13. Help me plan it.`

Watch how the root agent transfers control: flights → hotels → weather →
then summarizes everything as one itinerary.

Or use the visual UI (`adk web`) to literally watch the hand-offs between
agents in the trace panel — this is the best way to *show* learners
multi-agent routing happening in real time.

### Step 3 — Deploy
```bash
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --staging_bucket=gs://$BUCKET_NAME \
  travel_concierge
```
or
```bash
python deploy_multi_agent.py \
  --project=$PROJECT_ID \
  --location=us-central1 \
  --bucket=gs://$BUCKET_NAME
```

Important concept to call out to learners: **the whole agent tree deploys as
ONE Agent Engine resource.** You don't deploy each sub-agent separately —
Agent Engine just runs the process that contains the root agent and its
sub-agents, and orchestration happens inside that process.

---

## Teaching progression suggestion (for your training session)

1. Show the single agent running locally with `adk web` — point out the 4
   building blocks: model, instruction, tools, root_agent.
2. Deploy it live to Agent Engine, show the Console picking it up.
3. Introduce the multi-agent file — point out each sub-agent is *literally
   the same Agent class* as the single-agent demo.
4. Run `adk web` on the multi-agent version and have learners watch the
   trace view as control transfers between sub-agents.
5. Deploy the multi-agent version, compare side-by-side in the console.
6. Optional stretch: have learners add a 4th sub-agent (e.g.
   `currency_agent`) themselves as a hands-on exercise.

## Cost/cleanup tip for trial accounts
Agent Engine resources keep running (and billing) until deleted. After your
demo, clean up with:
```python
from vertexai import agent_engines
agent_engines.delete(remote_agent.resource_name)
```
or delete it from the Console under Agent Engine.
