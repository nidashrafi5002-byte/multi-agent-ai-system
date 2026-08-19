import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from groq import APIStatusError, RateLimitError
from tools.groq_utils import create_chat_completion

load_dotenv()

# ─────────────────────────────────────
# STATE — shared memory between nodes
# ─────────────────────────────────────
class AgentState(TypedDict):
    user_input: str
    domain: str
    plan: str
    research: str
    written_report: str
    quality_score: int
    retry_count: int
    final_output: str
    execution_log: list

# ─────────────────────────────────────
# NODE 1 — Input Node
# ─────────────────────────────────────
def input_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 1: INPUT NODE")
    state["execution_log"].append({
        "node": "Input Node",
        "status": "✅ Complete",
        "detail": f"Received: {state['user_input'][:50]}..."
    })
    print(f"✅ Input received: {state['user_input'][:50]}...")
    return state

# ─────────────────────────────────────
# NODE 2 — Router Node
# ─────────────────────────────────────
def router_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 2: ROUTER NODE")

    prompt = f"""
    Classify this query into one domain:
    research, stock, code, job, flight, general

    Query: {state['user_input']}

    Reply with ONLY one word.
    """

    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )

    domain = response.choices[0].message.content.strip().lower()
    valid = ["research", "stock", "code", "job", "flight", "general"]
    if domain not in valid:
        domain = "general"

    state["domain"] = domain
    state["execution_log"].append({
        "node": "Router Node",
        "status": "✅ Complete",
        "detail": f"Domain: {domain.upper()}"
    })
    print(f"✅ Domain: {domain.upper()}")
    return state

# ─────────────────────────────────────
# NODE 3 — Planner Node
# ─────────────────────────────────────
def planner_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 3: PLANNER NODE")

    prompt = f"""
    Break this query into 4 clear subtasks.
    
    Query: {state['user_input']}
    Domain: {state['domain']}

    Reply in this format:
    1. [subtask]
    2. [subtask]
    3. [subtask]
    4. [subtask]
    """

    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )

    plan = response.choices[0].message.content.strip()
    state["plan"] = plan

    state["execution_log"].append({
        "node": "Planner Node",
        "status": "✅ Complete",
        "detail": "4 subtasks created"
    })
    print("✅ Plan created!")
    return state

# ─────────────────────────────────────
# NODE 4 — Researcher Node
# ─────────────────────────────────────
def researcher_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 4: RESEARCHER NODE")

    prompt = f"""
    Research this topic thoroughly based on the plan.

    Topic: {state['user_input']}
    Plan: {state['plan']}

    Provide detailed findings for each subtask.
    Include real world examples and key facts.
    """

    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )

    research = response.choices[0].message.content.strip()
    state["research"] = research

    state["execution_log"].append({
        "node": "Researcher Node",
        "status": "✅ Complete",
        "detail": "Research completed"
    })
    print("✅ Research done!")
    return state

# ─────────────────────────────────────
# NODE 5 — Writer Node
# ─────────────────────────────────────
def writer_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 5: WRITER NODE")

    retry_msg = ""
    if state["retry_count"] > 0:
        retry_msg = f"This is retry #{state['retry_count']}. Make it much better!"

    prompt = f"""
    Write a professional structured report.
    {retry_msg}

    Topic: {state['user_input']}
    Research: {state['research']}

    Include these sections:
    1. OVERVIEW
    2. KEY FINDINGS  
    3. REAL WORLD APPLICATIONS
    4. CHALLENGES
    5. FUTURE SCOPE
    
    Make it detailed, clear and professional.
    """

    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )

    report = response.choices[0].message.content.strip()
    state["written_report"] = report

    state["execution_log"].append({
        "node": "Writer Node",
        "status": "✅ Complete",
        "detail": f"Report written (Attempt {state['retry_count'] + 1})"
    })
    print("✅ Report written!")
    return state

# ─────────────────────────────────────
# NODE 6 — Reviewer Node
# ─────────────────────────────────────
def reviewer_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 6: REVIEWER NODE")

    prompt = f"""
    Review this report and give a quality score.

    Report: {state['written_report']}

    Score out of 100 based on:
    - Completeness
    - Clarity  
    - Depth
    - Structure

    Reply ONLY in this format:
    SCORE: [number]
    FEEDBACK: [one line]
    """

    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}]
    )

    review = response.choices[0].message.content.strip()

    # Extract score
    score = 75
    for line in review.split("\n"):
        if "SCORE:" in line:
            try:
                score = int(line.split(":")[1].strip())
            except:
                score = 75

    state["quality_score"] = score

    state["execution_log"].append({
        "node": "Reviewer Node",
        "status": "✅ Complete",
        "detail": f"Quality Score: {score}/100"
    })
    print(f"✅ Quality Score: {score}/100")
    return state

# ─────────────────────────────────────
# NODE 7 — Output Node
# ─────────────────────────────────────
def output_node(state: AgentState) -> AgentState:
    print("\n📍 NODE 7: OUTPUT NODE")

    from datetime import datetime
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final = f"""
{'='*60}
        RESEARCH REPORT — LangGraph
{'='*60}
Topic    : {state['user_input']}
Date     : {now}
Score    : {state['quality_score']}/100
Retries  : {state['retry_count']}
{'='*60}

{state['written_report']}

{'='*60}
    """

    state["final_output"] = final
    state["execution_log"].append({
        "node": "Output Node",
        "status": "✅ Complete",
        "detail": "Final report ready!"
    })
    print("✅ Final output ready!")
    return state

# ─────────────────────────────────────
# ROUTING LOGIC
# ─────────────────────────────────────
def should_retry(state: AgentState) -> Literal["retry", "output"]:
    """If quality score < 70 retry writer — max 2 retries"""
    if state["quality_score"] < 70 and state["retry_count"] < 2:
        state["retry_count"] += 1
        print(f"\n🔄 Score too low! Retrying... (Attempt {state['retry_count']})")
        return "retry"
    return "output"

# ─────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("input", input_node)
    graph.add_node("router", router_node)
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("output", output_node)

    # Add edges
    graph.set_entry_point("input")
    graph.add_edge("input", "router")
    graph.add_edge("router", "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "reviewer")

    # Conditional edge — retry or output
    graph.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "retry": "writer",
            "output": "output"
        }
    )

    graph.add_edge("output", END)

    return graph.compile()

# ─────────────────────────────────────
# RUN FUNCTION
# ─────────────────────────────────────
def run_graph(user_input: str) -> dict:
    graph = build_graph()

    initial_state = AgentState(
        user_input=user_input,
        domain="",
        plan="",
        research="",
        written_report="",
        quality_score=0,
        retry_count=0,
        final_output="",
        execution_log=[]
    )

    result = graph.invoke(initial_state)
    return result