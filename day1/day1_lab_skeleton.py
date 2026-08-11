# ============================================================
# DAY 1 LAB — SKELETON: Build the Research Agent Yourself
# ============================================================
# Fill in every TODO. Each step tells you exactly WHERE in the
# LangGraph docs to look. Don't copy from the solution file
# (day1_lab_solution.py) until you've tried each step —
# the point of Day 1 is learning to THINK in state graphs.
#
# The system you're building:
#
#   START → collect → store_memory → analyze → evaluate
#              ↑                                  │
#              └── quality < 7 (max 3 tries) ─────┤
#                                                 └ quality >= 7
#                                                       ↓
#                                          report → audit → END
#
# Recommended reading order BEFORE you start (30 min total):
#   1. "Thinking in LangGraph" (the mental model):
#      https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
#   2. Graph API concepts (State, Nodes, Edges):
#      https://docs.langchain.com/oss/python/langgraph/graph-api
#   3. Using the Graph API (code patterns you'll copy):
#      https://docs.langchain.com/oss/python/langgraph/use-graph-api
#
# API reference (exact signatures when docs aren't enough):
#   https://reference.langchain.com/python/langgraph/
#
# Setup: `uv sync`, then create .env (or set USE_FAKE=1 — see README.md).
# ============================================================

import os
import operator
from datetime import datetime
from typing import Annotated, List, Dict
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import InMemorySaver
# TODO STEP 0 — import the graph building blocks from langgraph.
# You need: StateGraph, START, END from langgraph.graph
#           InMemorySaver from langgraph.checkpoint.memory
# WHERE TO LOOK: "Graph API" docs, first code example on the page.
# from langgraph.graph import ...
# from langgraph.checkpoint.memory import ...

load_dotenv()


# ============================================================
# STEP 1 — THE STATE  (the "digital clipboard" from the slides)
# ============================================================
# Define a TypedDict with everything the workflow needs to remember:
#   topic (str), search_query (str), collected_data (List[Dict]),
#   analyzed_data (List[Dict]), quality_score (int),
#   iteration_count (int), final_report (str), execution_logs
#
# KEY IDEA: execution_logs should use a REDUCER so every node can
# APPEND log lines instead of overwriting the list:
#     execution_logs: Annotated[List[str], operator.add]
#
# WHERE TO LOOK: Graph API docs → "State" section → "Reducers".
#   https://docs.langchain.com/oss/python/langgraph/graph-api
# ASK YOURSELF: what happens to a plain (non-reducer) key when two
# nodes write it? What happens with operator.add?

class AgentState(TypedDict):
    topic: str
    # TODO: add the remaining 6 keys (one uses Annotated + operator.add)
    search_query:str
    collected_data:List[Dict]
    analyzed_data:List[Dict]
    quality_score:int
    iteration_count:int
    final_report:str
    execution_logs: Annotated[List[str],operator.add]


# ============================================================
# STEP 2 — MODEL, SEARCH TOOL, EMBEDDINGS
# ============================================================
# Create:
#   llm          = ChatOpenAI(model="gpt-4o-mini", temperature=0)
#   search_tool  = TavilySearch(max_results=5)   # langchain_tavily!
#   vector_store = a Chroma or InMemoryVectorStore with embeddings
#
# ------------------------------------------------------------
# USING OPENROUTER (free models — recommended for this course)
# ------------------------------------------------------------
# OpenRouter is OpenAI-compatible, so ChatOpenAI works as-is —
# you only change the key, the base_url, and the model name.
#
# 1. Get a key at https://openrouter.ai/keys  (starts with sk-or-)
# 2. Put in your .env:
#        OPENAI_API_KEY=sk-or-...
# 3. Create the model like this:
#
#    llm = ChatOpenAI(
#        model="nvidia/nemotron-3-super-120b-a12b:free",
#        temperature=0,
#        base_url="https://openrouter.ai/api/v1",
#    )
#
# Free NVIDIA Nemotron models (the ":free" suffix is REQUIRED —
# without it you'll be billed):
#   nvidia/nemotron-3-super-120b-a12b:free   <- use this one
#   nvidia/nemotron-3-nano-30b-a3b:free      <- fallback if rate-limited
#   nvidia/nemotron-3-ultra-550b-a55b:free   <- biggest, often congested
#   deepseek/deepseek-v4-flash-0731:free     <- try it, could work
# Full list: https://openrouter.ai/collections/free-models
#
# KNOW THE LIMITS: free models are rate-limited (~20 req/min and a
# small daily cap). This lab makes ~5-10 LLM calls per run, so you
# have plenty — but don't run it in a tight loop, and if you get
# HTTP 429, wait a minute or switch to the nano model.
#
# CAVEAT for Step 3: with_structured_output() needs tool/function
# calling. Nemotron supports it, but if a free model ever returns
# an error there, either (a) try another :free model, or (b) pass
# method="json_schema" to with_structured_output.
#
# NOTE: OpenRouter has NO embeddings endpoint. For the vector store
# use InMemoryVectorStore + local HuggingFaceEmbeddings
# (uv sync --group embeddings), or DeterministicFakeEmbedding —
# embeddings only power the memory-retrieval bonus, not the core graph.
# ------------------------------------------------------------
#
# GOTCHA: the old imports you'll find in 2023-24 tutorials
# (langchain.vectorstores, langchain_community.tools.tavily_search)
# are DEAD. Current homes:
#   - TavilySearch:      https://docs.langchain.com/oss/python/integrations/providers/tavily
#   - Chat models:       https://docs.langchain.com/oss/python/langchain/models
#   - InMemoryVectorStore: langchain_core.vectorstores
#
# NOTE: TavilySearch.invoke({"query": q}) returns a DICT — the
# actual sources are under the "results" key. print() it once to see.

