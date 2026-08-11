# ============================================================
# DAY 2 LAB — SKELETON: Build a Multi-Agent Research Team
# ============================================================
# Fill in every TODO. Don't open the solution (day2_lab_solution.py)
# until you pass the self-check at the bottom.
#
# WHAT CHANGES FROM DAY 1 — read this table twice:
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
# What does NOT change: State + Nodes + Edges. A multi-agent system
# is STILL just a StateGraph. If you can build Day 1, you can build
# this — the new ideas are personas, the supervisor, and guardrails.
#
# The system you're building (the SUPERVISOR pattern):
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
# Recommended reading BEFORE you start (~25 min):
#   1. Multi-agent concepts (architectures, supervisor pattern):
#      https://docs.langchain.com/oss/python/langgraph/multi-agent
#   2. Refresh: conditional branching + loops (you need both again):
#      https://docs.langchain.com/oss/python/langgraph/use-graph-api#conditional-branching
#   3. Structured output (the supervisor's decision is structured!):
#      https://docs.langchain.com/oss/python/langchain/structured-output
#
# Setup: same as Day 1 — `uv sync`, keys in .env, or USE_FAKE=1.
# ============================================================

import os
import operator
from datetime import datetime
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

MAX_REVISIONS = 2      # cap on writer↔critic loops
MAX_TURNS = 12         # cap on total supervisor decisions


# ============================================================
# STEP 1 — SHARED STATE: the team's "blackboard"
# ============================================================
# Day 1's state was a data PIPELINE (each field filled once, in
# order). Day 2's state is a BLACKBOARD: every agent reads all of
# it and writes only its own section; the supervisor reads it to
# decide who goes next.
#
# Define a TypedDict with:
#   task (str)
#   research_notes  <- List[str], APPEND-ONLY (which reducer? Day 1!)
#   analysis (str), draft (str), critique (str)
#   revision_count (int), turn_count (int)
#   next_agent (str)   <- the supervisor writes its decision HERE
#   execution_logs     <- append-only, same as Day 1
#
# ASK YOURSELF: why must research_notes append but draft overwrite?
# What would happen to the revision loop if draft used operator.add?

class TeamState(TypedDict):
    task: str
    research_notes: Annotated[List[str], operator.add]
    analysis: str
    draft: str
    critique: str
    revision_count: int
    turn_count: int
    next_agent: str
    execution_logs: Annotated[List[str], operator.add]


# ============================================================
# STEP 2 — STRUCTURED ROUTING DECISION
# ============================================================
# Day 1: structured output produced a quality SCORE.
# Day 2: structured output produces a ROUTING DECISION — this is
# the trick that turns an LLM into a supervisor. Literal[...] means
# the model CANNOT invent an agent that doesn't exist.
#
# WHERE TO LOOK: structured-output docs (same page as Day 1).

class RouterDecision(BaseModel):
    """The supervisor's choice of who acts next."""
    next_agent: Literal["researcher", "analyst", "writer", "critic", "FINISH"]
    reason: str = Field(description="One sentence explaining the choice")


# ============================================================
# STEP 3 — ONE LLM, FOUR PERSONAS (+ tools scoped per agent)
# ============================================================
# A multi-agent "team" doesn't need four models — it needs four
# SYSTEM PROMPTS. (In production you might also vary the model per
# agent: cheap model for the critic, big one for the writer.)
#
# TODO:
# 1. Write a PERSONAS dict: role -> system prompt, for
#    "researcher", "analyst", "writer", "critic".
#    Each persona must say what the agent DOES and what it MUST NOT
#    do (e.g. the researcher never analyzes). Boundaries between
#    agents live in the prompts — write them sharp.
# 2. Create llm (ChatOpenAI + OpenRouter, exactly like Day 1) and
#    search_tool (TavilySearch(max_results=4)).
# 3. supervisor_llm = llm.with_structured_output(RouterDecision)
# 4. Helper: run_persona(role, user_content) → invoke llm with
#    [SystemMessage(PERSONAS[role]), HumanMessage(user_content)]
#    and return response.content.
#
# TOOL SCOPING: only the researcher node may call search_tool.
# That's a deliberate design decision, not a limitation — ask
# yourself what could go wrong if the critic could search.

