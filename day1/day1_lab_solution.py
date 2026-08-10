# ============================================================
# DAY 1 LAB — SOLUTION: Enterprise Research Agent in LangGraph
# ============================================================
# This is the reference implementation of the skeleton
# (day1_lab_skeleton.py). Every step is marked so you can diff
# it against your own attempt.
#
#   START → collect → store_memory → analyze → evaluate
#              ↑                                  │
#              └── quality < 7 (max 3 tries) ─────┤
#                                                 └ quality >= 7
#                                                       ↓
#                                          report → audit → END
#
# Two run modes:
#   USE_FAKE=1  → no API keys needed; deterministic fakes for the
#                 LLM, the search tool, and the embeddings. The
#                 fake evaluator scores 5 on iteration 1 and 8
#                 afterwards, so you SEE the retry loop fire.
#   default     → real OpenRouter LLM + Tavily search (.env keys).
# ============================================================

import os
import operator
from datetime import datetime
from typing import Annotated, List, Dict
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage
from langchain_core.vectorstores import InMemoryVectorStore

# STEP 0 — graph building blocks
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"


# ============================================================
# STEP 1 — THE STATE
# ============================================================
# Note the reducer on execution_logs: nodes return {"execution_logs":
# ["one line"]} and LangGraph APPENDS via operator.add instead of
# overwriting. Every other key uses last-write-wins.

class AgentState(TypedDict):
    topic: str
    search_query: str
    collected_data: List[Dict]
    analyzed_data: List[Dict]
    quality_score: int
    iteration_count: int
    final_report: str
    execution_logs: Annotated[List[str], operator.add]


# ============================================================
# STEP 3 — STRUCTURED OUTPUT schema (defined early so fakes can use it)
# ============================================================

class QualityScore(BaseModel):
    """Evaluation of research quality."""
    score: int = Field(ge=1, le=10)
    reasoning: str = Field(description="One-sentence justification")


# ============================================================
# STEP 2 — MODEL, SEARCH TOOL, EMBEDDINGS
# ============================================================

if USE_FAKE:
    # ---------- deterministic fakes: run the graph offline ----------
    from langchain_core.embeddings import DeterministicFakeEmbedding

    class FakeLLM:
        """Just enough of the ChatModel surface for this lab."""

        def invoke(self, messages):
            class _Resp:
                content = (
                    "Key findings: multi-agent orchestration, state-graph "
                    "workflows, and guardrails dominate enterprise agentic "
                    "AI adoption in 2026."
                )
            return _Resp()

    class FakeEvaluator:
        """Scores low on the first pass so the retry loop fires."""

        def __init__(self):
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                return QualityScore(score=5, reasoning="Only one shallow pass over the sources.")
            return QualityScore(score=8, reasoning="Second pass added breadth and depth.")

    class FakeSearch:
        def invoke(self, payload):
            q = payload["query"]
            return {
                "results": [
                    {
                        "title": f"Fake source A for: {q}",
                        "url": "https://example.com/a",
                        "content": f"Deterministic content about {q} — trends, tooling, adoption.",
                    },
                    {
                        "title": f"Fake source B for: {q}",
                        "url": "https://example.com/b",
                        "content": f"Deterministic content about {q} — risks, governance, ROI.",
                    },
                ]
            }

    llm = FakeLLM()
    evaluator = FakeEvaluator()
    search_tool = FakeSearch()
    embeddings = DeterministicFakeEmbedding(size=256)

else:
    # ---------- real providers ----------
    from langchain_openai import ChatOpenAI
    from langchain_tavily import TavilySearch

    # OpenRouter is OpenAI-compatible: same ChatOpenAI class, different
    # base_url + model name. OPENAI_API_KEY in .env must be your
    # sk-or-... key. The ":free" suffix is REQUIRED to avoid billing.
    llm = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
    )

    # STEP 3 — the structured evaluator. Returns a QualityScore OBJECT,
    # not a string: result.score is already a validated int in [1, 10].
    evaluator = llm.with_structured_output(QualityScore)

    search_tool = TavilySearch(max_results=5)  # needs TAVILY_API_KEY

    # OpenRouter has no embeddings endpoint → local HF embeddings if
    # installed (uv sync --group embeddings), else deterministic fakes.
    # Embeddings only power the RAG bonus, not the core graph.
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except ImportError:
        from langchain_core.embeddings import DeterministicFakeEmbedding
        embeddings = DeterministicFakeEmbedding(size=256)

vector_store = InMemoryVectorStore(embeddings)


# ============================================================
# STEP 4 — NODES
# ============================================================
# Each node returns a PARTIAL update: only the keys it changed.
# LangGraph merges it into the state (execution_logs via its reducer).

def collect_node(state: AgentState):
    """Search the web. On retries, CHANGE the query — a loop that
    repeats the identical action can never produce a different result."""
    iteration = state["iteration_count"] + 1

    # A different angle per iteration (rule (a) of loop termination):
    angles = {
        1: f"{state['topic']} overview 2026",
        2: f"{state['topic']} case studies implementation challenges",
        3: f"{state['topic']} ROI metrics production deployments",
    }
    query = angles.get(iteration, f"{state['topic']} latest developments")

    results = search_tool.invoke({"query": query})["results"]

    sources = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in results
    ]

    return {
        "search_query": query,
        "collected_data": sources,
        "iteration_count": iteration,
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] collect (iter {iteration}): "
            f"'{query}' → {len(sources)} sources"
        ],
    }


