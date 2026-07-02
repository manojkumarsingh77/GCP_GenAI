"""
Cymbal Retail Agents — Step 2: Create the Vertex AI RAG Engine corpus
=====================================================================
Creates a managed RAG corpus, uploads the three policy documents from
data/knowledge_base/, and prints the corpus resource name that you must
paste into your .env file as RAG_CORPUS.

Usage:
    export GOOGLE_CLOUD_PROJECT=project-ef200147-6b7b-4fd8-9bb
    export GOOGLE_CLOUD_LOCATION=us-central1
    python setup/02_create_rag_corpus.py
"""

import os
import sys
import time
from pathlib import Path

import vertexai
from vertexai.preview import rag

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
CORPUS_DISPLAY_NAME = "cymbal-retail-policies"
KB_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"


def ensure_serverless_mode() -> None:
    """Switches the project's RAG Engine deployment mode to Serverless.

    Deployment mode (Spanner vs Serverless) is a PROJECT-LEVEL setting,
    separate from whatever vector_db you pass to create_corpus(). New
    projects default to (or attempt) Spanner mode, which is allowlist-
    restricted in us-central1/us-east1/us-east4 and fails with:
    'Spanner mode ... is restricted to only allowlisted projects'.
    This must be switched before any corpus is created.
    """
    config_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    print(f"🔧 Checking RAG Engine deployment mode for {config_name} ...")

    current = rag.get_rag_engine_config(name=config_name)
    print(f"ℹ️  Current RagEngineConfig: {current}")

    new_config = rag.RagEngineConfig(
        name=config_name,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rag.Serverless()),
    )
    updated = rag.update_rag_engine_config(rag_engine_config=new_config)
    print(f"✅ Deployment mode set to Serverless: {updated}")


def main() -> None:
    if not PROJECT_ID:
        sys.exit("❌ Set GOOGLE_CLOUD_PROJECT first, e.g. export GOOGLE_CLOUD_PROJECT=my-proj")

    print(f"🔧 Initializing Vertex AI  |  project={PROJECT_ID}  location={LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    ensure_serverless_mode()

    # ---- Reuse the corpus if it already exists (idempotent for classrooms) ----
    existing = [c for c in rag.list_corpora() if c.display_name == CORPUS_DISPLAY_NAME]
    if existing:
        corpus = existing[0]
        print(f"ℹ️  Corpus already exists, reusing: {corpus.name}")
    else:
        print(f"🔧 Creating RAG corpus '{CORPUS_DISPLAY_NAME}' "
              f"(Serverless mode + text-embedding-005)...")
        corpus = rag.create_corpus(
            display_name=CORPUS_DISPLAY_NAME,
            embedding_model_config=rag.EmbeddingModelConfig(
                publisher_model="publishers/google/models/text-embedding-005"
            ),
            vector_db=rag.RagManagedVertexVectorSearch(),
        )
        print(f"✅ Corpus created: {corpus.name}")

    # ---- Upload each knowledge base file directly (no GCS needed) ----
    files = sorted(KB_DIR.glob("*.md"))
    if not files:
        sys.exit(f"❌ No .md files found in {KB_DIR}")

    already = {f.display_name for f in rag.list_files(corpus.name)}
    for path in files:
        if path.name in already:
            print(f"ℹ️  Skipping (already imported): {path.name}")
            continue
        print(f"⬆️  Uploading {path.name} ...")
        rag.upload_file(
            corpus_name=corpus.name,
            path=str(path),
            display_name=path.name,
            description=f"Cymbal Retail policy document: {path.stem}",
        )
        time.sleep(2)  # be gentle on trial-account quotas

    print("\n📄 Files now in corpus:")
    for f in rag.list_files(corpus.name):
        print(f"   - {f.display_name}")

    print("\n" + "=" * 70)
    print("✅ RAG corpus ready. Add this line to your .env file:")
    print(f"\nRAG_CORPUS={corpus.name}\n")
    print("=" * 70)


if __name__ == "__main__":
    main()