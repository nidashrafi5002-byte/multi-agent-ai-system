"""
Interview Pipeline
Orchestrates resume analysis, planning, adaptive questioning, and evaluation.
Interfaces cleanly with backend/routes/interview.py and React frontend.
"""
from typing import Dict, Any, List
from agents.resume_analyzer import extract_text_from_file, analyze_resume
from agents.interview_planner import plan_interview
from agents.interviewer_agent import generate_opening_question, generate_adaptive_turn
from agents.interview_evaluator import generate_interview_report

try:
    from memory.history_db import add_history
except ImportError:
    add_history = None  # type: ignore

MAX_FOLLOW_UPS_PER_TOPIC = 3


def _finalize_session(session: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report and optionally log completion to MAIA history."""
    session["is_completed"] = True
    session["finished"] = True
    session["report"] = generate_interview_report(
        profile=session["profile"],
        turns=session.get("history", []),
        interview_type=session.get("interview_type", "Technical Interview"),
        target_role=session.get("target_role", "AI Engineer"),
        difficulty=session.get("difficulty", "Mid-Level"),
    )
    if add_history:
        name = session.get("profile", {}).get("candidate_name", "Candidate")
        itype = session.get("interview_type", "Interview")
        role = session.get("target_role", "")
        add_history("interview", f"{itype} — {name} ({role})")
    return session


def extract_and_profile_resume(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Stage 1: Extract text and parse resume into structured candidate profile."""
    raw_text = extract_text_from_file(file_bytes, filename)
    profile = analyze_resume(raw_text)
    return profile


def start_interview_session(
    profile: Dict[str, Any],
    interview_type: str = "Technical Interview",
    target_role: str = "AI Engineer",
    difficulty: str = "Mid-Level",
    total_questions: int = 5,
) -> Dict[str, Any]:
    """Stage 2: Generate interview plan and return initialized session with opening question."""
    plan = plan_interview(profile, interview_type, target_role, difficulty, total_questions)
    opening_question = generate_opening_question(plan, profile, interview_type, target_role, difficulty)

    return {
        "profile": profile,
        "interview_type": interview_type,
        "target_role": target_role,
        "difficulty": difficulty,
        "total_questions": total_questions,
        "question_count": total_questions,
        "plan": plan,
        "history": [],
        "current_question": opening_question,
        "current_question_index": 0,
        "follow_ups_on_topic": 0,
        "last_action": None,
        "is_completed": False,
        "finished": False,
        "report": None,
    }


def submit_candidate_answer(session: Dict[str, Any], answer: str) -> Dict[str, Any]:
    """Stage 3: Process candidate answer, adaptively formulate next question or finalize."""
    current_q = session.get("current_question", "Tell me about your technical background.")
    stripped = answer.strip()
    if not stripped:
        raise ValueError("Answer cannot be empty.")

    session.setdefault("history", []).append({
        "question": current_q,
        "candidate_answer": stripped,
    })

    plan_idx = session.get("current_question_index", 0)
    total_q = session.get("total_questions", 5)

    next_turn = generate_adaptive_turn(
        history=session["history"],
        plan=session.get("plan", []),
        profile=session["profile"],
        interview_type=session.get("interview_type", "Technical Interview"),
        target_role=session.get("target_role", "AI Engineer"),
        difficulty=session.get("difficulty", "Mid-Level"),
        current_question_index=plan_idx,
        total_questions=total_q,
    )

    action = str(next_turn.get("action", "ADVANCE")).upper().strip()
    if action not in ("PROBE", "CLARIFY", "CHALLENGE", "ADVANCE"):
        action = "ADVANCE"

    follow_ups = session.get("follow_ups_on_topic", 0)
    if action != "ADVANCE":
        follow_ups += 1
        if follow_ups >= MAX_FOLLOW_UPS_PER_TOPIC:
            action = "ADVANCE"
            follow_ups = 0
    else:
        follow_ups = 0

    session["follow_ups_on_topic"] = follow_ups
    session["last_action"] = action
    session["last_assessment"] = next_turn.get("assessment", "")

    if action == "ADVANCE":
        plan_idx += 1
        session["current_question_index"] = plan_idx

    if plan_idx >= total_q:
        return _finalize_session(session)

    session["current_question"] = next_turn.get("next_question", "")
    session["is_completed"] = False
    session["finished"] = False
    return session


def generate_evaluation_report(session: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 4: Generate or return comprehensive evaluation report."""
    if session.get("report"):
        return session["report"]

    report = generate_interview_report(
        profile=session.get("profile", {}),
        turns=session.get("history", []),
        interview_type=session.get("interview_type", "Technical Interview"),
        target_role=session.get("target_role", "AI Engineer"),
        difficulty=session.get("difficulty", "Mid-Level")
    )
    session["report"] = report
    session["is_completed"] = True
    session["finished"] = True
    return report