def store_memory_node(state: AgentState):
    """Save source contents into the vector store (long-term memory)."""
    texts = [s["content"] for s in state["collected_data"] if s["content"]]
    if texts:
        vector_store.add_texts(texts)
    return {
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] store_memory: {len(texts)} chunks embedded"
        ]
    }


def analyze_node(state: AgentState):
    """LLM-analyze each source, enriched with related past research
    retrieved from the vector store — that retrieval step is the RAG."""
    analyzed = []
    for source in state["collected_data"]:
        related = vector_store.similarity_search(source["content"], k=2)
        related_context = "\n".join(d.page_content[:200] for d in related)

        prompt = (
            f"Topic: {state['topic']}\n\n"
            f"Source: {source['title']}\n{source['content']}\n\n"
            f"Related prior research:\n{related_context}\n\n"
            "Extract the 2-3 most important insights as concise bullet points."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        analyzed.append(
            {
                "title": source["title"],
                "url": source["url"],
                "insights": response.content,
            }
        )

    return {
        "analyzed_data": analyzed,
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] analyze: {len(analyzed)} sources analyzed"
        ],
    }


def evaluate_node(state: AgentState):
    """Score the research with the STRUCTURED evaluator. result is a
    QualityScore object — no fragile int() parsing of free text."""
    summary = "\n".join(a["insights"] for a in state["analyzed_data"])
    result = evaluator.invoke(
        [
            HumanMessage(
                content=(
                    f"Rate this research on '{state['topic']}' from 1-10 for "
                    f"depth, breadth, and usefulness to an enterprise reader.\n\n"
                    f"{summary}"
                )
            )
        ]
    )
    return {
        "quality_score": result.score,
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] evaluate: score={result.score} "
            f"({result.reasoning})"
        ],
    }


def report_node(state: AgentState):
    """Generate the enterprise report from analyzed_data."""
    insights = "\n\n".join(
        f"### {a['title']}\nSource: {a['url']}\n{a['insights']}"
        for a in state["analyzed_data"]
    )
    response = llm.invoke(
        [
            HumanMessage(
                content=(
                    f"Write a concise enterprise research report on "
                    f"'{state['topic']}' with an executive summary, key "
                    f"findings, and recommendations, based on:\n\n{insights}"
                )
            )
        ]
    )
    return {
        "final_report": response.content,
        "execution_logs": [f"[{datetime.now():%H:%M:%S}] report: generated"],
    }


def audit_node(state: AgentState):
    """Log completion stats — the compliance trail."""
    return {
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] audit: done | "
            f"iterations={state['iteration_count']} | "
            f"final_score={state['quality_score']} | "
            f"sources={len(state['collected_data'])}"
        ]
    }


# ============================================================
# STEP 5 — THE CONDITIONAL EDGE
# ============================================================
# BOTH termination rules:
#   a) collect_node changes the query each iteration
#   b) hard cap at 3 iterations
# Remove (b) and force low scores → GraphRecursionError at limit 25.

def quality_router(state: AgentState) -> str:
    if state["quality_score"] >= 7:
        return "report"
    if state["iteration_count"] >= 3:
        return "report"  # give up gracefully, ship what we have
    return "collect"


# ============================================================
# STEP 6 — WIRE THE GRAPH
# ============================================================

workflow = StateGraph(AgentState)

workflow.add_node("collect", collect_node)
workflow.add_node("store_memory", store_memory_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("report", report_node)
workflow.add_node("audit", audit_node)

workflow.add_edge(START, "collect")
workflow.add_edge("collect", "store_memory")
workflow.add_edge("store_memory", "analyze")
workflow.add_edge("analyze", "evaluate")

# The dict maps router RETURN VALUES to NODE NAMES.
workflow.add_conditional_edges(
    "evaluate",
    quality_router,
    {"collect": "collect", "report": "report"},
)

workflow.add_edge("report", "audit")
workflow.add_edge("audit", END)


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
        "topic": "Enterprise Agentic AI Systems",
        "search_query": "",
        "collected_data": [],
        "analyzed_data": [],
        "quality_score": 0,
        "iteration_count": 0,
        "final_report": "",
        "execution_logs": [],
    }

    config = {"configurable": {"thread_id": "run-1"}}  # required by checkpointer

    print("\n" + "=" * 60)
    print(f"RUN (USE_FAKE={USE_FAKE})")
    print("=" * 60)

    final_state = None
    for chunk in app.stream(initial_state, config, stream_mode="values"):
        final_state = chunk
        if chunk["execution_logs"]:
            print(chunk["execution_logs"][-1])

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(final_state["final_report"])

    print("\n" + "=" * 60)
    print("FULL EXECUTION LOG")
    print("=" * 60)
    for line in final_state["execution_logs"]:
        print(line)
