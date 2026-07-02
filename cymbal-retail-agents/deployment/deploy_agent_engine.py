"""
Module 7 — Deploy the multi-agent system to Vertex AI Agent Engine
==================================================================
Agent Engine (part of the Gemini Enterprise Agent Platform) is Google's
fully managed runtime for agents: sessions, scaling, IAM, and tracing.

IMPORTANT before deploying:
  1. The stdio MCP transport (local subprocess) does not apply in the managed
     runtime — deploy the MCP server to Cloud Run first (Module 6) and set
     MCP_SERVER_URL in your .env to the Cloud Run URL + /mcp.
  2. Create the staging bucket:
        gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-agent-staging
  3. Grant the AI Platform Reasoning Engine service agent the
     'Vertex AI User' role so it can query your RAG corpus.

Usage:
    python deployment/deploy_agent_engine.py            # deploy
    python deployment/deploy_agent_engine.py --delete RESOURCE_NAME
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING = os.environ["STAGING_BUCKET"]


def deploy() -> None:
    if not os.environ.get("MCP_SERVER_URL"):
        sys.exit(
            "❌ MCP_SERVER_URL is empty. Deploy the MCP server to Cloud Run "
            "(Module 6) and set MCP_SERVER_URL in .env before deploying to "
            "Agent Engine."
        )

    vertexai.init(project=PROJECT, location=LOCATION, staging_bucket=STAGING)

    from customer_desk.agent import root_agent  # import after vertexai.init

    app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)

    print("🚀 Deploying to Agent Engine (5–10 minutes)...")
    remote_agent = agent_engines.create(
        agent_engine=app,
        display_name="cymbal-customer-desk",
        requirements=[
            "google-adk>=1.5.0",
            "google-cloud-aiplatform[adk,agent_engines]>=1.95.0",
            "mcp>=1.9.0",
            "python-dotenv>=1.0.1",
        ],
        extra_packages=["./customer_desk"],
        env_vars={
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "MODEL": os.environ.get("MODEL", "gemini-2.5-flash"),
            "RAG_CORPUS": os.environ.get("RAG_CORPUS", ""),
            "MCP_SERVER_URL": os.environ["MCP_SERVER_URL"],
        },
    )

    print("\n✅ Deployed!")
    print(f"   Resource name: {remote_agent.resource_name}")
    print("\nQuick remote smoke test:")
    session = remote_agent.create_session(user_id="trainer")
    for event in remote_agent.stream_query(
        user_id="trainer",
        session_id=session["id"],
        message="What is the status of order ORD-78003?",
    ):
        print(event)


def delete(resource_name: str) -> None:
    vertexai.init(project=PROJECT, location=LOCATION)
    agent_engines.get(resource_name).delete(force=True)
    print(f"🧹 Deleted {resource_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", metavar="RESOURCE_NAME",
                        help="Delete a deployed agent instead of deploying")
    args = parser.parse_args()
    if args.delete:
        delete(args.delete)
    else:
        deploy()
