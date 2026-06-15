# Loom Script: Agent Memory and Graph-Enhanced Agentic RAG
**Target length:** 6–7 minutes | ~950–1100 words | Audience: instructor, class members, new students
**Note:** Script follows the notebook top to bottom — scroll with it in real time.

---

## [0:00–0:35] Intro, Concept Shift, and Learning Outcomes

Hi everyone. Today I wanted to walk through the agent memory and GraphRAG lab, and I think this is the session where the agent starts to feel like a real application rather than a demo.

In Session 2, the agent could decide whether to retrieve — but it had no memory between questions. Every new conversation started from zero. This lab changes that. By the end, the agent knows who it's talking to, what they've told it before, how they prefer to communicate, and what's happened in past sessions — and it retrieves all of that before every model call, not because the model remembered to look it up.

The two breakout rooms tackle two distinct problems that are easy to conflate. Breakout Room 1 is about **memory**: where information lives, how long it persists, who controls it, and what kind of information belongs in each type. Breakout Room 2 is about **retrieval strategy**: what dense vector search can't do, and how a source-grounded knowledge graph covers what's missing. Together they answer a question that Session 2 left open — what does a stateful, relationship-aware agent actually look like in code?

By the end of this lab, I can implement all three long-term memory types — semantic, episodic, and procedural — alongside short-term checkpointed state, combine them in a unified agent using `@dynamic_prompt`, and manage context with summarization middleware. I can also build a source-grounded knowledge graph from reviewed triples, traverse it with BFS, and give an agent the tools to choose between dense and graph retrieval based on the structure of the question.

---

## [0:25–0:55] Task 1 — Imports and Setup

[*Show: imports cell*]

Task 1 sets up the environment. The imports here are denser than Session 2 — we're pulling in `InMemorySaver` for thread-scoped checkpoints, `InMemoryStore` for cross-thread persistent memory, `ToolRuntime` for injecting runtime context into tools, and `dynamic_prompt` and `SummarizationMiddleware` for context engineering. There's also `networkx` for the knowledge graph in BOR2.

The key thing before any memory work: `LANGSMITH_TRACING=true` is set here. For a multi-memory agent, LangSmith traces are how you see whether the right memory types were retrieved at the right time.

---

## [0:55–1:40] Task 2 — A Practical Memory Model

[*Show: memory model markdown table*]

Task 2 introduces the framework. Before writing a line of code, the lab stops to distinguish two orthogonal dimensions that are easy to conflate.

**Dimension 1 is scope** — how long does something persist and where?

| Scope | Mechanism | Identity |
|---|---|---|
| Short-term | Graph state + checkpointer | `thread_id` |
| Long-term | Store + namespace | Usually `user_id` |

**Dimension 2 is type** — what kind of information is stored long-term?

| Type | Contents | Example |
|---|---|---|
| Semantic | Facts and preferences | "Luna prefers shredded wet food" |
| Episodic | Experiences and outcomes | "Carrier training reduced stress before last visit" |
| Procedural | Rules and instructions | "Use short checklists, separate urgent signs" |

The key insight from this framing: **semantic, episodic, and procedural are not five competing storage products — they're three ways to organize long-term information**, all living in the same `InMemoryStore` under different namespaces.

The lab also gives four questions to ask before storing anything: How long should it last? What kind of information is it? Who does it belong to? And who can write, review, and delete it?

---

## [1:40–2:10] Task 3 — Short-Term Memory with `InMemorySaver`

[*Show: short_term_agent creation, then thread isolation test*]

Task 3 implements short-term memory. The `InMemorySaver` checkpointer saves graph state under a `thread_id`. Within the same thread, the agent remembers everything from the conversation so far.

The isolation test here is important. Luna's thread — `luna-short-term` — knows her name and that she's preparing for an annual vet visit. A new thread — `new-short-term` — gets a blank state and correctly says it has no information about the user's cat. That's not a failure — that's correct isolation. Different threads don't inherit each other's state.

The `get_state` call at the end lets you inspect the checkpoint directly:

```python
snapshot = short_term_agent.get_state(thread_luna)
print(f"Messages stored in thread: {len(snapshot.values['messages'])}")
print(f"Checkpoint ID: {snapshot.config['configurable'].get('checkpoint_id')}")
```

This is useful for debugging — you can verify the state is exactly what you expect before relying on it.

---

## [2:10–2:45] Task 4 — Long-Term Memory with `InMemoryStore`

[*Show: profile_namespace function, save_profile_memory tool, then user isolation test*]

Task 4 adds cross-thread persistence. The `InMemoryStore` holds records addressed by `namespace + key`. For user data, namespace includes a trusted user ID that the application provides — the model never decides which user's namespace to read or write.

```python
def profile_namespace(user_id: str) -> tuple[str, str]:
    return (user_id, "profile")
```

The write policy is explicit: only save when the user clearly asks. Store it as user-provided information, not a verified fact. Always provide tools to inspect and delete.

The isolation test runs two users — `user-123` saves Luna's name and a communication preference. `user-456` runs in the same store and correctly gets back "no profile memories stored." The store doesn't leak between users because every read and write is scoped to `profile_namespace(runtime.context.user_id)` — and the application supplies `user_id`, not the model.

---

## [2:45–3:10] Task 5 — Summarization Middleware

[*Show: SummarizationMiddleware init, demo_history run, message count output*]

Task 5 addresses a practical problem: checkpointed message histories grow indefinitely. Large histories cost more, add latency, and bury relevant information.

`SummarizationMiddleware` compresses older messages into a summary while keeping recent messages verbatim:

```python
SummarizationMiddleware(
    model=llm,
    trigger=("messages", 8),   # summarize after 8 messages
    keep=("messages", 4),       # keep last 4 verbatim
)
```

The lab runs a 10-message history through a summarizing agent. The returned state shows fewer messages than were sent — the middleware replaced the older ones with a summary. The thresholds here are small by design so the behavior is visible in a notebook.

**The critical safety note:** summarization is intentionally lossy. The LLM decides what to keep. Safety-critical facts, user preferences, and anything the user might want to delete should never exist *only* in a generated summary. Those belong in structured long-term memory with provenance and deletion controls.

---

## [3:10–3:35] Q1 + Q2 — When to Use Which Memory

[*Show: Q1 and Q2 cells with answers*]

**Q1** asks you to classify five items — latest follow-up question, user-confirmed communication preference, tentative model-generated diagnosis, cat name the user asked to remember, outdated routine the user asked to forget.

My answers: short-term for the follow-up question (it's only relevant in this thread). Long-term semantic for the communication preference — it's a stable user fact that should persist. *No memory at all* for the tentative diagnosis — the notebook is explicit that unverified medical inferences should never be stored as fact. Long-term semantic for the cat name — the user asked for it to be saved, and it's a fact that needs to cross threads. And no memory for the outdated routine — the write policy says to delete when asked.

**Q2** asks why summarization is not a substitute for structured memory. The answer comes down to three things: summaries are lossy and LLM-generated with no guaranteed accuracy; their purpose is cost and context control, not reliable storage; and they're not structured or deletable. Anything a user might want to correct or delete must live in the store with explicit tooling.

---

## [3:35–4:20] Activity 1 — Consent-Aware Cat Profile

[*Show: Activity 1 code — ProfileField extension, consent flag, MAX_PROFILE_VALUE_LENGTH, export tool, isolation test*]

Activity 1 extends the profile memory system. I added two new `ProfileField` values — `vet_clinic_name` and `cat_gender` — and rewrote `save_profile_memory` with three new guardrails:

```python
@tool
def save_profile_memory(field: ProfileField, value: str, consent: bool, runtime: ToolRuntime[UserContext]) -> str:
    if not consent:
        return "Nothing was saved because consent was not granted."
    if len(value.strip()) > MAX_PROFILE_VALUE_LENGTH:
        return f"Nothing was saved because the value exceeds {MAX_PROFILE_VALUE_LENGTH} characters."
    runtime.store.put(
        profile_namespace(runtime.context.user_id), field,
        {"value": value.strip(), "source": "user_confirmed",
         "updated_at": datetime.now(timezone.utc).isoformat(), "consent": consent},
        index=False,
    )
```

The `consent` flag is required on every write. If `consent=False`, nothing is stored and the tool returns a clear message. The `MAX_PROFILE_VALUE_LENGTH = 500` check rejects oversized values before they hit the store.

I also added `export_profile_memories` — a tool that returns the current user's full profile as a dictionary, so users can inspect exactly what's stored.

The isolation test used two contexts: `user_a` (user-a) and `user_b` (user-b). I saved `cat_name`, `vet_clinic_name`, and `cat_gender` under `user_a`. When I called `export_profile_for_user("user-b")`, I got back an empty dict. When I tried to delete `cat_name` from `user_b`'s namespace, it was a no-op. And `user_a`'s data remained untouched. Isolation works because every operation uses `profile_namespace(runtime.context.user_id)` and the application — not the model — supplies `user_id`.

---

## [4:20–5:00] Tasks 6, 7, 8 — Semantic, Episodic, and Procedural Memory

[*Show: semantic put with index=["text"], then episodic put with safety_note, then procedural propose + apply*]

**Task 6 — Semantic Memory:** Semantic memory stores facts and preferences. The key detail here is `index=["text"]`. Profile fields were stored with `index=False` because they're retrieved by exact key. Semantic memories are stored with `index=["text"]` so they can be found by semantic similarity:

```python
memory_store.put(semantic_namespace, "food-texture",
    {"text": "Luna eats shredded wet food and usually refuses pate texture.",
     "kind": "preference", "source": "user_confirmed"},
    index=["text"],
)
```

I stored four semantic memories and then tested with the query *"How should I format a plan for Luna's vet appointment?"* — a question with no food keyword at all. The top results came back as `appointment-style` and `carrier-routine`, not `food-texture`. That's semantic search doing what keyword search can't: matching on meaning, not terms.

**Task 7 — Episodic Memory:** Episodic memory stores past experiences — situation, action, outcome. The critical addition in each record is the `safety_note`:

```python
{"situation": "Preparing questions for Luna's annual appointment",
 "action": "The assistant produced a five-item checklist grouped into observations, routine care, and questions.",
 "outcome": "The user gave positive feedback on the concise format.",
 "source": "interaction_feedback",
 "safety_note": "Reuse the format, not medical conclusions."}
```

That safety note exists because the agent should learn to reuse what worked — a format, a communication style — without copying the actual medical content from one episode into another situation where it may not apply.

**Task 8 — Procedural Memory:** Procedural memory stores how the agent should behave. The dangerous pattern from a naive draft is letting user feedback rewrite the system prompt automatically. A single bad message could weaken safety rules, and changes would be unauditable.

The lab implements a staged review workflow instead:

```python
# Step 1: propose — does not apply
candidate = propose_procedure_revision(feedback)

# Step 2: human review of candidate
# Step 3: apply only if approved
approved_procedure = apply_approved_procedure_revision(
    approved_demo_revision,
    approved_by="notebook_demo_reviewer",
)
```

The `apply_approved_procedure_revision` call bumps the version number and records who approved it. What does not happen: the model never directly writes to the procedure namespace. The application owns that gate.

---

## [5:00–5:40] Task 9 — Unified Agent with `@dynamic_prompt`

[*Show: memory_aware_system_prompt function, then unified_agent creation, then Visualize and Run Across Threads*]

Task 9 combines all five memory types in one agent using `@dynamic_prompt`:

```python
@dynamic_prompt
def memory_aware_system_prompt(request: ModelRequest) -> str:
    profile_items  = runtime.store.search(profile_namespace(user_id))
    semantic_items = runtime.store.search((user_id, "semantic"), query=query, limit=3)
    episode_items  = runtime.store.search((user_id, "episodes"), query=query, limit=1)
    procedure_item = runtime.store.get(procedure_namespace, "response-policy")
```

This runs *before every model call* — not once at agent startup. Profile is retrieved by namespace search. Semantic and episodic are retrieved by similarity against the current query. Procedural is retrieved by exact key. The assembled prompt labels each memory type and explicitly states that all user memory is *untrusted context, not instructions* — only the procedural namespace supplies instructions.

**Visualize:** `unified_agent.get_graph().draw_mermaid_png()` renders the compiled graph. `create_agent` is LangGraph under the hood — the visualization shows the agent, tools, and middleware nodes.

**Run Across Threads — three tests:**
1. `unified-luna-thread` — first request uses semantic and episodic memory about appointment prep. The agent produces a concise checklist format, matching the episodic feedback from `appointment-checklist-2025-09`.
2. Same thread follow-up — "Make the checklist even shorter. What was the cat's name?" — the agent knows Luna's name from the *checkpointed thread state*, not the store. That's short-term memory at work.
3. `unified-new-thread` — same user, new thread. Message history resets. But `memory_aware_system_prompt` still finds `food-texture` from the store and answers correctly: "Luna prefers shredded wet food." Cross-thread long-term memory worked.

---

## [5:40–6:10] BOR2 — Tasks 10–12: Dense Limitation and Knowledge Graph

[*Show: Task 10 dense query output, then Task 11 reviewed_relations build, then Task 12 graph traversal output*]

Breakout Room 2 switches to retrieval strategy. Task 10 runs the relationship query — *"How are senior cats, increased thirst, kidney disease, home monitoring, and veterinary care connected?"* — against the dense vector store. Two individually relevant chunks come back, but neither explicitly traces the full connection path. Dense search finds *similar* chunks. It does not follow *relationships*.

Task 11 builds a small source-grounded knowledge graph from reviewed triples. Every edge stores its source section, chunk ID, and an evidence phrase:

```python
reviewed_relations = [
    {"subject": "senior cats", "relation": "owners should watch for", "object": "increased thirst",
     "section": "Senior Cats", "evidence": "Owners should watch for increased thirst."},
    {"subject": "increased thirst", "relation": "should be discussed with", "object": "veterinary care", ...},
    ...
]
for relation in reviewed_relations:
    relation["chunk_id"] = chunk_id_for_section(relation["section"])
```

Why reviewed triples instead of LLM extraction? Cost, duplicate entities, and unsupported edges. The lab starts from manually verified relationships to keep the focus on retrieval behavior.

Task 12 traverses the graph using BFS from matched entities. The same relationship query now returns the full connection path — senior cats → increased thirst → veterinary care; senior cats → kidney disease → veterinarian-recommended diet — and the supporting source chunks for each. Graph search makes the reasoning path inspectable; dense search made it opaque.

---

## [6:10–6:45] Task 13 + Activity 2 — Agent Chooses + Extend the Graph

[*Show: search_cat_health_dense and search_cat_health_graph tools, then Activity 2 new triple addition*]

Task 13 gives the agent both tools:

```python
@tool
def search_cat_health_dense(query: str) -> str:
    """Search semantically similar guideline chunks for a direct, focused cat health question."""

@tool
def search_cat_health_graph(query: str, max_hops: Literal[1, 2] = 2) -> str:
    """Follow cat health relationships for a connection, pathway, or multi-hop question."""
```

The docstrings are the contracts. For the direct question about urinary emergency signs, the agent chose dense. For the multi-hop relationship question, it chose graph. The distinction in the docstrings — "direct, focused" versus "connection, pathway, or multi-hop" — is what guides that choice. If those docstrings were vague or similar, the agent would guess.

Activity 2 extends the graph with a dental disease triple. The four steps map directly to how new triples should always be added:

```python
# Step 1: Define the triple with evidence from the actual corpus
new_relation = {
    "subject": "dental disease", "relation": "warning signs include", "object": "bad breath",
    "section": "Dental And Oral Health",
    "evidence": "Warning signs include bad breath, drooling, pawing at the mouth...",
}

# Step 2: Attach chunk_id and add to graph — both subject AND object get entity_to_chunk_ids updated
new_relation["chunk_id"] = chunk_id_for_section(new_relation["section"])
entity_to_chunk_ids[subject].add(new_relation["chunk_id"])
entity_to_chunk_ids[object_].add(new_relation["chunk_id"])

# Step 3: Add an alias so the entity can be found in natural questions
ENTITY_ALIASES["tooth problems"] = "dental disease"

# Step 4: Run graph_results to confirm the new chunk is returned
graph_context = graph_results("How are tooth problems and bad breath connected in cats?")
```

The entity_to_chunk_ids update for *both* entities is easy to miss — if you only update the subject, graph traversal reaches `bad breath` but can't recover the source chunk for it.

---

## [6:45–7:30] Key Takeaways, Key Insights, and Lessons Yet to Learn

Let me end with three layers: what I'm taking away right now, what's deeper than the code, and what I still want to understand.

---

### Top 5 Key Takeaways

**1. Memory is a scope-and-type problem, not a tool selection problem.** Short-term is checkpointed thread state under a `thread_id`. Long-term is a namespaced store record. Semantic, episodic, and procedural are three ways to organize long-term information — not three competing storage systems. Get this framing right before writing a line of code.

**2. User isolation is an application responsibility, not a model responsibility.** The namespace pattern works because the application supplies `user_id`, not the model. Every read and write in this lab uses `profile_namespace(runtime.context.user_id)`. If you let the model choose the namespace, isolation breaks the moment the model reasons incorrectly about who is asking.

**3. Write policy and deletion are architecture, not afterthoughts.** Memory without a deletion path is a liability. The lab adds consent flags, length validation, and a `delete_profile_memory` tool from Task 4 onward — before any memory is actually stored. The same principle applies to procedural memory: no feedback path should ever let the model directly overwrite safety instructions.

**4. Summarization compresses context — it does not replace structured memory.** The LLM decides what to include in a summary. Facts a user confirmed, preferences they set, or instructions they might want to revoke must live in the store with provenance and deletion tools. Summarization is for cost and context management; the store is for reliable durable facts.

**5. Dense retrieval and graph retrieval are complementary, not competing.** Dense finds similar chunks for direct questions. Graph follows relationships to connected entities and their source chunks for multi-hop questions. The agent routes correctly only when the tool docstrings are clearly distinct contracts. Weak docstrings produce random routing regardless of how correct the underlying retrieval is.

---

### 5 Key Insights

**1. The `@dynamic_prompt` pattern keeps memory retrieval in application code, not model reasoning.** Running memory lookups before every model call — not relying on the model to decide when to call a memory tool — is a fundamental design choice. It makes retrieval deterministic and auditable instead of dependent on whether the model remembered to look something up.

**2. Memory type should match the update policy, not just the content.** Semantic facts have implicit expiration — a cat's routine changes. Episodic records encode feedback that may not generalize. Procedural instructions require human review before versioning. Choosing the right type is really choosing the right write, update, and delete contract for that kind of information.

**3. The knowledge graph is a provenance structure, not just a search shortcut.** Every edge in the graph stores a source section, chunk ID, and evidence phrase. The graph tells you *why* two entities are connected and *where in the corpus* that connection is supported. That's fundamentally different from similarity scores, which tell you *how related* two chunks are but not *how they're related*.

**4. Reviewed triples are a deliberate design choice, not a limitation.** A production system could use LLM extraction to build the graph automatically. But automated extraction introduces duplicate entities, unsupported edges, and indexing costs. Starting from reviewed triples keeps the lesson focused on retrieval behavior. In production, the extraction quality determines the graph quality — which determines the retrieval quality.

**5. Four questions before any memory store call are more valuable than any specific API.** Duration, type, scope, and update policy — ask those before touching the store. The specific LangGraph APIs will change. The questions won't.

---

### 5 Lessons Yet to Be Learned

**1. How do you handle memory drift and staleness at scale?** Luna's food preference might change after a vet visit. An episode from 2024 might conflict with new guidance in 2026. This lab doesn't implement TTL, versioning, or staleness detection for semantic or episodic records. How you detect and resolve conflicts in a live system is an open design problem.

**2. What's the right production store?** `InMemoryStore` disappears when the kernel stops. A real system needs a persistent, queryable store — likely one that supports both exact key retrieval and vector similarity. The choice of backend (Postgres + pgvector, Pinecone, Weaviate, etc.) affects consistency, query latency, and the operations burden.

**3. How do you scale knowledge graph construction beyond reviewed triples?** The dental disease triple in Activity 2 was added manually. Production indexing pipelines use LLM extraction, entity resolution, triple deduplication, and community detection. Microsoft GraphRAG is one full implementation. Learning how extraction quality propagates through to retrieval quality is a non-trivial research and engineering problem.

**4. How does procedural memory interact with multi-tenant systems?** This lab uses a single `("cat-health-agent", "procedures")` namespace. In a multi-tenant system with different organizations and different approved policies, who owns the procedure namespace, how are conflicting versions resolved, and how do you audit changes across tenants? The lab surfaces the problem; the production solution is an access control and governance design question.

**5. When does memory hurt more than it helps?** Storing preferences early and retrieving them persistently can cause an agent to double down on incorrect past behavior. If an early episode recorded a bad outcome but was still stored without a correction, the agent may repeat the same mistake. This lab doesn't implement correction or negative feedback loops. Learning when and how to unlearn — not just remember — is the next layer of memory system design.

---

Thanks for watching.



---

## End of Script

**Total estimated runtime:** ~7 minutes at natural speaking pace

**Key code snippets covered:**
- Memory model two-dimension table (Task 2)
- `InMemorySaver` + thread isolation demo (Task 3)
- `profile_namespace()` + write policy (Task 4)
- `SummarizationMiddleware` thresholds + safety caveat (Task 5)
- Q1 + Q2 in-line with code rationale
- `consent` flag + `MAX_PROFILE_VALUE_LENGTH` + `export_profile_memories` (Activity 1)
- Isolation test: user-a vs user-b (Activity 1)
- `index=["text"]` vs `index=False` distinction (Task 6)
- `safety_note` in episodic memory records (Task 7)
- Staged review: `propose_procedure_revision` → `apply_approved_procedure_revision` (Task 8)
- `@dynamic_prompt` with all four memory retrieval calls (Task 9)
- Visualize + three Run Across Threads tests (Task 9)
- Dense retrieval limitation query (Task 10)
- Reviewed triples + `chunk_id_for_section` (Task 11)
- BFS graph traversal + relationship path output (Task 12)
- Tool docstring contracts (Task 13)
- Four-step Activity 2 graph extension with `entity_to_chunk_ids` note
