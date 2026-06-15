# Loom Script: Multi-Agent Deep Research for Cat Nutrition and Obesity
**Target length:** 5–7 minutes | ~850–1000 words | Audience: instructor, class members, new students
**Note:** Script follows the notebook top to bottom — scroll with it in real time.

---

## [0:00–0:25] Intro + Core Idea

Hi everyone. Today I wanted to walk through the multi-agent deep research lab, which takes a fundamentally different approach from the first three sessions. Instead of one agent with tools, this lab is about composing multiple specialized agents into a coordinated research pipeline.

The question the system answers is: *what does current evidence say about preventing and safely managing obesity in adult indoor cats?*

That's a hard research question — not a lookup. Answering it well requires scope definition, parallel investigation across different source types, source verification, report writing, and citation auditing. No single agent should be responsible for all of that. This lab is about understanding *why not*, and what to do instead.

The mental model is a pipeline:
```text
scope → delegate → search → verify → write → audit → evaluate
```
Every stage is a named agent or a deterministic code step. The key insight before we even look at a line of code: **multi-agent systems are primarily a context engineering choice** — you use them when different stages need different prompts, different tools, different cost controls, or different context windows.

---

## [0:25–0:55] Task 1 — Environment Setup and Budget Profile

[*Show: imports cell, then API key / budget config cell*]

Task 1 sets up the environment. The imports are denser than previous labs — we're pulling in Pydantic for typed contracts, Tavily's search and extract clients, LangChain's `create_agent` and middleware, and LangGraph for the outer workflow.

The budget config cell is important. Instead of hardcoding limits in agent definitions, the lab externalizes them as environment variables:

```python
os.environ["AIM_SEARCH_DEPTH"] = "advanced"
os.environ["AIM_SEARCH_CALL_LIMIT"] = "4"
os.environ["AIM_EXTRACT_CALL_LIMIT"] = "3"
os.environ["AIM_WORKER_MODEL_CALL_LIMIT"] = "10"
```

This is deliberate design — **research depth is an application policy, not a model property**. We'll see exactly why that matters in Activity 2.

---

## [0:55–1:45] Task 2 — Typed Handoff Contracts

[*Show: Pydantic model definitions — ResearchTask, ResearchFindings, ResearchDossier, FinalReport, CitationAudit*]

Task 2 is where the architecture really starts. Every handoff between agents is a Pydantic model. `ResearchTask` is what the supervisor sends a worker. `ResearchFindings` is what the worker sends back. `ResearchDossier` is the aggregated output. `FinalReport` is what the writer produces. `CitationAudit` is what the deterministic auditor produces.

Why does this matter? Free-form prose is ambiguous — each agent interprets "give me a useful summary" differently. Typed contracts make the boundaries explicit and enforceable. They provide structural guarantees: required fields exist, types are correct, list lengths are bounded.

The key thing to notice across all these models is that **source URLs are first-class data**. Every `SourceRecord` has a URL. Every `ClaimRecord` has `source_urls`. The writer's `FinalReport` has a `citations` list. URL provenance is tracked from the first search result through to the final report — and the system will reject URLs that can't be traced back to actual tool output.

**Question 1 answer:** Some things are application guarantees — schema shape, URL provenance, task alignment, citation audit pass/fail. Other things are still model judgment — which sources are authoritative, which claims to extract, what confidence level to assign, how to synthesize across specialists. You want the application to own the things that must be right, and let the model own the things that require judgment.

---

## [1:45–2:15] Task 3 — Tavily + URL Provenance

[*Show: tavily_search and tavily_extract init, then normalize_url, observed_tool_urls, sanitize_findings*]

Task 3 configures the two Tavily tools — search finds candidate sources, extract reads selected pages more deeply. We deliberately do not use Tavily's Research API because the whole point is to build the multi-agent behavior ourselves.

The more important code here is the URL provenance layer:

```python
def observed_tool_urls(agent_result: dict) -> set[str]:
    observed: set[str] = set()
    for message in agent_result.get("messages", []):
        if isinstance(message, ToolMessage):
            observed.update(urls_in_value(message.content))
    return observed
```

Every URL that appears in a tool message gets extracted and normalized. Then `sanitize_findings` drops any source or claim whose URL wasn't actually observed in tool output. This doesn't prove a claim is correct — it just prevents the agent from hallucinating a URL that was never returned by a search or extract call. It's a provenance check, not a truth check.

---

## [2:15–2:55] Tasks 4 & 5 — Specialized Workers + Supervisor Tools

[*Show: GUIDELINE_RESEARCHER_PROMPT and EVIDENCE_RESEARCHER_PROMPT, then worker creation, then @tool wrappers*]

Task 4 creates two research workers. They use the same model and the same tools, but their system prompts make them fundamentally different actors. The guideline researcher prioritizes AAFP, AAHA, WSAVA, and professional organizations. The evidence researcher prioritizes peer-reviewed studies and actively challenges broad nutrition claims — it's designed to push back on weak evidence.

Each worker gets **fresh middleware per run** via `worker_middleware()`:

```python
def worker_middleware():
    return [
        ModelCallLimitMiddleware(run_limit=WORKER_MODEL_CALL_LIMIT, exit_behavior="end"),
        ToolCallLimitMiddleware(tool_name=tavily_search.name, run_limit=SEARCH_CALL_LIMIT, exit_behavior="continue"),
        ToolCallLimitMiddleware(tool_name=tavily_extract.name, run_limit=EXTRACT_CALL_LIMIT, exit_behavior="continue"),
    ]
```

Task 5 wraps each worker in a high-level `@tool` that the supervisor can call. This is the central subagent pattern: **supervisor → high-level worker tool → create_agent worker → Tavily**. The supervisor sees one compact JSON result per worker call — it never receives the worker's full message history, all the search traces, or intermediate reasoning steps.

Failures are also isolated. If a worker errors out, `failed_findings` returns a structured gap record instead of crashing the whole pipeline. One failed research stream becomes a visible evidence gap, not a silent data loss.

**Question 2 answer:** What stays inside the worker: the full ReAct loop, all Tavily responses, the system prompt, intermediate reasoning. What crosses the boundary: a `ResearchTask` JSON in, a `ResearchFindings` JSON out. This keeps the supervisor's context clean, makes cost per stage predictable, and makes failures attributable. The cost tradeoff is real — you pay for multiple agent runs instead of one. But the debuggability benefit — being able to point to exactly which worker produced a bad finding — is often worth it.

---

## [2:55–3:20] Task 6 + Activity 1 — Supervisor and Methodology Specialist

[*Show: SUPERVISOR_PROMPT and research_supervisor creation, then Activity 1 methodology worker*]

Task 6 builds the research supervisor. It receives the scoper's brief — exactly three tasks — and delegates each one to the right specialist. The critical instruction in the prompt is to emit all independent tool calls in the same model turn so the runtime can execute them in parallel.

The supervisor is still agentic — the model decides which worker to call and can revise its approach after seeing worker outputs. But operational middleware caps delegation at 6 model calls and 3 calls per worker tool, preventing a runaway loop.

Activity 1 adds a third specialist — a methodology researcher whose job is to appraise study design, sample size, randomization quality, and bias risks. I extended `SpecialistName` to include `"methodology"` and added a focused prompt:

```python
METHODOLOGY_RESEARCHER_PROMPT = f'''
You are the methodology specialist...
Score methodological quality and note bias risks such as small samples, industry
funding, surrogate outcomes, or extrapolation from dogs or humans to cats.
'''
```

The key Activity 1 insight: this specialist has a separate context window because methodology appraisal involves heavy intermediate reasoning — stepping through methods sections, evaluating confounders, distinguishing association from causation. You don't want that reasoning polluting the guideline researcher's context. Separate context windows keep each actor focused. The cost is one more concurrent worker run, which raises total spend even if wall clock time stays similar since all three can run in parallel.

