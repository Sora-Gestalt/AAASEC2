# ============================================================
# DAY 2 LAB — SOLUTION: Multi-Agent Research Team in LangGraph
# ============================================================
# Day 1 you built a SINGLE AGENT: one workflow, function nodes,
# and a router YOU wrote (quality_router) deciding the flow.
#
# Day 2 you build a MULTI-AGENT SYSTEM: a team of specialized LLM
# agents coordinated by an LLM SUPERVISOR that decides — at
# runtime — who works next.
#
#   Day 1 (single agent)              Day 2 (multi-agent)
#   ─────────────────────             ─────────────────────────────
#   nodes = Python functions          nodes = LLM agents w/ personas
#   routing = your if/else            routing = supervisor LLM decides
#   one prompt for everything         one system prompt PER agent
#   tools available everywhere        tools SCOPED (only researcher
#                                       can search the web)
#   loop = quality-score retry        loop = critic sends draft back
#                                       to writer for revision
#
#              ┌──────────── supervisor ─────────────┐
#              │       (LLM decides who's next)      │
#     ┌────────┼───────────┬───────────┬─────────────┤
#     ↓        ↓           ↓           ↓             ↓
#  researcher  analyst    writer     critic       FINISH
#     │        │           │           │             ↓
#     └────────┴───────────┴───────────┘            END
#          (every worker reports back to the supervisor)
#
# Two run modes (same as Day 1):
#   USE_FAKE=1  → no API keys; deterministic fakes. The fake critic
#                 REJECTS the first draft so you SEE the revision
#                 loop: writer → critic → writer → critic → FINISH.
#   default     → real OpenRouter LLM + Tavily search (.env keys).
# ============================================================

import os
import operator
from datetime import datetime
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage

# STEP 0 — same building blocks as Day 1
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"

MAX_REVISIONS = 2      # cap on writer↔critic loops
MAX_TURNS = 12         # cap on total supervisor decisions


# ============================================================
# STEP 1 — SHARED STATE: the team's "blackboard"
# ============================================================
# Day 1's state was a data PIPELINE (each field filled once, in
# order). Day 2's state is a BLACKBOARD: every agent reads all of
# it and writes its own section; the supervisor reads it to decide
# who goes next. Same reducer trick for append-only fields.

class TeamState(TypedDict):
    task: str
    research_notes: Annotated[List[str], operator.add]   # researcher appends
    analysis: str                                        # analyst writes
    draft: str                                           # writer writes
    critique: str                                        # critic writes
    revision_count: int
    turn_count: int
    next_agent: str                                      # supervisor's decision
    execution_logs: Annotated[List[str], operator.add]


# ============================================================
# STEP 3 — STRUCTURED ROUTING DECISION (defined early for fakes)
# ============================================================
# Day 1: structured output produced a quality SCORE.
# Day 2: structured output produces a ROUTING DECISION — this is
# what turns an LLM into a supervisor.

class RouterDecision(BaseModel):
    """The supervisor's choice of who acts next."""
    next_agent: Literal["researcher", "analyst", "writer", "critic", "FINISH"]
    reason: str = Field(description="One sentence explaining the choice")


# ============================================================
# STEP 2 — ONE LLM, FOUR PERSONAS (+ tools scoped per agent)
# ============================================================
# A multi-agent "team" doesn't need four different models — it needs
# four different SYSTEM PROMPTS (and, in bigger systems, different
# tools/models per agent: cheap model for the critic, big model for
# the writer, etc.). Only the researcher gets the search tool.

PERSONAS = {
    "researcher": (
        "You are the team's RESEARCHER. You gather raw facts with the search "
        "tool. Output 3-5 terse factual bullet points with sources. You never "
        "analyze or editorialize — that's the analyst's job."
    ),
    "analyst": (
        "You are the team's ANALYST. You receive raw research notes and find "
        "the patterns: trends, tensions, implications. Output a tight analysis "
        "in 3-4 sentences. You never gather new facts and never write prose "
        "for the final report."
    ),
    "writer": (
        "You are the team's WRITER. You turn the analysis into a polished "
        "executive brief (~150 words): headline, 2-3 findings, 1 recommendation. "
        "If a critique is present, revise the draft to address every point."
    ),
    "critic": (
        "You are the team's CRITIC. Judge the draft harshly but fairly against "
        "the research notes. Reply with exactly 'APPROVED' if it is accurate, "
        "specific and complete; otherwise reply 'REVISE:' followed by concrete, "
        "actionable fixes."
    ),
}