PERSONAS = {
    "researcher": (
        "You are an expert researcher. Your sole responsibility is to search for factual, "
        "up-to-date, and relevant raw information concerning the user's task. Summarize facts "
        "concisely into raw notes. You MUST NOT offer strategic insights, write final drafts, or criticize."
    ),
    "analyst": (
        "You are a strategic business analyst. Your job is to take raw research notes and analyze "
        "key trends, trade-offs, advantages, and risks. You MUST NOT perform web searches, write "
        "polished final reports, or review drafts."
    ),
    "writer": (
        "You are a professional technical writer. Your task is to draft comprehensive, cohesive, "
        "and polished reports based on research notes and strategic analysis. If feedback/critique "
        "is provided, address every critique point directly in your revision. You MUST NOT perform web searches."
    ),
    "critic": (
        "You are a strict editorial critic. Your sole task is to review draft reports against provided "
        "research notes and analysis. If the draft is complete and accurate, respond with 'APPROVED'. "
        "If improvements are needed, start your response strictly with 'REVISE:' followed by clear, actionable feedback. "
        "You MUST NOT draft new sections or perform web searches."
    ),
}

llm = ChatOpenAI(
       model="nvidia/nemotron-3-super-120b-a12b:free",
      temperature=0,
      base_url="https://openrouter.ai/api/v1",
)

search_tool = TavilySearch(max_results=4)
supervisor_llm = llm.with_structured_output(RouterDecision)