# TODO: your code here


from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.embeddings import DeterministicFakeEmbedding

llm = ChatOpenAI(
       model="nvidia/nemotron-3-super-120b-a12b:free",
      temperature=0,
      base_url="https://openrouter.ai/api/v1",
)

search_tool = TavilySearch(max_results=5)

embeddings = DeterministicFakeEmbedding(size=384)

vector_store = InMemoryVectorStore(embedding=embeddings)


# ============================================================
# STEP 3 — STRUCTURED OUTPUT for the quality score
# ============================================================
# Never parse int(response.content) out of free text. Define a
# Pydantic schema and use llm.with_structured_output(...) so the
# model is FORCED to return valid data.
#
# WHERE TO LOOK: https://docs.langchain.com/oss/python/langchain/structured-output
# ASK YOURSELF: what does with_structured_output return — a string,
# a dict, or a QualityScore object?

class QualityScore(BaseModel):
    """Evaluation of research quality."""
    score: int = Field(ge=1, le=10)
    reasoning: str = Field(description="One-sentence justification")

# TODO: evaluator = llm.with_structured_output(QualityScore)

evaluator = llm.with_structured_output(QualityScore)


# ============================================================
# STEP 4 — NODES
# ============================================================
# A node is just a function: takes state, returns a PARTIAL update
# (a dict with ONLY the keys it changed). LangGraph merges it in.
# Do NOT mutate state in place; do NOT return the whole state.
#
# WHERE TO LOOK: Use Graph API docs → "Define and update state".
#   https://docs.langchain.com/oss/python/langgraph/use-graph-api

def collect_node(state: AgentState):
    """Search the web. On retries, CHANGE the query!"""
    # TODO:
    # 1. iteration = state["iteration_count"] + 1
    # 2. Build a query that DIFFERS per iteration (why? see Step 5)
    # 3. results = search_tool.invoke({"query": query})["results"]
    # 4. return {"search_query": ..., "collected_data": ...,
    #            "iteration_count": ..., "execution_logs": [...]}

    iteration = state["iteration_count"] + 1
    topic = state["topic"]
    
    if iteration == 1:
        query = f"overview and key principles of {topic}"
    elif iteration == 2:
        query = f"advanced application and architecture of {topic}"
    else:
        query = f"challenges and enterprise case studies for {topic}"
    results = search_tool.invoke({"query":query})["results"]
    return {"search_query":query,"collected_data":results,"iteration_count":iteration
            ,"execution_logs":[f"Iteration {iteration}: Searched for '{query}'"]}


def store_memory_node(state: AgentState):
    """Save source contents into the vector store."""
    # TODO: vector_store.add_texts([...contents...])
    collected_data = state.get("collected_data",[])
    texts = [item["content"] for item in collected_data if "content" in item]

    if texts:
        vector_store.add_texts(texts=texts)
    
    log_message = f"[store_memory_node] Stored {len(texts)} document chunks in vector store."
    return {"execution_logs":[log_message]}

