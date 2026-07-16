"""
Shared helper for scoring RAGAS's real `ToolCallAccuracy` metric against
this project's live agent (Q9, Q11, Q13) -- Open Items / Task 5 finding:
these three eval harnesses previously scored "tool_call_accuracy" (where
they scored it at all) with a hand-written LLM-judge PASS/FAIL prompt,
not RAGAS's actual metric class. This module wires in the real thing.

API verified against this project's actual pinned dependency
(`ragas==0.2.15` in requirements.txt), fetched directly from that exact
tag on GitHub -- NOT assumed from a newer ragas version. This matters:
the course's own Session 6 notebook environment runs a much newer ragas
dev build (0.4.4.dev8) with a different API (`ragas.metrics.collections`,
a `strict_order` kwarg, `.ascore(user_input=..., reference_tool_calls=...)`
as an async method). That newer surface does NOT exist in 0.2.15. This
project's real `ToolCallAccuracy` (`ragas.metrics.ToolCallAccuracy`, the
same one `run_eval.py` already imports RAGAS metrics from) has:
  - no `strict_order` parameter at all,
  - a synchronous public entrypoint: `.multi_turn_score(MultiTurnSample)`,
  - sequence "alignment" checked as an IN-ORDER SUBSEQUENCE match (every
    reference tool call must appear in the predicted sequence in the same
    RELATIVE order, though not necessarily adjacent -- extra/interleaved
    predicted calls are fine, out-of-order ones are not).

Two real, disclosed limitations of applying this metric honestly to this
project's tools, not hidden by tuning the reference to whatever the agent
happened to do:

1. Several of this project's tools (search_filings's `query`,
   search_filings_exact's `keywords`, search_live_news's `query`) take
   free-text arguments the agent composes itself -- there is no fixed
   "correct" string to check exact-match against, unlike the Session 6
   metal-price agent's single deterministic `metal_name` argument. Only
   `ticker` (where a tool takes one) is included in reference args here;
   free-text args are left out of the reference on purpose. A side
   effect: get_market_data's argument accuracy can be checked properly
   (ticker is its only arg), but search_live_news has no deterministic
   arg at all -- its argument-accuracy component will read 0.0 by
   construction, which is a property of the metric applied to a
   free-text-only tool, not a defect in this implementation.
2. This project's design (Task 2's Infrastructure table) treats
   search_filings and search_filings_exact as interchangeable for
   "did the agent check filings," and doesn't require Q9/Q13's three
   tool categories to fire in any particular order. RAGAS 0.2.15's
   ToolCallAccuracy supports neither "either of these tool names" nor
   true unordered matching directly (no strict_order toggle exists in
   this version). Worked around here by scoring every acceptable
   tool-name variant, in every order permutation, against the real
   predicted sequence, and reporting the best-scoring one -- a max over
   orderings of an order-sensitive containment check is the correct way
   to express "these calls, in any order," not a way of inflating the
   score.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from ragas.dataset_schema import MultiTurnSample
from ragas.messages import AIMessage, HumanMessage, ToolCall
from ragas.metrics import ToolCallAccuracy

_metric = ToolCallAccuracy()


def _to_ai_message(predicted_tool_calls: list[dict]) -> AIMessage:
    """This project's ChatResult.tool_calls (plain {"name","args"} dicts,
    extracted in app/graph.py's get_tool_calls() from the real LangGraph
    trace) collapsed into one synthetic Ragas AIMessage. Faithful to what
    ToolCallAccuracy actually reads: `_multi_turn_ascore` only pulls
    `.tool_calls` off AIMessage instances in `sample.user_input` -- it
    never inspects message content or turn structure, HumanMessage vs.
    ToolMessage boundaries, etc. -- so one AIMessage carrying the full,
    real, ordered tool-call sequence is functionally equivalent to a
    faithfully turn-by-turn-converted trace for this specific metric,
    without fabricating intermediate turns the metric wouldn't use anyway.
    """
    calls = [ToolCall(name=c["name"], args=c["args"]) for c in predicted_tool_calls]
    return AIMessage(content="", tool_calls=calls or None)


@dataclass
class ToolCallAccuracyResult:
    score: float
    best_reference: list[str]  # tool names, in the order that scored best
    all_scores_tried: list[tuple[list[str], float]]


def score_tool_call_accuracy(
    question: str,
    predicted_tool_calls: list[dict],
    acceptable_tool_sets: list[list[ToolCall]],
) -> ToolCallAccuracyResult:
    """Score real predicted tool calls against one or more acceptable
    "correct" tool-call sets, each representing a legitimate way to
    answer -- e.g. Q9 accepts either search_filings or
    search_filings_exact as the filings check. Every order permutation
    of every acceptable set is tried (see module docstring, limitation
    2); the best score wins.
    """
    ai_message = _to_ai_message(predicted_tool_calls)
    user_input = [HumanMessage(content=question), ai_message]

    all_scores: list[tuple[list[str], float]] = []
    best_score = -1.0
    best_ref: list[str] = []

    for acceptable_set in acceptable_tool_sets:
        for perm in itertools.permutations(acceptable_set):
            sample = MultiTurnSample(user_input=user_input, reference_tool_calls=list(perm))
            score = _metric.multi_turn_score(sample)
            names = [tc.name for tc in perm]
            all_scores.append((names, score))
            if score > best_score:
                best_score = score
                best_ref = names

    return ToolCallAccuracyResult(
        score=best_score, best_reference=best_ref, all_scores_tried=all_scores
    )
