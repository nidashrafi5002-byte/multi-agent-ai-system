import json
import re
from typing import Dict, Any, List
from tools.groq_utils import create_chat_completion

def plan_interview(
    profile: Dict[str, Any],
    interview_type: str = "Technical Interview",
    target_role: str = "Software Engineer",
    difficulty: str = "Mid-Level",
    num_questions: int = 5
) -> List[Dict[str, Any]]:
    """Generate an adaptive interview roadmap aligned to the candidate's resume and target role."""
    prompt = f"""
    You are a Lead Technical Hiring Manager.
    Design an interview roadmap for a candidate based on their verified resume profile.

    INTERVIEW DETAILS:
    - Target Role: {target_role}
    - Interview Type: {interview_type}
    - Seniority: {difficulty}
    - Total Questions: {num_questions}

    CANDIDATE RESUME PROFILE:
    - Name: {profile.get('candidate_name', 'Candidate')}
    - Key Skills: {', '.join(profile.get('skills', [])[:10])}
    - Technologies: {', '.join(profile.get('frameworks_and_tools', [])[:10])}
    - Projects: {[p.get('title') for p in profile.get('projects', [])]}

    INSTRUCTIONS:
    1. If interview_type is 'Project Defense', dedicate questions directly to verifying architecture, routing, tool choices, trade-offs, and failure modes for their listed projects.
    2. Provide exactly {num_questions} sequential interview objectives.

    Return ONLY a JSON array of objectives:
    [
        {{
            "step": 1,
            "focus_area": "e.g., Project Defense: Architecture & Core Decisions",
            "context_source": "Project: MAIA Multi-Agent System",
            "inquiry_goal": "Probe candidate's rationale for choosing LangGraph over linear pipelines."
        }}
    ]
    """

    try:
        response = create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        
        plan = json.loads(content)
        if isinstance(plan, list) and len(plan) > 0:
            return plan[:num_questions]
    except Exception:
        pass

    fallback_plan = []
    projects = profile.get("projects", [])
    proj_title = projects[0].get("title", "Key Project") if projects else "Core Experience"
    for i in range(1, num_questions + 1):
        fallback_plan.append({
            "step": i,
            "focus_area": f"Technical Deep Dive {i}" if i > 1 else f"Project Defense: {proj_title}",
            "context_source": proj_title,
            "inquiry_goal": f"Evaluate technical competence for {target_role} at {difficulty} level."
        })
    return fallback_plan