def analyze_node(state: AgentState):
    """LLM-analyze each source. Bonus: retrieve related past
    research with vector_store.similarity_search(content, k=2)
    and include it in the prompt — that's what makes this RAG."""
    # TODO
    collected_data = state.get("collected_data",[])
    topic = state.get("topic","")
    analyzed_results = []
    
    for item in collected_data:
        content = item.get("content","")
        title = item.get("title","untitled")
        retrieved_docs = vector_store.similarity_search(content,k=2)
        past_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
        
        prompt = f"""You are a helpful AI assistant analyzing research data for the topic: '{topic}'.
            Newly Collected Data:
            Title: {title}
            Content: {content}

            Retrieved Past Memory (RAG Context):
            {past_context if past_context else "No prior context."}

            Task: Extract key insights, facts, and technical details from this data."""
        
        response = llm.invoke([HumanMessage(content=prompt)])

        analyzed_results.append({
            "title":title,
            "analysis":response.content
        })
        
    return {
        "analyzed_data":analyzed_results,
        "execution_logs":[f"[analyzed_node] Analyzed {len(analyzed_results)} items."]
    }

def evaluate_node(state: AgentState):
    """Score the research with the STRUCTURED evaluator (Step 3)."""
    # TODO: return {"quality_score": result.score, "execution_logs": [...]}
    analyzed_data = state.get("analyzed_data",[])
    topic = state.get("topic","")
    
    formatted_analysis = "\n\n".join(
        [f"source: {item.get('title','untitled')}\nAnalysis: {item.get('analysis','')}" for item in analyzed_data]
    )
    
    prompt = f"""
        You are a helpful quality researcher AI assistant evaluator
        Topic: {topic}
        
        Research Collected & Analyzed:
        {formatted_analysis if formatted_analysis else "no data analyzed yet."}
        
        Task: Assess whether this research provides sufficient depth, technical detail, and actionable insights on the topic.
        Assign a score from 1 (unusable) to 10 (exceptionally thorough and complete) and provide a concise reason.
    """
    
    eval_result:QualityScore = evaluator.invoke([HumanMessage(content=prompt)])
    
    log_message = f"[evaluate_node] Quality Score: {eval_result.score}/10. Reason: {eval_result.reasoning}"
    
    return {
        "quality_score":eval_result.score,
        "execution_logs":[log_message]
    }


