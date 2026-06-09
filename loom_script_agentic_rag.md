# Loom Script: Cat Health Agentic RAG with LangChain and LangGraph
**Target length:** ~4 minutes | ~600 words | Audience: instructor, class members, new students
**Note:** Script follows the notebook top to bottom — scroll with it in real time.

---

## [0:00–0:20] Intro + Concept Shift

Hi everyone. Today I wanted to walk through this lab where I built an agentic RAG system using LangChain, LangGraph, and a Qdrant vector store.

In Session 1, retrieval was a fixed first step — every question triggered a retrieve call. The pattern was always: question, retrieve, generate.

This lab changes that. Retrieval becomes a tool the agent can choose to call — or not. The agent reads the question, decides whether it needs context from the cat health guidelines, and then answers. That decision is now the agent's to make.

---

## [0:20–0:35] Task 1 — Imports and Setup

[*Show: imports cell*]

Before walking through the lab, I wanted to briefly cover the environment setup. The imports cover each stage of the workflow — `create_agent` and middleware from LangChain, `TextLoader` for document loading, `ChatOpenAI` and `OpenAIEmbeddings` for the model and embeddings, `QdrantVectorStore` for the vector store, and `StateGraph`, `ToolNode`, and `tools_condition` from LangGraph for the explicit agent loop in Breakout Room 2.

---

## [0:35–1:00] Task 2 — Load, Chunk, and Index

[*Show: TextLoader and RecursiveCharacterTextSplitter cells*]

For the corpus, I loaded a cat health guidelines Markdown file using `TextLoader`. I then chunked it into 10 pieces using `RecursiveCharacterTextSplitter` with a chunk size of 900 and an overlap of 120. The overlap is important — it preserves context across chunk boundaries so relevant information doesn't get cut off at the edges.

Those chunks were then embedded and stored in an in-memory Qdrant collection. In-memory means no Docker or cloud account needed — the collection just disappears when the kernel stops.

---

## [1:00–1:20] Task 3 — The Retrieval Tool

[*Show: `@tool` function*]

Now here's where the shift from Session 1 actually happens. Instead of wiring retrieval directly into the pipeline, I wrapped it as a LangChain `@tool`. The docstring acts as a contract — it tells the model exactly what topics this tool covers, and the model uses it to decide when to call it.

```python
@tool
def retrieve_cat_health_guidelines(query: str) -> str:
    """Search the cat health guideline corpus for relevant context about cat preventive care,
    nutrition, hydration, vaccines, parasites, dental health, urinary warning signs, emergencies,
    senior cats, stress, behavior, and safe home monitoring."""
    results = vector_store.similarity_search_with_score(query, k=retrieval_k)
    if not results:
        return "No relevant cat health guideline context found."
    return _format_retrieved_docs(results)
```

I also tested the tool directly before building the agent — just to see what the model would actually receive. The top chunks came back relevant and scores were solid.

---

## [1:20–1:45] Task 4 — `create_agent` with Middleware

[*Show: `create_agent` call*]

The first way I built the agent loop was with `create_agent`. You hand it the model, the tool, a system prompt, and middleware, and it assembles the loop for you.

```python
agent_middleware = [
    log_before_model,
    ModelCallLimitMiddleware(run_limit=4, exit_behavior="end"),
]

agent = create_agent(
    model=llm,
    tools=[retriever_tool],
    system_prompt=AGENT_SYSTEM_PROMPT,
    middleware=agent_middleware,
)
```

Middleware lets you add behavior to the loop without rebuilding it. I used a `before_model` hook to log each step, and a `ModelCallLimitMiddleware` to cap at 4 model calls per run — without that, a confused agent can keep looping and rack up costs.

---

## [1:45–2:30] Task 5 — Stream the Agent: Examples 1–3

[*Show: `print_agent_stream` output, scroll through examples*]

Task 5 is where you actually see the agent making decisions. The stream shows each node update so you can watch the path the agent took, not just the final answer.