if USE_FAKE:
    # ---------- deterministic fakes: run the whole team offline ----------
    class FakeWorker:
        """Canned per-persona outputs; critic rejects once, then approves."""

        def __init__(self):
            self.critic_calls = 0

        def invoke_persona(self, role, _messages):
            if role == "researcher":
                return ("- Fact A: enterprises adopt supervisor-pattern agent teams (src: example.com/a)\n"
                        "- Fact B: tool scoping reduces agent error rates (src: example.com/b)\n"
                        "- Fact C: revision loops improve output quality (src: example.com/c)")
            if role == "analyst":
                return ("The pattern across sources: coordination, not raw model power, drives "
                        "multi-agent value. Scoped tools and review loops are the recurring "
                        "levers; unstructured agent swarms underperform supervised teams.")
            if role == "writer":
                return ("HEADLINE: Supervised agent teams beat solo agents.\n"
                        "Findings: (1) supervisor routing enables specialization; (2) tool "
                        "scoping cuts errors; (3) critic loops raise quality.\n"
                        "Recommendation: pilot a supervisor-pattern team on one workflow.")
            if role == "critic":
                self.critic_calls += 1
                if self.critic_calls == 1:
                    return "REVISE: cite the sources from the research notes; quantify finding (2)."
                return "APPROVED"
            return ""

    fake_worker = FakeWorker()

    def run_persona(role, user_content):
        return fake_worker.invoke_persona(role, user_content)

    def supervisor_decide(state) -> RouterDecision:
        """Deterministic supervisor: same logic a real LLM should follow."""
        if not state["research_notes"]:
            return RouterDecision(next_agent="researcher", reason="No research yet.")
        if not state["analysis"]:
            return RouterDecision(next_agent="analyst", reason="Research done, needs analysis.")
        if not state["draft"]:
            return RouterDecision(next_agent="writer", reason="Analysis done, needs a draft.")
        if not state["critique"]:
            return RouterDecision(next_agent="critic", reason="Draft ready for review.")
        if state["critique"].startswith("REVISE") and state["revision_count"] < MAX_REVISIONS:
            return RouterDecision(next_agent="writer", reason="Critic requested changes.")
        return RouterDecision(next_agent="FINISH", reason="Draft approved (or revision cap hit).")

else:
    # ---------- real providers ----------
    from langchain_openai import ChatOpenAI
    from langchain_tavily import TavilySearch

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
    )
    search_tool = TavilySearch(max_results=4)
    supervisor_llm = llm.with_structured_output(RouterDecision)

    def run_persona(role, user_content):
        response = llm.invoke(
            [SystemMessage(content=PERSONAS[role]), HumanMessage(content=user_content)]
        )
        return response.content

    def supervisor_decide(state) -> RouterDecision:
        status = (
            f"Task: {state['task']}\n"
            f"Research notes: {'YES (' + str(len(state['research_notes'])) + ')' if state['research_notes'] else 'none'}\n"
            f"Analysis: {'YES' if state['analysis'] else 'none'}\n"
            f"Draft: {'YES' if state['draft'] else 'none'}\n"
            f"Critique: {state['critique'] or 'none'}\n"
            f"Revisions so far: {state['revision_count']} (max {MAX_REVISIONS})\n"
        )
        return supervisor_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You are the SUPERVISOR of a research team (researcher, analyst, "
                        "writer, critic). Given the team's progress, pick who acts next. "
                        "Standard order: researcher → analyst → writer → critic. If the "
                        "critique starts with REVISE and revisions < max, send the writer. "
                        "If the critique is APPROVED or revisions are maxed out, FINISH."
                    )
                ),
                HumanMessage(content=status),
            ]
        )


# ============================================================
# STEP 4 — THE SUPERVISOR NODE (the piece Day 1 didn't have)
# ============================================================
# Day 1's quality_router was YOUR code deciding the route.
# Here the LLM decides — but notice the GUARDRAILS around it:
# never trust an LLM to terminate a loop. Code enforces the caps,
# exactly like Day 1's iteration_count did.

def supervisor_node(state: TeamState):
    turn = state["turn_count"] + 1

    if turn > MAX_TURNS:  # guardrail 1: absolute turn cap
        decision = RouterDecision(next_agent="FINISH", reason="Turn cap reached.")
    else:
        decision = supervisor_decide(state)
        # guardrail 2: LLM may not restart the revision loop past the cap
        if (decision.next_agent in ("writer", "critic")
                and state["revision_count"] >= MAX_REVISIONS
                and state["draft"]):
            decision = RouterDecision(next_agent="FINISH", reason="Revision cap reached.")

    return {
        "next_agent": decision.next_agent,
        "turn_count": turn,
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] supervisor (turn {turn}): "
            f"→ {decision.next_agent} ({decision.reason})"
        ],
    }


