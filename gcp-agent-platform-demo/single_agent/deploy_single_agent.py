"""
Deploys the customer_support_agent to Vertex AI Agent Engine.
"""

import argparse
import sys
import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

from customer_support_agent.agent import root_agent


def validate_bucket(bucket: str) -> str:
    if not bucket or not bucket.startswith("gs://") or not bucket[len("gs://"):]:
        sys.exit(
            f"ERROR: --bucket must look like 'gs://your-bucket-name', got: '{bucket}'"
        )
    return bucket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--location", default="us-central1")
    parser.add_argument("--bucket", required=True, help="gs://your-staging-bucket")
    args = parser.parse_args()

    bucket = validate_bucket(args.bucket)

    vertexai.init(
        project=args.project,
        location=args.location,
        staging_bucket=bucket,
    )

    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    print(f"Deploying customer_support_agent to Agent Engine (bucket: {bucket})... this can take 5-10 min")

    remote_agent = agent_engines.create(
        app,
        requirements=[
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]",
        ],
        # THIS is what was missing: ship your actual agent source code
        # so the deployed container can `import customer_support_agent`.
        extra_packages=[
            "./customer_support_agent",   # the whole package directory
        ],
        display_name="customer-support-agent",
    )

    print("\nDeployment complete!")
    print("Resource name:", remote_agent.resource_name)


if __name__ == "__main__":
    main()