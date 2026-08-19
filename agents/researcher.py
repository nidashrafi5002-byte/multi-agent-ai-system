import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion

load_dotenv()

def research_topic(plan: dict) -> dict:

    prompt = f"""
    You are a Research Agent. Your job is to research 
    a topic based on the given plan and provide detailed 
    findings for each subtask.

    Original Topic: {plan['original_query']}

    Research Plan:
    {plan['plan']}

    IMPORTANT: Always detect the language of the user's
    message and respond in that SAME language.
    If user writes in Hindi, respond in Hindi.
    If user writes in Japanese, respond in Japanese.
    If user writes in Tamil, respond in Tamil.
    Never switch languages unless user asks.

    For each subtask in the plan, provide:
    - Detailed findings
    - Key points
    - Real world examples

    Be thorough and informative.
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    research = response.choices[0].message.content.strip()

    return {
        "original_query": plan['original_query'],
        "plan": plan['plan'],
        "research": research
    }