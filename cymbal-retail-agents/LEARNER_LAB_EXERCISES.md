# 🧪 Learner Lab Exercises — Cymbal Customer Desk

Work through these after completing the setup in `STEP_BY_STEP_GUIDE.md`.
Each lab maps to a competency your trainer will assess.

---

## Lab 1 — Observe multi-agent routing (15 min)
Start `adk web` and, using the **Events tab**, trace how each prompt is routed.

Try these and record which sub-agent handled each, and which tool it called:

1. "What is your return policy for electronics?"
2. "Track my order ORD-78002."
3. "Is the Cymbal AeroBook laptop in stock in Delhi?"
4. "This kettle sparked when I plugged it in!"
5. "Can I return order ORD-78001? What refund will I get?"

**Checkpoint questions**
- For prompt 5, how many sub-agents were involved? In what sequence?
- Where in the event trace can you see the RAG chunks that were retrieved?

---

## Lab 2 — Extend the RAG knowledge base (20 min)
1. Create `data/knowledge_base/payments_and_emi_faq.md` with a short FAQ
   (EMI eligibility, failed payment retries, invoice download steps).
2. Re-run `python setup/02_create_rag_corpus.py` (it skips existing files).
3. Ask: *"Can I pay for a laptop with EMI?"* — verify grounded answers.

**Stretch:** lower `vector_distance_threshold` in `knowledge_agent.py` to 0.4.
What happens to recall vs. precision? Demonstrate with one question.

---

## Lab 3 — Add a new MCP tool (30 min)
Add a `cancel_order(order_id: str)` tool to `mcp_server/retail_ops_server.py`:
- Only orders in `PROCESSING` status may be cancelled.
- Set status to `CANCELLED` and return a confirmation payload.
- Restart `adk web` and cancel `ORD-78005` through natural conversation.

**Checkpoint:** show the tool being invoked in the Events tab, and prove
the guardrail works by trying to cancel a `DELIVERED` order.

---

## Lab 4 — Guardrail & escalation flow (20 min)
1. Ask to return **ORD-78001** (₹24,999 TV). The refund exceeds ₹20,000.
2. Verify: operations_agent creates the return in `PENDING_APPROVAL`, and the
   coordinator hands off to escalation_agent, which files a
   `SUPERVISOR_APPROVAL` ticket.
3. Ask for the ticket status using the ticket ID you received.

**Discussion:** the ₹20,000 rule is enforced in *two* places — the policy
document (RAG) and the MCP server code. Why is enforcing guardrails in
deterministic code, not just prompts, essential in production?

---

## Lab 5 — Break it, then fix it (15 min)
1. Delete `RAG_CORPUS` from `.env` and ask a policy question. Observe the
   failure mode. How could the agent degrade more gracefully?
2. Stop/rename the MCP server file and ask for an order status. What error
   surfaces, and what does the coordinator tell the user?

---

## Lab 6 (Advanced) — Production deployment
1. Deploy the MCP server to Cloud Run (`deployment/deploy_mcp_cloudrun.sh`).
2. Set `MCP_SERVER_URL` in `.env`, restart `adk web`, confirm the operations
   agent now uses the **remote** server (watch Cloud Run logs stream).
3. Deploy to Agent Engine (`python deployment/deploy_agent_engine.py`) and
   run the remote smoke query.
4. **Teardown** everything per the guide's final module — trial credits are
   precious.

---

## Grading rubric (suggested)
| Competency | Evidence | Weight |
|---|---|---|
| Multi-agent routing understanding | Lab 1 trace notes | 15% |
| RAG grounding & tuning | Lab 2 demo | 20% |
| MCP tool development | Lab 3 working tool + guardrail | 25% |
| Safety & escalation design | Lab 4 discussion answer | 15% |
| Debugging & failure analysis | Lab 5 write-up | 10% |
| Cloud deployment | Lab 6 screenshots | 15% |
