"""Knowledge Agent — answers policy questions via Vertex AI RAG Engine."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag

from ..prompts import KNOWLEDGE_INSTRUCTION

# RAG_CORPUS looks like:
# projects/<PROJECT_NUMBER>/locations/us-central1/ragCorpora/<CORPUS_ID>
RAG_CORPUS = os.environ.get("RAG_CORPUS", "")

search_policy_knowledge_base = VertexAiRagRetrieval(
    name="search_policy_knowledge_base",
    description=(
        "Semantic search over Cymbal Retail's official policy documents: "
        "returns & refunds, shipping & delivery, warranty & Cymbal Care+. "
        "Input: a natural-language question. Output: the most relevant "
        "policy passages with sources."
    ),
    rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)] if RAG_CORPUS else [],
    similarity_top_k=5,
    vector_distance_threshold=0.6,
)

knowledge_agent = LlmAgent(
    name="knowledge_agent",
    model=os.environ.get("MODEL", "gemini-2.5-flash"),
    description=(
        "Policy expert. Answers questions about returns, refunds, shipping, "
        "delivery timelines, warranties, and Cymbal Care+ by searching the "
        "official policy knowledge base (RAG)."
    ),
    instruction=KNOWLEDGE_INSTRUCTION,
    tools=[search_policy_knowledge_base],
)
