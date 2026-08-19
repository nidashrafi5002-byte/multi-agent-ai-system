import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion

load_dotenv()

def plan_research(user_query: str) -> dict:

    prompt = f"""
    You are a Planner Agent. Your job is to break down 
    a research topic into exactly 4 clear subtasks.

    User wants to research: {user_query}

    Return ONLY this format, nothing else:
    1. [subtask 1]
    2. [subtask 2]
    3. [subtask 3]
    4. [subtask 4]
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    plan = response.choices[0].message.content.strip()

    return {
        "original_query": user_query,
        "plan": plan
    }