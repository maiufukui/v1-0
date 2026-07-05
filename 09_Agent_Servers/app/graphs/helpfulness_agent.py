from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.graphs.simple_agent import graph as inner_agent

# state schema for outerloop helpfulness check
from typing import Literal, NotRequired

class HelpfulnessState(MessagesState):
    loop_count: NotRequired[int]
    is_helpful: NotRequired[bool]

# judgment schema for outerloop helpfulness check
class HelpfulnessJudgement(BaseModel):
    helpful: bool = Field(
        description="True if the assistant's last answer fully and correctly answers the user's question."
    )
    reasoning: str = Field(description="One sentence explaining the verdict.")

# Node: call the inner agent and return the new messages
def call_agent(state: HelpfulnessState) -> dict:
    result = inner_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]
    return {"messages": new_messages}


# Node: judge the response and return the new state
from app.models import get_chat_model

def judge_response(state: HelpfulnessState) -> dict:
    last_answer = next(
        m for m in reversed(state["messages"])
        if isinstance(m, AIMessage) and not m.tool_calls
    )
    last_question = next(
        m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)
    )

    judge = get_chat_model().with_structured_output(HelpfulnessJudgement)
    verdict = judge.invoke([
        SystemMessage(
            content="You are an extremely strict judge. Only mark an answer helpful if it is "
            "thorough, cites specific facts from a retrieved source, and fully resolves the "
            "user's question with no follow-up needed. Default to unhelpful otherwise."
        ),
        HumanMessage(
            content=f"Question: {last_question.content}\n\nAnswer: {last_answer.content}\n\n"
            "Does this answer fully and accurately address the question?"
        ),
    ])

    return {
        "loop_count": state.get("loop_count", 0) + 1,
        "is_helpful": verdict.helpful,
    }

# Node: Node: prepare a retry 
def add_retry_note(state: HelpfulnessState) -> dict:
    return {
        "messages": [
            SystemMessage(
                content="That answer wasn't fully helpful. Please reconsider and give a more complete answer."
            )
        ]
    }

# Routing function to end - safe limit MAX_LOOPS
MAX_LOOPS = 3

def route_after_judge(state: HelpfulnessState) -> Literal["retry", "end"]:
    if state["is_helpful"]:
        return "end"
    if state["loop_count"] >= MAX_LOOPS:
        return "end"
    return "retry"

# Graph flow definition
workflow = StateGraph(HelpfulnessState)
workflow.add_node("agent", call_agent)
workflow.add_node("judge", judge_response)
workflow.add_node("retry", add_retry_note)

workflow.set_entry_point("agent")
workflow.add_edge("agent", "judge")
workflow.add_conditional_edges("judge", route_after_judge, {"retry": "retry", "end": END})
workflow.add_edge("retry", "agent")

graph = workflow.compile()