# ============================================================
# STEP 5 — WORKER AGENT NODES
# ============================================================
# Each worker: read the blackboard → act in persona → write ONLY
# its own section (partial updates, same rule as Day 1).

def researcher_node(state: TeamState):
    if USE_FAKE:
        notes = run_persona("researcher", state["task"])
    else:
        results = search_tool.invoke({"query": state["task"]})["results"]
        raw = "\n".join(f"- {r.get('title','')}: {r.get('content','')[:300]} ({r.get('url','')})"
                        for r in results)
        notes = run_persona("researcher", f"Task: {state['task']}\n\nSearch results:\n{raw}")

    return {
        "research_notes": [notes],
        "execution_logs": [f"[{datetime.now():%H:%M:%S}] researcher: notes gathered"],
    }


def analyst_node(state: TeamState):
    notes = "\n\n".join(state["research_notes"])
    analysis = run_persona("analyst", f"Task: {state['task']}\n\nResearch notes:\n{notes}")
    return {
        "analysis": analysis,
        "execution_logs": [f"[{datetime.now():%H:%M:%S}] analyst: analysis written"],
    }


def writer_node(state: TeamState):
    revising = bool(state["critique"] and state["critique"].startswith("REVISE"))
    prompt = (
        f"Task: {state['task']}\n\nAnalysis:\n{state['analysis']}\n\n"
        f"Research notes:\n" + "\n\n".join(state["research_notes"])
    )
    if revising:
        prompt += f"\n\nPrevious draft:\n{state['draft']}\n\nCritique to address:\n{state['critique']}"

    draft = run_persona("writer", prompt)
    return {
        "draft": draft,
        "critique": "",  # reset so the critic reviews the NEW draft
        "revision_count": state["revision_count"] + (1 if revising else 0),
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] writer: "
            + ("revision " + str(state["revision_count"] + 1) if revising else "first draft")
        ],
    }


def critic_node(state: TeamState):
    critique = run_persona(
        "critic",
        f"Task: {state['task']}\n\nResearch notes:\n"
        + "\n\n".join(state["research_notes"])
        + f"\n\nDraft to review:\n{state['draft']}",
    )
    verdict = "APPROVED" if critique.strip().upper().startswith("APPROVED") else "REVISE"
    return {
        "critique": critique,
        "execution_logs": [f"[{datetime.now():%H:%M:%S}] critic: {verdict}"],
    }


# ============================================================
# STEP 6 — ROUTING FUNCTION + WIRE THE GRAPH
# ============================================================
# The conditional-edge FUNCTION is now trivial — it just reads the
# supervisor's decision from state. Compare with Day 1, where all
# the decision logic lived inside quality_router itself. The
# intelligence moved from the edge into a NODE.

def route_from_supervisor(state: TeamState) -> str:
    return state["next_agent"]


workflow = StateGraph(TeamState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)

workflow.add_edge(START, "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        "critic": "critic",
        "FINISH": END,
    },
)

# Every worker reports back to the supervisor — the hub-and-spoke
# shape that DEFINES the supervisor pattern.
for worker in ["researcher", "analyst", "writer", "critic"]:
    workflow.add_edge(worker, "supervisor")


# ============================================================
# STEP 7 — COMPILE, VISUALIZE, RUN
# ============================================================

if __name__ == "__main__":
    app = workflow.compile(checkpointer=InMemorySaver())

    print("=" * 60)
    print("GRAPH (paste into https://mermaid.live):")
    print("=" * 60)
    print(app.get_graph().draw_mermaid())

    initial_state = {
        "task": "Should our company adopt multi-agent AI systems in 2026?",
        "research_notes": [],
        "analysis": "",
        "draft": "",
        "critique": "",
        "revision_count": 0,
        "turn_count": 0,
        "next_agent": "",
        "execution_logs": [],
    }

    config = {"configurable": {"thread_id": "team-run-1"}}

    print("\n" + "=" * 60)
    print(f"RUN (USE_FAKE={USE_FAKE})")
    print("=" * 60)

    final_state = None
    for chunk in app.stream(initial_state, config, stream_mode="values"):
        final_state = chunk
        if chunk["execution_logs"]:
            print(chunk["execution_logs"][-1])

    print("\n" + "=" * 60)
    print("FINAL DRAFT")
    print("=" * 60)
    print(final_state["draft"])

    print("\n" + "=" * 60)
    print(f"STATS: turns={final_state['turn_count']} "
          f"revisions={final_state['revision_count']} "
          f"verdict={final_state['critique'][:40]}")
    print("=" * 60)
