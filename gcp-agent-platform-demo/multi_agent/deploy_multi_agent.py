"""
Deploys the travel_concierge multi-agent system to Vertex AI Agent Engine.

The whole tree (root_agent + its 3 sub_agents) deploys as ONE Agent Engine
resource — Agent Engine doesn't need separate deployments per sub-agent;
the orchestration happens inside the running agent process.

Usage:
    python deploy_multi_agent.py \
        --project=YOUR_PROJECT_ID \
        --location=us-central1 \
        --bucket=gs://YOUR_STAGING_BUCKET
"""

import argparse
import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

from travel_concierge.agent import root_agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--location", default="us-central1")
    parser.add_argument("--bucket", required=True, help="gs://your-staging-bucket")
    args = parser.parse_args()

    bucket_name = args.bucket.removeprefix("gs://").strip("/")
    if not bucket_name:
        parser.error(f"--bucket must be a non-empty gs:// path, got {args.bucket!r}")

    vertexai.init(
        project=args.project,
        location=args.location,
        staging_bucket=args.bucket,
    )

    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    print("Deploying travel_concierge (root + 3 sub-agents) to Agent Engine...")

    remote_agent = agent_engines.create(
        app,
        requirements=[
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]",
        ],
        # THIS is what was missing: ship your local source tree so the
        # remote container can actually import `travel_concierge`.
        extra_packages=[
            "./travel_concierge",
        ],
        display_name="travel-concierge-multi-agent",
    )

    print("\nDeployment complete!")
    print("Resource name:", remote_agent.resource_name)


if __name__ == "__main__":
    main()