---

## [3:20–3:55] Tasks 7 & 8 — Scoper, Verifier, Writer, Evaluator

[*Show: SCOPER_PROMPT and scoper_agent, then verifier/writer/evaluator creation*]

Breakout Room 2 builds the outer workflow. Task 7 creates the scoper, which converts an open-ended request into exactly three bounded research tasks — or asks one clarification question if the request is too ambiguous.

The scoper returns a `ScopeDecision`:

```python
class ScopeDecision(BaseModel):
    needs_clarification: bool
    clarification_question: str | None = None
    assumptions: list[str]
    brief: ResearchBrief | None = None
```

If `needs_clarification` is True, LangGraph — not the scoper — handles the pause and resume with `interrupt()`. The scoper's only job is to produce the decision. The graph owns what happens next.

Task 8 creates three more agents. The verifier uses Tavily Extract to inspect candidate URLs and approves only sources it can actually confirm through tool output. Critically, **verification is separate from writing** — the writer receives only the verification report, so it cannot quietly promote a weak source while composing polished prose.

The evaluator sees the report, the verification report, and the citation audit. It scores on six dimensions: coverage, synthesis, source quality, citation integrity, uncertainty handling, and medical safety. But there's a hard override: if the deterministic citation audit failed, the evaluator's `passed` is forced to `False` in code — the model cannot pass an evaluation when the audit failed, regardless of what it scored.

---

## [3:55–4:25] Tasks 9 & 10 — Graph State, Nodes, and Deterministic Citation Audit

[*Show: DeepResearchState TypedDict, then scope_node / verify_node / audit_node, then audit_report_citations*]

Task 9 defines the LangGraph state — a `TypedDict` where each field is the typed output of one pipeline stage. Each node reads what it needs and writes a typed result forward. Error handling uses fallback objects — if verification fails, a `VerificationReport` with all claims marked unsupported is returned, so the write stage still has something to work with.

**Question 3 answer:** `create_agent` owns dynamic, model-driven decisions within one role — what to search for, how to evaluate a source, what confidence to assign. LangGraph owns deterministic lifecycle decisions: pipeline order, the clarification branch, interrupt/resume, URL sanitization after agent output, and the citation audit. The decision that would be hardest to move across that boundary is the citation audit — currently it's pure Python and can be unit tested with synthetic data, no model required. If it moved inside an agent, the check becomes probabilistic and flaky.

Task 10 is that audit:

```python
def audit_report_citations(report: FinalReport, verification: VerificationReport) -> CitationAudit:
    approved = {normalize_url(source.url) for source in verification.approved_sources}
    # checks: unknown URLs, duplicate citations, missing [N] markers
    passed = bool(cited) and not unknown and not duplicates and not missing_markers
```

It checks four things: every cited URL is in the approved set, no duplicate citations, no missing numeric markers, and at least one citation exists. These are all deterministic Python assertions — no LLM call, no probability involved. Model confidence is not enough for citation integrity.

---

## [4:25–5:00] Tasks 11 & 12 — Compile, Visualize, and Run

[*Show: graph_builder wiring, then deep_research_graph.get_graph().draw_mermaid_png(), then stream output*]

Task 11 wires the full LangGraph. The graph structure is:

```text
START → scope
scope --[clarification needed]-→ clarify → scope (loop back)
scope --[brief ready]-→ research → verify → write → audit → evaluate → END
```

`InMemorySaver` is required here — not optional. Without a checkpointer, `interrupt()` in the clarify node can't recover the paused state when you resume.

Task 12 runs the system end to end using streaming with `subgraphs=True`, which shows nested namespaces — you can see `outer-graph → research_supervisor → guideline_researcher → tools` all updating in real time. That observability is the whole point of streaming: you can watch the delegation hierarchy as it executes.