def run_persona(role: str, user_content: str) -> str:
    messages = [
        SystemMessage(content=PERSONAS[role]),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    return str(response.content)


# ============================================================
# STEP 4 — THE SUPERVISOR NODE (the piece Day 1 didn't have)
# ============================================================
# The supervisor node must:
# 1. Increment turn_count.
# 2. Build a STATUS SUMMARY of the blackboard (which sections are
#    filled? what does the critique say? how many revisions?).
#    Don't dump the full text of everything — the supervisor needs
#    STATUS, not content. (Why? Think tokens and attention.)
# 3. Ask supervisor_llm for a RouterDecision.
# 4. GUARDRAILS — never trust an LLM to terminate a loop:
#      a) if turn_count > MAX_TURNS → force FINISH
#      b) if the LLM picks writer/critic but revision_count >=
#         MAX_REVISIONS and a draft exists → force FINISH
#    This is Day 1's iteration cap wearing a new hat. Same lesson:
#    the LLM proposes, YOUR CODE disposes.
# 5. Return {"next_agent": ..., "turn_count": ..., "execution_logs": [...]}
#
# WHERE TO LOOK: multi-agent docs → "Supervisor" section.

def supervisor_node(state: TeamState):
    current_turn = state.get("turn_count", 0) + 1

    has_research = len(state.get("research_notes", [])) > 0
    has_analysis = bool(state.get("analysis", ""))
    has_draft = bool(state.get("draft", ""))
    has_critique = bool(state.get("critique", ""))
    critique_text = state.get("critique", "")
    revisions = state.get("revision_count", 0)

    status_summary = (
        f"Task: {state['task']}\n"
        f"Research Notes Present: {has_research} ({len(state.get('research_notes', []))} entries)\n"
        f"Analysis Present: {has_analysis}\n"
        f"Draft Present: {has_draft}\n"
        f"Critique Present: {has_critique} (Content: {critique_text if has_critique else 'None'})\n"
        f"Revision Count: {revisions}/{MAX_REVISIONS}\n"
        f"Current Turn Count: {current_turn}/{MAX_TURNS}\n\n"
        "Determine the next agent to route to. Workflow order is typically: "
        "researcher -> analyst -> writer -> critic -> (writer if REVISE, else FINISH). "
        "Choose FINISH if work is fully complete or approved."
    )

    prompt = [
        SystemMessage(content="You are the supervisor coordinating a multi-agent team. Select the next single best agent to execute task standard workflow."),
        HumanMessage(content=status_summary)
    ]

    decision = supervisor_llm.invoke(prompt)
    next_agent = decision.next_agent

    if current_turn > MAX_TURNS:
        next_agent = "FINISH"
    elif next_agent in ["writer", "critic"] and revisions >= MAX_REVISIONS and has_draft:
        next_agent = "FINISH"

    log_msg = f"[{datetime.now().isoformat()}] Supervisor selected '{next_agent}'. Reason: {decision.reason}"
    return {
        "next_agent": next_agent,
        "turn_count": current_turn,
        "execution_logs": [log_msg],
    }


# ============================================================
# STEP 5 — WORKER AGENT NODES
# ============================================================
# Each worker: read the blackboard → act in persona → return a
# PARTIAL update with ONLY its own section (Day 1 rule, unchanged).

def researcher_node(state: TeamState):
    """Search the web (ONLY this agent may), condense to notes."""
    try:
        results = search_tool.invoke({"query": state["task"]})
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        raw_text = "\n\n".join([f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}" for r in results])
    except Exception as e:
        raw_text = f"Search failed or unavailable: {str(e)}"

    notes = run_persona("researcher", f"Task: {state['task']}\n\nSearch Results:\n{raw_text}")
    log = f"[{datetime.now().isoformat()}] Researcher generated notes."
    return {
        "research_notes": [notes],
        "execution_logs": [log]
    }


def analyst_node(state: TeamState):
    """Turn raw notes into analysis."""
    notes_str = "\n---\n".join(state.get("research_notes", []))
    prompt = f"Task: {state['task']}\n\nResearch Notes:\n{notes_str}"
    analysis = run_persona("analyst", prompt)
    log = f"[{datetime.now().isoformat()}] Analyst generated strategic evaluation."
    return {
        "analysis": analysis,
        "execution_logs": [log]
    }


def writer_node(state: TeamState):
    """Write the draft — or REVISE it if a critique is present."""
    critique = state.get("critique", "")
    revising = bool(critique and critique.startswith("REVISE"))

    notes_str = "\n---\n".join(state.get("research_notes", []))
    analysis_str = state.get("analysis", "")
    current_draft = state.get("draft", "")

    if revising:
        prompt = (
            f"Task: {state['task']}\n\n"
            f"Research Notes:\n{notes_str}\n\n"
            f"Analysis:\n{analysis_str}\n\n"
            f"Previous Draft:\n{current_draft}\n\n"
            f"Critique to Fix:\n{critique}\n\n"
            "Please revise the draft to address the critique completely."
        )
    else:
        prompt = (
            f"Task: {state['task']}\n\n"
            f"Research Notes:\n{notes_str}\n\n"
            f"Analysis:\n{analysis_str}\n\n"
            "Please write the initial draft based on the research and analysis."
        )

    draft = run_persona("writer", prompt)
    rev_count = state.get("revision_count", 0) + (1 if revising else 0)
    log = f"[{datetime.now().isoformat()}] Writer {'revised' if revising else 'created'} the draft."

    return {
        "draft": draft,
        "critique": "",
        "revision_count": rev_count,
        "execution_logs": [log]
    }


def critic_node(state: TeamState):
    """Review the draft against the research notes."""
    notes_str = "\n---\n".join(state.get("research_notes", []))
    prompt = (
        f"Task: {state['task']}\n\n"
        f"Research Notes:\n{notes_str}\n\n"
        f"Analysis:\n{state.get('analysis', '')}\n\n"
        f"Current Draft:\n{state.get('draft', '')}\n\n"
        "Review the draft. Respond with 'APPROVED' or 'REVISE: <detailed suggestions>'."
    )
    critique = run_persona("critic", prompt)
    log = f"[{datetime.now().isoformat()}] Critic completed review."
    return {
        "critique": critique,
        "execution_logs": [log]
    }


# ============================================================
# STEP 6 — ROUTING FUNCTION + WIRE THE GRAPH
# ============================================================
# The conditional-edge function is now TRIVIAL — it just reads the
# supervisor's decision:
#
#     def route_from_supervisor(state) -> str:
#         return state["next_agent"]
#
# Compare with Day 1, where all decision logic lived inside
# quality_router. The intelligence MOVED from the edge into a node.
#
# Wiring checklist:
# 1. add all five nodes
# 2. START → supervisor
# 3. add_conditional_edges("supervisor", route_from_supervisor,
#        {"researcher": "researcher", "analyst": "analyst",
#         "writer": "writer", "critic": "critic", "FINISH": END})
# 4. EVERY worker gets an edge BACK to supervisor — the
#    hub-and-spoke shape that defines the supervisor pattern.
#    (A for-loop over the four worker names is idiomatic.)

def route_from_supervisor(state: TeamState) -> str:
    return state["next_agent"]


builder = StateGraph(TeamState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", researcher_node)
builder.add_node("analyst", analyst_node)
builder.add_node("writer", writer_node)
builder.add_node("critic", critic_node)

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        "critic": "critic",
        "FINISH": END,
    }
)

workers = ["researcher", "analyst", "writer", "critic"]
for worker in workers:
    builder.add_edge(worker, "supervisor")


# ============================================================
# STEP 7 — COMPILE, VISUALIZE, RUN
# ============================================================
# Same as Day 1: compile with InMemorySaver, print the Mermaid
# diagram (it should look like a STAR, not Day 1's chain), stream
# with stream_mode="values" and a thread_id, print the final draft.
#
# EXPERIMENT 1: set MAX_REVISIONS = 0. What happens to quality?
# EXPERIMENT 2: delete guardrail (a) and make the critic always
#   say REVISE. Watch the turn cap save you — then delete guardrail
#   (b) too and meet your old friend GraphRecursionError.
# EXPERIMENT 3: swap the analyst's persona for a terrible one
#   ("you are vague and generic"). How far does the damage spread
#   through the team? This is why persona boundaries matter.

if __name__ == "__main__":
    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)

    try:
        print(graph.get_graph().draw_mermaid())
    except Exception:
        pass

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

    config = {"configurable": {"thread_id": "day2_test_run"}}

    for event in graph.stream(initial_state, config=config, stream_mode="values"):
        agent = event.get("next_agent", "start")
        turns = event.get("turn_count", 0)
        print(f"\n--- Turn {turns} | State update triggered by: {agent} ---")
        if event.get("execution_logs"):
            print(f"Latest Log: {event['execution_logs'][-1]}")

    final_state = graph.get_state(config).values
    print("\n================ FINAL DRAFT ================")
    print(final_state.get("draft", "No draft produced."))
    print("=============================================")
    print(f"Total turns: {final_state.get('turn_count')}")
    print(f"Total revisions: {final_state.get('revision_count')}")


# ============================================================
# SELF-CHECK before you look at the solution
# ============================================================
# [ ] I can explain the supervisor pattern in one sentence
# [ ] My routing function reads state — the DECISION was made in a node
# [ ] research_notes appends; draft overwrites; I know why each
# [ ] The writer RESETS critique — I can explain what breaks if not
#     (hint: what does the supervisor see on the turn after a revision?)
# [ ] Only researcher_node touches search_tool
# [ ] My supervisor has BOTH guardrails, and I triggered EXPERIMENT 2
# [ ] My Mermaid diagram is a star: supervisor in the middle
# [ ] I can name one task where Day 1's single agent is the BETTER
#     design (multi-agent is not free: more calls, more latency,
#     more places to break — coordination must earn its cost)
#
# Stuck? Debugging order that works:
#   1. stream_mode="updates" — watch each supervisor decision + reason
#   2. print the status summary your supervisor_node builds — is the
#      LLM seeing an accurate picture of the blackboard?
#   3. check your conditional-edge dict covers ALL five decisions
#   4. only THEN open day2_lab_solution.py
# ============================================================