def report_node(state: AgentState):
    """Generate the enterprise report from analyzed_data."""
    analyzed_data = state.get("analyzed_data", [])
    topic = state.get("topic", "")
    

    sources_summary = "\n\n".join(
        [f"Source: {item.get('title')}\n{item.get('analysis')}" for item in analyzed_data]
    )
    
    prompt = f"""You are a principal technical analyst writing a final enterprise report.
        Topic: {topic}

        Analyzed Findings:
        {sources_summary}

        Task: Synthesize the findings above into a structured, executive-ready enterprise report.
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "final_report": response.content,
        "execution_logs": ["[report_node] Generated final enterprise report."]
    }
    


def audit_node(state: AgentState):
    """Log completion stats."""
    # TODO
    logs = state.get("execution_logs",[])
    quality_score = state.get("quality_score",0)
    iterations = state.get("iteration_count",0)
    
    audit_summary = (
        f"[audit_node] Workflow completed in {iterations} iteration(s) "
        f"with final quality score {quality_score}/10."
        f"Total log entries: {len(logs)}"
    )

    return {"execution_logs":[audit_summary]}

# ============================================================
# STEP 5 — THE CONDITIONAL EDGE (the heart of this lab)
# ============================================================
# Write a router function: takes state, RETURNS THE NAME of the
# next node as a string.
#
# CRITICAL — loops must terminate. Two rules:
#   a) every retry must change something (your query, Step 4.2),
#   b) hard-cap the retries with iteration_count.
# Without both, same search → same score → infinite loop → LangGraph
# kills the run at recursion limit 25 with GraphRecursionError.
#
# WHERE TO LOOK (read BOTH):
#   - "Conditional branching":
#     https://docs.langchain.com/oss/python/langgraph/use-graph-api#conditional-branching
#   - "Create and control loops":
#     https://docs.langchain.com/oss/python/langgraph/use-graph-api#create-and-control-loops
#
# EXPERIMENT: comment out the iteration cap, force low scores, run,
# and read the GraphRecursionError message. Now you understand why
# the docs insist on termination conditions.

def quality_router(state: AgentState) -> str:
    # TODO: return "report" or "collect"
    quality_score = state.get("quality_score",0)
    iteration_count = state.get("iteration_count",0)
    
    if quality_score >= 7 or iteration_count >= 3:
        return "report"
    return "collect"


# ============================================================
# STEP 6 — WIRE THE GRAPH
# ============================================================
# 1. workflow = StateGraph(AgentState)
# 2. add_node(...) for all six nodes
# 3. add_edge(START, "collect")        <- START, not set_entry_point
# 4. linear edges: collect → store_memory → analyze → evaluate
# 5. add_conditional_edges("evaluate", quality_router,
#        {"collect": "collect", "report": "report"})
#    (the dict maps router RETURN VALUES to NODE NAMES)
# 6. report → audit → END
#
# WHERE TO LOOK: Graph API docs → "Edges".

# TODO: your code here

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

workflow.add_conditional_edges(
    "evaluate", 
    quality_router, 
    {
        "collect": "collect", 
        "report": "report"
    }
)

workflow.add_edge("report", "audit")
workflow.add_edge("audit", END)

# ============================================================
# STEP 7 — COMPILE with a checkpointer, VISUALIZE, RUN
# ============================================================
# 1. app = workflow.compile(checkpointer=InMemorySaver())
#    A checkpointer saves state after every node → enables resume,
#    time-travel debugging, and human-in-the-loop.
#    WHERE TO LOOK: https://docs.langchain.com/oss/python/langgraph/persistence
#
# 2. Visualize what you built:
#       print(app.get_graph().draw_mermaid())
#    → paste the output into https://mermaid.live
#    Does the picture match the diagram at the top of this file?
#
# 3. Run with STREAMING so you watch state evolve node by node:
#       config = {"configurable": {"thread_id": "run-1"}}  # required
#       for chunk in app.stream(initial_state, config,
#                               stream_mode="values"):
#           ...
#    WHERE TO LOOK: https://docs.langchain.com/oss/python/langgraph/streaming
#
# 4. BONUS — human-in-the-loop: compile with
#       interrupt_before=["report"]
#    then inspect state and resume. WHERE TO LOOK:
#       https://docs.langchain.com/oss/python/langgraph/interrupts


checkpointer = InMemorySaver()


app = workflow.compile(checkpointer=checkpointer)


print("=== MERMAID GRAPH DIAGRAM ===")
print(app.get_graph().draw_mermaid())
print("=============================\n")

if __name__ == "__main__":
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
    # TODO: compile, visualize, stream, print final report + logs
    config = {"configurable": {"thread_id": "research-run-1"}}

    print("--- STARTING STREAMING EXECUTION ---")
    
    for state_snapshot in app.stream(initial_state, config=config, stream_mode="values"):
        current_logs = state_snapshot.get("execution_logs", [])
        if current_logs:
            # Print the most recent log line added to the state
            print(f"> {current_logs[-1]}")

    print("\n--- WORKFLOW COMPLETE ---")

    # Fetch final state snapshot from the checkpointer thread
    final_snapshot = app.get_state(config)
    
    print("\n=== FINAL REPORT ===")
    print(final_snapshot.values.get("final_report", "No report generated."))
    
    print("\n=== COMPLETE EXECUTION LOGS ===")
    for log in final_snapshot.values.get("execution_logs", []):
        print(f" - {log}")
        
# ============================================================
# SELF-CHECK before you look at the solution
# ============================================================
# [ ] My nodes return partial dicts, never the whole mutated state
# [ ] execution_logs uses a reducer, and I can explain why
# [ ] My router has BOTH a quality exit AND an iteration cap
# [ ] Retried searches use a different query than the first attempt
# [ ] I saw the Mermaid diagram and it matches the intended flow
# [ ] I know what GraphRecursionError is and how to trigger it
# [ ] The quality score comes from with_structured_output, not int()
#
# Stuck? Debugging order that works:
#   1. print() the raw return of search_tool.invoke — check its shape
#   2. run app.stream(..., stream_mode="updates") — shows exactly
#      which node produced which state update
#   3. compare your edge wiring against the diagram at the top
#   4. only THEN open day1_lab_solution.py
# ============================================================
