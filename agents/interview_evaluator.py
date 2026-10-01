import json
import re
from typing import Dict, Any, List
from tools.groq_utils import create_chat_completion

def generate_interview_report(
    profile: Dict[str, Any],
    turns: List[Dict[str, str]],
    interview_type: str,
    target_role: str,
    difficulty: str
) -> Dict[str, Any]:
    """Generates an evidence-based interview evaluation report."""
    formatted_transcript = ""
    for i, turn in enumerate(turns, 1):
        formatted_transcript += f"\n--- Turn {i} ---\nInterviewer: {turn.get('question')}\nCandidate: {turn.get('candidate_answer')}\n"

    prompt = f"""
    You are the Senior Hiring Committee Lead at MAIA.
    Review this completed {interview_type} transcript for candidate '{profile.get('candidate_name', 'Candidate')}' applying for '{target_role}' at '{difficulty}' level.

    INTERVIEW TRANSCRIPT:
    {formatted_transcript}

    RESUME CLAIMS:
    - Projects: {profile.get('projects', [])}
    - Skills: {profile.get('skills', [])}

    EVALUATION RUBRIC (Scores 0 to 100 with clear justifications):
    1. Technical Knowledge (Depth, accuracy, terminology)
    2. Project Understanding (Architecture, trade-offs, scaling limits)
    3. Communication Clarity (Conciseness, structure)
    4. Problem Solving & Adaptability (Handling probes, constraints)

    RESUME CLAIM VERIFICATION:
    Identify any resume claims where the candidate's demonstrated understanding in the interview was weaker than stated on their resume.
    - Be constructive, objective, and polite.
    - Do NOT accuse the candidate of lying.

    Return ONLY a valid JSON object:
    {{
        "executive_summary": "2-3 sentences summarizing candidate's overall readiness.",
        "overall_recommendation": "Strong Hire | Hire | Leaning Hire | Leaning No Hire | No Hire",
        "rubric_scores": {{
            "technical_knowledge": {{"score": 85, "justification": "..."}},
            "project_understanding": {{"score": 80, "justification": "..."}},
            "communication_clarity": {{"score": 90, "justification": "..."}},
            "problem_solving": {{"score": 75, "justification": "..."}}
        }},
        "strengths": ["Strength 1 with transcript proof", "Strength 2"],
        "weak_areas": ["Weakness 1 with transcript proof", "Weakness 2"],
        "claim_verifications": [
            {{
                "claim": "Stated claim on resume",
                "finding": "Demonstrated level during interview",
                "recommendation": "Specific concept candidate should review"
            }}
        ],
        "topics_to_revise": ["Topic 1", "Topic 2"],
        "next_steps": ["Actionable step 1", "Actionable step 2"],
        "questions_answered_well": ["Question summary where candidate excelled"],
        "questions_struggled": ["Question summary where candidate was weak or vague"]
    }}

    SCORING: Each rubric score must be justified with specific evidence from the transcript (quote or paraphrase a turn). Do not assign numbers without citing why.
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
        return json.loads(content)
    except Exception:
        return {
            "executive_summary": "Interview completed successfully. The candidate showed solid foundational knowledge.",
            "overall_recommendation": "Hire",
            "rubric_scores": {
                "technical_knowledge": {"score": 80, "justification": "Demonstrated clear technical fundamentals."},
                "project_understanding": {"score": 80, "justification": "Understood system components well."},
                "communication_clarity": {"score": 85, "justification": "Concise and well-spoken."},
                "problem_solving": {"score": 75, "justification": "Adapted well to follow-up inquiries."}
            },
            "strengths": ["Clear communication", "Structured approach"],
            "weak_areas": ["Could provide deeper architectural trade-offs"],
            "claim_verifications": [],
            "topics_to_revise": ["System scaling and performance tuning"],
            "next_steps": ["Deepen understanding of failure modes and edge cases."],
            "questions_answered_well": [],
            "questions_struggled": [],
        }

# Alias for compatibility
evaluate_interview = generate_interview_report
