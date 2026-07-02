#!/usr/bin/env bash
# ==========================================================================
# Cymbal Retail Agents — Step 1: Enable required Google Cloud APIs
# Run from Cloud Shell or any terminal with gcloud installed & authenticated.
#
# Usage:  bash setup/01_enable_apis.sh YOUR_PROJECT_ID
# ==========================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ No project ID. Usage: bash setup/01_enable_apis.sh YOUR_PROJECT_ID"
  exit 1
fi

echo "🔧 Setting active project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "🔧 Enabling APIs (takes 1–2 minutes)..."
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  --project "$PROJECT_ID"

echo ""
echo "✅ APIs enabled:"
echo "   - Vertex AI (Gemini models, RAG Engine, Agent Engine)"
echo "   - Cloud Storage (staging bucket + RAG documents)"
echo "   - Cloud Build / Cloud Run / Artifact Registry (MCP server deployment)"
echo ""
echo "➡️  Next: python setup/02_create_rag_corpus.py"