**Example 1** — "What urinary signs suggest my cat needs urgent veterinary care?" The agent called the retrieval tool and expanded the question into a longer search query. It pulled chunk 4 — litter box and urinary warning signs — with a score of 0.78, and chunk 5 on symptoms needing vet attention. The final answer was grounded directly in those chunks, with sources.

**Example 2** — "What preventive care should an adult cat get each year?" Again the tool was called. It retrieved chunk 1, the preventive care section, with a score of 0.77, and the answer walked through the annual exam items from that chunk.

**Example 3** — "Who won the 2022 FIFA World Cup?" No tool call at all. The agent declined and said it's scoped to the cat health guidelines. That's the system prompt doing the filtering — not the retriever.

---

## [2:30–2:50] Activity 1 — Retrieval Budget

[*Show: Activity 1 code and output*]

For Activity 1, I added a retrieval budget — at most one tool call per run using `ToolCallLimitMiddleware`:

```python
retrieval_budget = ToolCallLimitMiddleware(
    tool_name=retriever_tool.name,
    run_limit=1,
    exit_behavior="continue",
)
```

When I asked the agent to search separately for urinary signs and annual preventive care, it tried to fire two calls at once. Middleware allowed the first and blocked the second — the output literally says "Tool call limit exceeded. Do not call 'retrieve_cat_health_guidelines' again." The second topic came back incomplete. That's the trade-off: cost control at the expense of multi-topic answer quality.

---

## [2:50–3:30] Task 6 — Explicit LangGraph Loop

[*Show: `StateGraph` construction*]

The second way I built the same loop was with LangGraph directly. I defined a `StateGraph`, an agent node, a `ToolNode`, and used `tools_condition` as the conditional edge — retrieve if there's a tool call, otherwise end.

```python
langgraph_builder = StateGraph(MessagesState)
langgraph_builder.add_node("agent", call_model)
langgraph_builder.add_node("tools", ToolNode([retriever_tool], handle_tool_errors=True))

langgraph_builder.add_edge(START, "agent")
langgraph_builder.add_conditional_edges("agent", tools_condition)
langgraph_builder.add_edge("tools", "agent")
```

Everything `create_agent` handled automatically is now explicit and editable. The same two test questions — urinary signs and the FIFA question — produced the same behavior, which confirms the loops are equivalent.

---

## [3:30–3:50] Activity 2 — Scope Routing

[*Show: routed graph and `route_question`*]

For Activity 2, I added a deterministic routing step at `START`. A keyword check runs before the agent — clearly off-topic questions route to an `out_of_scope` node and skip the model entirely:

```python
def route_question(state: MessagesState) -> str:
    text = _latest_user_text(state)
    if any(keyword in text for keyword in UNRELATED_KEYWORDS):
        return "out_of_scope"
    if any(keyword in text for keyword in CAT_HEALTH_KEYWORDS):
        return "agent"
    return "agent"  # ambiguous → default to agent
```

The benefit is speed and cost savings on obvious off-topic queries. You can see it here — the FIFA question hits the `out_of_scope` node and returns instantly, zero model calls, zero retrieval:

```
--- Update from node: out_of_scope ---
This assistant is scoped only to the cat health guideline corpus,
so I can't help with that question.
```

The limitation is that keyword lists are brittle. The ambiguous question — "What should I do about frequent vomiting?" — has no cat keyword and no unrelated keyword, so it defaults to the agent. That worked fine here because vomiting is in the corpus. But something like "my pet has a urinary blockage" would also miss the keyword list since "pet" isn't in `CAT_HEALTH_KEYWORDS` — so it still routes to agent, which is the safe default, but shows the list needs constant maintenance to be reliable.

This is the key distinction between middleware and graph routing: middleware adds rules around the same flow, graph routing changes what flow runs entirely.

---

## [3:50–4:00] Key Takeaways

Three things I took from this lab: retrieval as an action — not a pre-step — is what makes it agentic. `create_agent` is the fast path, LangGraph is for when you need control. And streaming is essential — the path the agent took matters as much as the answer it gave.

Thanks for watching.
