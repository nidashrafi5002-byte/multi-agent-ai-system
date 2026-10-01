import json
import re
from typing import Dict, Any, List
from tools.groq_utils import create_chat_completion

def generate_opening_question(
    plan: List[Dict[str, Any]],
    profile: Dict[str, Any],
    interview_type: str,
    target_role: str,
    difficulty: str
) -> str:
    """Generate opening question based on the candidate's resume and initial plan objective."""
    first_step = plan[0] if plan else {}
    prompt = f"""
    You are MAIA's Senior AI Interviewer conducting a realistic {difficulty}-level {interview_type} for the role of {target_role}.
    
    CANDIDATE INFO:
    - Name: {profile.get('candidate_name', 'Candidate')}
    - Key Projects: {profile.get('projects', [])}
    - Skills: {profile.get('skills', [])}
    - First Objective: {first_step.get('focus_area', 'Background & Projects')}
    - Goal: {first_step.get('inquiry_goal', 'Open the interview with a focused question')}

    RULES:
    1. Act like a polite, professional, yet rigorous human interviewer.
    2. Reference specific projects or technologies directly from the candidate's resume.
    3. Start with a warm, conversational opening (e.g., "Thanks for joining us today," "I see you've worked on...")
    4. Ask ONE clear, focused opening question that invites detailed response.
    5. Make it feel like a natural conversation, not an interrogation.
    6. Avoid generic "tell me about yourself" questions — be specific to their experience.
    
    Example opening: "Thanks for joining us today. I see you've worked on several interesting projects, including [specific project]. Could you walk me through how you approached [specific technical challenge] in that project?"
    """
    response = create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4  # Slightly higher for more natural conversation
    )
    return response.choices[0].message.content.strip()


def generate_adaptive_turn(
    history: List[Dict[str, str]],
    plan: List[Dict[str, Any]],
    profile: Dict[str, Any],
    interview_type: str,
    target_role: str,
    difficulty: str,
    current_question_index: int,
    total_questions: int
) -> Dict[str, Any]:
    """Evaluates candidate's previous answer dynamically and formulates the next question."""
    last_turn = history[-1] if history else {}
    last_answer = last_turn.get("candidate_answer", "")
    last_question = last_turn.get("question", "")
    current_objective = plan[min(current_question_index, len(plan) - 1)] if plan else {}
    next_objective = (
        plan[min(current_question_index + 1, len(plan) - 1)]
        if plan and current_question_index + 1 < len(plan)
        else {}
    )

    recent_lines = []
    for turn in history[-4:]:
        recent_lines.append(f"Q: {turn.get('question', '')}\nA: {turn.get('candidate_answer', '')}")
    transcript_snippet = "\n\n".join(recent_lines) if recent_lines else "(first turn)"

    # Calculate answer quality score based on previous turns
    strong_answers = sum(1 for turn in history if len(turn.get('candidate_answer', '')) > 100)
    answer_quality = "high" if strong_answers >= len(history) * 0.7 else "medium" if strong_answers >= len(history) * 0.4 else "low"

    prompt = f"""
    You are an expert AI Interviewer conducting a {difficulty} {interview_type} for a {target_role}.
    
    RECENT TRANSCRIPT:
    {transcript_snippet}
    
    LAST TURN:
    - Interviewer Question: "{last_question}"
    - Candidate Answer: "{last_answer}"
    
    CURRENT TOPIC (Topic {current_question_index + 1} of {total_questions}):
    - Focus: {current_objective.get('focus_area', 'System Competency')}
    - Goal: {current_objective.get('inquiry_goal', 'Assess technical depth')}
    - Resume context: {current_objective.get('context_source', 'Resume')}

    NEXT TOPIC (only if you choose ADVANCE):
    - Focus: {next_objective.get('focus_area', 'Next competency area')}
    - Goal: {next_objective.get('inquiry_goal', 'Continue structured interview')}
    
    CANDIDATE RESUME HIGHLIGHTS (ground questions here — do not invent facts):
    - Projects: {profile.get('projects', [])}
    - Skills: {profile.get('skills', [])}
    
    CANDIDATE PERFORMANCE CONTEXT:
    - Overall answer quality so far: {answer_quality}
    - Questions asked: {len(history)}
    - Remaining questions: {total_questions - current_question_index}
    
    EVALUATION & ADAPTIVE STRATEGY:
    1. Analyze the candidate's answer for:
       - Technical correctness and depth
       - Specific examples and concrete details
       - Understanding of trade-offs and alternatives
       - Ability to explain "why" behind technical choices
       - Relevance to the question asked
    
    2. Choose ONE strategy based on answer quality:
       - PROBE: Candidate made a specific technical claim — probe deeper on the SAME topic:
         * Ask about tool/library choice rationale
         * Ask about evaluation metrics or performance
         * Ask about trade-offs considered
         * Ask about alternative approaches they rejected
         * Example: "Why did you choose ChromaDB over Pinecone for this architecture?"
       
       - CLARIFY: Answer was vague, incomplete, or lacked specifics:
         * Ask for a concrete example from their project
         * Ask for specific metrics or outcomes
         * Ask about implementation details
         * Example: "Can you walk me through a specific example of how you implemented that?"
       
       - CHALLENGE: Strong answer — test deeper understanding:
         * Ask about edge cases or failure modes
         * Ask about scale considerations
         * Ask "what would you change now?"
         * Ask about limitations of their approach
         * Example: "How would this architecture handle 10x the current load?"
       
       - ADVANCE: Answer was comprehensive and satisfactory:
         * Move to NEXT TOPIC
         * Reference their previous answer to maintain flow
         * Ask ONE new question aligned with next objective
         * Example: "That's a solid approach. Let's move on — can you tell me about your experience with [next topic]?"
    
    3. Difficulty Adjustment:
       - If answer_quality is "high": Increase question complexity (use CHALLENGE more)
       - If answer_quality is "low": Simplify and use CLARIFY to build confidence
       - Always maintain professional, conversational tone
    
    4. Natural Conversation Flow:
       - Reference specific technologies or concepts from their answer
       - Use transitional phrases: "That's interesting," "I see," "Good point"
       - Make questions feel like natural follow-ups, not rigid interrogations
       - Avoid robotic "Thank you for your answer" transitions
    
    Reply ONLY with a JSON object:
    {{
        "assessment": "1-sentence assessment of the candidate's answer quality and technical depth",
        "action": "PROBE" or "CLARIFY" or "CHALLENGE" or "ADVANCE",
        "next_question": "A natural, conversational follow-up question that references their answer when appropriate"
    }}
    """
    try:
        response = create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4  # Slightly higher for more natural conversation
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        return json.loads(content)
    except Exception:
        return {
            "assessment": "Candidate responded to previous inquiry.",
            "action": "ADVANCE",
            "next_question": f"Thanks for that. Let's move to our next topic — can you discuss your experience with {current_objective.get('focus_area', 'this domain')}?"
        }

# Alias for compatibility
get_next_question = generate_adaptive_turn
