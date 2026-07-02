#!/usr/bin/env bash
# ==========================================================================
# Module 6 — Deploy the Retail Ops MCP server to Cloud Run
# Turns the local stdio MCP server into a remote streamable-HTTP MCP server
# that Agent Engine (and any MCP client) can call.
#
# Usage:  bash deployment/deploy_mcp_cloudrun.sh YOUR_PROJECT_ID
# ==========================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
REGION="us-central1"
SERVICE="retail-ops-mcp"

echo "🚀 Building & deploying $SERVICE to Cloud Run in $PROJECT_ID/$REGION..."
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --port 8080 \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 2 \
  --no-allow-unauthenticated

URL=$(gcloud run services describe "$SERVICE" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format 'value(status.url)')

echo ""
echo "✅ MCP server live (auth required — recommended even for demos)."
echo ""
echo "Add to your .env:"
echo "   MCP_SERVER_URL=$URL/mcp"
echo ""
echo "Grant Agent Engine's service agent permission to invoke it:"
echo "   PROJECT_NUMBER=\$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
echo "   gcloud run services add-iam-policy-binding $SERVICE \\"
echo "     --region $REGION --project $PROJECT_ID \\"
echo "     --member=serviceAccount:service-\${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com \\"
echo "     --role=roles/run.invoker"
echo ""
echo "For a quick classroom shortcut (NOT for production), redeploy with"
echo "--allow-unauthenticated instead."

# The Dockerfile at the project root builds only the MCP server + seed data.
# expects ./Dockerfile, so copy it up first if needed:
