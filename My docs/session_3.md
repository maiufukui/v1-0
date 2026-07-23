# Agent Memory and Graph-Enhanced Agentic RAG

---

## Intro + Concept

Hi everyone. Today I will be walking through this lab where I extended the agentic RAG system from Session 2 with two new capabilities: memory, so the agent can remember things across conversations, and graph-enhanced retrieval, so the agent can follow relationships between concepts instead of just finding similar chunks.

In particular the first breakout was focused on memory architecture looking at how long memory lasts, who controls it, where information lives, and what kind of information belongs in each memory type.

The second breakout was focused on retrieval approaches showing what dense vector search can't do, and how a source-grounded knowledge graph can help address what is missing, and how the agent can choose between dense retrieval and graph traversal.

By the end of this lab, I learned about the different long-term memory types (semantic, episodic, and procedural), how to implement short term and long term memory with LangGraph, manage context with summarization middleware and combine all memory types in one agent.

I also learned how to build a source-grounded knowledge graph and how to give an agent the tools to choose between dense and graph retrieval based on the structure of the question.

---

## Task 1 — Imports and Setup

First I will cover the environment set up. In addition to the LangChain and LangGraph components from Session 2, I'm now pulling in `InMemorySaver` for thread-scoped checkpoints, `InMemoryStore` for cross-thread memory, `ToolRuntime` for passing user identity into tools, `SummarizationMiddleware` and `dynamic_prompt` for context management, and `networkx` for the knowledge graph.

---

## Task 2 — A Practical Memory Model

*[Show: Task 2 dimension tables]*

Before jumping into the lab, I wanted to walk through a high level overview on memory and how to think about it.

The first dimension is scope — how long does it last and where does it persist? Short-term memory is the current conversation, stored in checkpointed graph state under a `thread_id`. Long-term memory lives in a store with a namespace and key, and persists across threads.

The second dimension is type — what kind of information is stored long-term? Semantic memory is facts and preferences. Episodic memory is past experiences and outcomes. Procedural memory is instructions and policy rules.

---

## Task 3 — Short-Term Memory

*[Show: InMemorySaver setup, then thread isolation demo]*

For short-term memory, I created an agent with an `InMemorySaver` checkpointer.

In the first example, I sent 2 messages — the agent remembered Luna's name and details of our conversation, which was saved under `thread_luna`.

When I asked the same question on a different thread, the agent had no memory of it — because the checkpoint is scoped to the other thread.

---

## Task 4 — Long-Term Memory

For long-term memory, we used a store to hold data that can be shared across threads. Long-term memories are defined by `namespace + key`.

**Step 1 — Define who the user is.** This is the trusted identity object. It is always created by the app, not the model.

```python
@dataclass(frozen=True)
class UserContext:
    user_id: str
```

**Step 2 — Define what fields can be saved.** This constrains what the model is allowed to write — it cannot invent new profile keys.

```python
ProfileField = Literal[
    "cat_name",
    "age_years",
    "food_preference",
    "care_routine",
    "communication_preference",
]
```

**Step 3 — Create the store with an embedding index.** The embedding index enables semantic search. Profile fields are stored with exact key lookup, but semantic memories use `index=["text"]` for similarity search. Same store, different indexing per record.

```python
memory_store = InMemoryStore(
    index={"embed": embeddings, "dims": 1536}
)
```

**Step 4 — Define the namespace function.** Every read and write goes through this with completely separate namespaces in the store. This is the isolation mechanism — two users never share a namespace.

```python
def profile_namespace(user_id: str) -> tuple[str, str]:
    return (user_id, "profile")
```

**Step 5 — Create the write tool with explicit write policy baked in.**

```python
@tool
def save_profile_memory(field: ProfileField, value: str, runtime: ToolRuntime[UserContext]) -> str:
    """Save one user-confirmed cat profile field. Call only when the user explicitly asks to remember it."""
    runtime.store.put(
        profile_namespace(runtime.context.user_id),
        field,
        {
            "value": cleaned_value,
            "source": "user_confirmed",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        index=False,
    )
```

**Step 6 — Create the read and delete tools.** Both scope every operation to the current user via `profile_namespace(runtime.context.user_id)`.

```python
@tool
def list_profile_memories(runtime: ToolRuntime[UserContext]) -> str:
    items = runtime.store.search(profile_namespace(runtime.context.user_id))

@tool
def delete_profile_memory(field: ProfileField, runtime: ToolRuntime[UserContext]) -> str:
    runtime.store.delete(namespace, field)
```

**Step 7 — Wire it all together.**

```python
long_term_agent = create_agent(
    model=llm,
    tools=[save_profile_memory, list_profile_memories, delete_profile_memory],
    system_prompt=LONG_TERM_SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
    store=memory_store,
    context_schema=UserContext,
)
```

`store=memory_store` connects the store. `context_schema=UserContext` tells the agent what shape the runtime context takes. Both are required — without `context_schema`, `runtime.context.user_id` would fail.

**Isolation test:**

*[Show code]* Here is an example of asking the agent to remember 2 details — it properly stored the details with the namespace, key, and value created by the tool.

*[Show code]* Next is an example of a different thread for the same user, with the store shared. As you can see it properly responded to the query.

*[Show code]* Here is an example to show that one user's profile does not leak to another user's conversation. `user-123` saved Luna's name, so in this thread with `user-456`, when asked what the agent remembered, the store correctly returned nothing for `user-456`.

---

## Task 5 — Summarization Middleware

*[Show: SummarizationMiddleware setup]*

Here we add `SummarizationMiddleware` to compress long conversation histories. Once the thread hits 8 messages, it replaces older ones with a summary and keeps the 4 most recent.

While this is helpful, summarization is very lossy. Therefore user-confirmed facts, consent flags, and anything the user might want to delete should not rely on a generated summary — those belong in the structured store.

---

## Activity 1 — Consent-Aware Cat Profile

For Activity 1, I extended the profile memory system so it supports 2 users with isolation to avoid leaking data between them.

- Added two new profile fields — `vet_clinic_name` and `cat_gender`
- Modified `save_profile_memory` to require an explicit consent flag. If consent is `False`, the tool returns an error and writes nothing. If there is no value, nothing is saved.
- Added a length cap at 500 characters to reject oversized inputs and empty values
- Added an `export_profile_memories` tool so a user can see everything stored about them in one call
- To demonstrate isolation, I created two users — `user-a` and `user-b`
  - Saved `cat_name`, `vet_clinic_name`, and `cat_gender` only under `user-a`'s namespace, then exported both profiles
  - `user-a` got the full profile back. `user-b` got an empty output.
  - I then tried to delete `cat_name` from `user-b`'s namespace — but could not because the key didn't exist there — and confirmed `user-a`'s record was untouched

The key insight: isolation works because every read and write uses `profile_namespace`, and the app supplies `user_id` — the model never chooses which namespace to access.

---

## Task 6 — Semantic Memory

*[Show: semantic_memories dict and memory_store.search output]*

Task 6 stores facts and preferences as semantic memory.

I stored four items for `user-123` — Luna's food texture preference, the user's communication preference, the carrier routine observation, and the timing of the annual visit.

The key difference from the profile fields in Task 4 is that these are stored with `index=["text"]` so they can be retrieved by semantic similarity, not just exact key lookup.

I tested retrieval with the query "How should I format a plan for Luna's vet appointment?" — even though none of the keys contain the word "format", the store returned the `appointment-style`, timing, and `carrier-routine` memories as the top matches because the text content was semantically close.

This shows the difference between exact lookup and semantic search over stored memory.

---

## Task 7 — Episodic Memory

*[Show: episodes dict and memory_store.search output]*

Task 7 stores past experiences. Each episode has a situation, an action taken, an outcome, a source, and a safety note.

I stored three episodes — the carrier prep before a vet visit, the appointment checklist that got positive feedback, and a food texture transition.

To test this, I asked "What response format worked well for appointment preparation?" — the `appointment-checklist` episode came back as the top match.

The safety note is important here. Episodic memory is about learning from outcomes. The risk is an agent treating a past answer as verified truth and repeating it even if it was wrong or circumstances changed. The safety note is a guardrail against that.

---

## Task 8 — Procedural Memory with Review

*[Show: base_procedure, propose_procedure_revision, apply_approved_procedure_revision]*

Task 8 stores instructions about how the agent should behave. The source draft lets user feedback rewrite the system prompt, which is risky.

The solution is a staged review workflow: feedback comes in, the model proposes a candidate revision without applying it, a human reviewer checks it, and only then is it written to the store with the approved version.

I tested it with feedback asking for checklist-first answers.

**Step 1 — The base policy lives in the store, not the system prompt.**

**Step 2 — Feedback produces a candidate. Nothing is written yet.**

```python
def propose_procedure_revision(feedback: str) -> ProcedureRevision:
    """Generate a candidate policy revision without applying it."""
```

**Step 3 — A human-reviewed revision is applied with a version bump and `approved_by` recorded.**

```python
def apply_approved_procedure_revision(revision: ProcedureRevision, *, approved_by: str) -> dict:
```

The key takeaway: user preferences belong in semantic memory, shared safety rules belong in procedural memory with access controls.

---

## Task 9 — Unified Memory Agent

*[Show: format_store_items helper, then memory_aware_system_prompt]*

Task 9 brings all memory types into one agent. Before building the agent itself, I set up a `format_store_items` helper that converts store results into labeled text blocks — it's what structures the memory sections injected into the prompt.

The core of Task 9 is the `@dynamic_prompt` middleware. It runs before every model call and reads all four memory sources from the store — profile, semantic, episodic, and procedural. All four get injected into the system prompt as separate labeled sections. User memory can inform the answer but can't override the safety instructions that come from procedural memory.

The agent itself combines everything — tools for writing, listing, and deleting profile memory, the dynamic prompt middleware, summarization middleware, a checkpointer for thread state, and the store for cross-thread memory.

### Visualize the Agent

Running the graph visualization shows the compiled agent including all middleware nodes — the dynamic prompt node, the model, the tools node, and the summarization middleware node. This is the same compiled LangGraph structure as `create_agent`, but now you can see memory injection as an explicit node in the graph before every model call.

### Run Across Threads — Thread 1, Message 1

*[Show: first unified_agent.invoke call and output]*

The first call asks: "Help me prepare for Luna's annual appointment. Use the response format that has worked well before."

Before the model even sees this question, the `@dynamic_prompt` middleware fires — it searches semantic memory for appointment-related context and pulls the episodic memory about the checklist format that got positive feedback. The model receives Luna's preferences and the past episode as context, and produces a checklist-first response matching the format from the episode.

### Run Across Threads — Thread 1, Message 2 (Follow-Up)

*[Show: follow-up unified_agent.invoke on the same thread]*

The follow-up on the same thread asks: "Make the checklist even shorter. What was the cat's name?"

The name comes from checkpointed thread state, the format instruction comes from the live conversation context. Both are in play at the same time.

### Run Across Threads — New Thread, Same User

*[Show: cross-thread unified_agent.invoke on new thread]*

The final call starts a brand new thread for the same user and asks: "What food texture preference do you remember?"

This is a fresh thread so there's no checkpoint to restore. However, the agent still answers correctly because the food texture preference lives in the store under `(user-123, "semantic")`, not in the thread. The store is shared across all threads for that user, therefore the agent was able to answer this question.

---

## Task 10 — See the Dense Retrieval Limitation

*[Show: MarkdownHeaderTextSplitter and chunk build, then print_dense_results output]*

Task 10 loads and indexes the same cat health corpus from earlier sessions, but this time using `MarkdownHeaderTextSplitter` first to split on document title and section, preserving section metadata on each chunk. Then `RecursiveCharacterTextSplitter` breaks those into smaller pieces with chunk size 800 and overlap 100. Each chunk gets a `chunk_id` and source in its metadata.

```python
vector_store = QdrantVectorStore.from_documents(...)
```

Once indexed into Qdrant, I ran the key relationship query:

> "How are senior cats, increased thirst, kidney disease, home monitoring, and veterinary care connected?"

The dense results came back individually relevant — chunks about senior cats, chunks about hydration — but nothing that explicitly shows the chain connecting all five concepts.

That's the limitation being demonstrated: similarity search finds chunks that are close to the query, but it can't surface the relationship path between concepts that live in different sections.

---

## Task 11 — Build a Small Source-Grounded Knowledge Graph

*[Show: reviewed_relations list, then knowledge_graph build loop, then edge print output]*

Task 11 starts from reviewed triples instead of using an LLM to extract triples from every chunk automatically, as this adds cost and can produce unsupported relationships.

Each triple explicitly carries a subject, relation, object, evidence phrase, source section, and the chunk ID it came from. The chunk ID gets attached automatically using `chunk_id_for_section`, which looks up which chunk belongs to that section.

Then the graph is built using `networkx.MultiDiGraph` — a directed graph that allows multiple edges between the same two nodes. `entity_to_chunk_ids` is a separate lookup that maps each entity to the chunk IDs associated with it — this is what later allows the traversal to recover source documents from the graph.

The printed output shows 8 edges covering the chains. Every edge has a chunk ID so every relationship traces back to a specific piece of source text.

---

## Task 12 — Traverse the Graph and Recover Source Chunks

*[Show: ENTITY_ALIASES, find_query_entities, traverse_graph, then graph_results output]*

Task 12 has three moving parts: entity matching, graph traversal, and chunk recovery.

**Entity matching** uses a hand-reviewed alias map to connect natural question language to graph node names. `find_query_entities` normalizes both the query and the alias keys, then returns whichever graph nodes matched.

**Graph traversal** uses up to `max_hops=2`. Starting from each matched entity, it walks outward across the undirected version of the graph and records every node it reaches along with its distance.

**Chunk recovery** scores each chunk based on how close its associated entity was to the starting point — entities at distance 0 score 1.0, distance 1 score 0.5, distance 2 score 0.33. If multiple entities map to the same chunk, the chunk keeps the highest score.

Running the relationship query, the output showed all five concepts matched as start entities, the full relationship path printed as a chain, and the supporting source chunks returned with their scores and section names. The graph made the connection path inspectable in a way dense search couldn't.

---

## Task 13 — Agent Chooses Dense or Graph Retrieval

*[Show: both tool definitions, GRAPH_RAG_PROMPT, then print_agent_stream for both questions]*

Task 13 gives the agent two tools with deliberately different contracts so the model can distinguish when to use each. The system prompt reinforces the distinction — use dense for focused questions, graph for relationships and multi-hop questions, and both are available if needed.

**Question 1 — "What signs suggest a urinary emergency in a cat?"**

- The agent called the dense tool, as the question is direct and focused, asking for specific symptoms.
- Dense retrieval returned the litter box and urinary warning signs chunk as the top result, and the agent answered from that.

**Question 2 — the relationship query about senior cats, increased thirst, kidney disease, home monitoring, and veterinary care:**

- The agent called the graph tool, received the relationship path and supporting chunks, and grounded its answer in the connection chain rather than just listing similar content.

---

## Activity 2 — Extend the Graph

*[Show: new_relation definition, knowledge_graph build, alias addition, graph_results output]*

In Activity 2 I extended the knowledge graph with one new reviewed triple from the Dental And Oral Health section, then confirmed the graph traversal could reach it.

**Step 1 — Define the new triple.**

I chose the relationship between dental disease and bad breath as a warning sign. The triple follows the exact same structure as the reviewed relations in Task 11 — subject, relation, object, section, and evidence.

The evidence string matters here — it's what makes this triple reviewable and traceable, not just an assertion.

**Step 2 — Attach the chunk ID and add to the graph.**

I used the same `chunk_id_for_section` lookup from Task 11 so the triple automatically points to the correct source chunk. Then I followed the exact same build pattern as Task 11 — normalize both entity strings, add nodes, add the directed edge with all metadata, and update `entity_to_chunk_ids` for both entities so chunk recovery works during traversal.

The `entity_to_chunk_ids` update on both entities is important — without it, `graph_results` would find the nodes during traversal but have no chunk to return as evidence.

**Step 3 — Add an alias.**

I added an entity alias to match the new node from natural question language. The alias key needs to be a phrase someone might actually use, and the value must exactly match the subject string used when building the graph.

```python
ENTITY_ALIASES["tooth problems"] = "dental disease"
```

The value `"dental disease"` matches exactly because `normalize_entity("dental disease")` produces `"dental disease"` — the same normalized string already in the graph as a node.

**Step 4 — Confirm the output.**

```python
activity_query = "How are tooth problems and bad breath connected in cats?"
graph_context = graph_results(activity_query, max_hops=2)
```

The output confirmed all four requirements:

- **Matched entities** — shows dental disease
- **Relationship path** — the new edge appeared: `dental disease --warning signs include--> bad breath [chunk-id]`
- **Supporting source chunk** — the Dental And Oral Health chunk was returned with a score of 1.0 since both matched entities were at distance 0 from the start

The key insight from this activity: adding a new triple to the graph is a deliberate, reviewable action — you define the evidence, attach it to a source chunk, and update the alias map. Nothing is inferred automatically. That traceability is what makes graph-grounded answers trustworthy.

---

## Key Takeaways

1. **Memory has two dimensions: scope and type.** Scope is how long and where it persists — short-term is thread state, long-term is a namespaced store. Type is what kind of information it is — semantic, episodic, and procedural. Clearly defining and understanding this is important in making sure the right architecture is used.

2. **User isolation is defined by the app, not the model.** The namespace must be keyed to a trusted identity supplied by the app. The moment the model chooses which namespace to read or write, isolation breaks.

3. **Summarization compresses history — it does not replace memory.** Anything a user might want to correct or delete must live in the structured store with provenance, not in a generated summary.

4. **Graph retrieval and dense retrieval are complementary, not competing.** Dense finds similar chunks. Graph follows the connection path between concepts. The contract in the tool docstrings is what ensures the agent chooses the right tool.