**Question 4 answer from my run:** Yes, the supervisor called all three workers in the same turn — three interleaved UUIDs in the stream. The evidence worker with the most search-heavy task hit Tavily twice before others hit it once. During verification, all sources were rejected because Tavily returned 400 errors and the tool-call limit was hit, so no URL could be extracted and confirmed. The writer preserved what verification recorded — it said verification retrieval failed and explicitly noted that as the gap, rather than inventing conclusions.

---

## [5:00–5:45] Activity 2 — Research Depth and Cost Comparison

[*Show: Activity 2 budget table, then Basic and Advanced results side by side*]

Activity 2 runs the same query twice with two budget profiles. This is the most instructive exercise in the lab.

**Basic profile** (`search_depth=basic`, 1 search call, 1 extract call, 4 model calls per worker): Tavily returned 400 errors, the tool-call cap was hit almost immediately, and zero sources were approved. The writer produced a report using a placeholder `"/"` as a citation — which failed the audit immediately. Evaluation also failed. The run cost about $0.044 and took 67 seconds. It saved money but delivered nothing usable.

**Deep profile** (`search_depth=advanced`, 4 search calls, 3 extract calls, 10 model calls): Tavily retrieved and extracted content from AAHA and WSAVA guideline hub pages. Two sources were approved, five claims were verified, and the citation audit passed. But — and this is the key insight — the **evaluation still failed**. Coverage and source quality both scored 3, because we got hub pages, not the underlying guideline PDFs or peer-reviewed studies. Extra budget bought better citations and grounding, not a complete answer to the brief.

The real takeaway: **research budget controls failure mode, not just speed**. Basic fails before verification can run at all. Deep at least fails with verified sources and honest gaps. For a production system, I would set citation audit failures as a hard zero-tolerance threshold — every citation must be traceable — while accepting that some questions on difficult topics will return low evaluation scores. The budget profile is a policy decision: how much evidence is enough before the report ships?

---

## [5:45–6:10] Key Takeaways

Three big things I'm walking away from this lab with:

**Multi-agent systems are a context engineering choice** — you split into agents when different stages genuinely need different prompts, context, or cost controls. Not just because more agents feels more sophisticated.

**The boundary between `create_agent` and LangGraph is a design principle** — `create_agent` owns dynamic reasoning inside one role, LangGraph owns fixed application rules about ordering, branching, and safety. The citation audit lives in LangGraph because it must be deterministic and testable. That rule should not be negotiable by the model.

**URL provenance and citation auditing are not optional** — partial failures must become visible gaps, not fabricated evidence. The whole sanitize_findings, sanitize_dossier, sanitize_verification chain, ending with a pure Python citation audit, is what keeps a system like this honest. Model confidence is never enough for source integrity.

And the cross-cutting lesson for research depth: budget is not a cost knob. It is a **quality-and-failure-mode policy**. Know what failure rate you can accept, and set your limits accordingly.

Thanks for watching.

---

## End of Script

**Total estimated runtime:** ~6 minutes at natural speaking pace

**Key code snippets covered:**
- Budget env vars (Task 1)
- Pydantic handoff contracts — ResearchTask, ResearchFindings (Task 2)
- `observed_tool_urls` + `sanitize_findings` (Task 3)
- `worker_middleware()` + named workers (Task 4)
- `@tool` wrapper pattern — supervisor → worker → Tavily (Task 5)
- `SUPERVISOR_PROMPT` + parallel delegation (Task 6)
- `METHODOLOGY_RESEARCHER_PROMPT` (Activity 1)
- `ScopeDecision` + `interrupt()` path (Task 7)
- Evaluator override for citation audit failure (Task 8)
- `DeepResearchState` TypedDict (Task 9)
- `audit_report_citations` (Task 10)
- Graph wiring + `InMemorySaver` (Task 11)
- `subgraphs=True` streaming + Q4 trace analysis (Task 12)
- Basic vs. Deep budget comparison (Activity 2)
