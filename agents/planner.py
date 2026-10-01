import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion

load_dotenv()

def plan_research(user_query: str) -> dict:

    prompt = f"""
    You are a Senior Planner Agent. Your job is to break down 
    a research topic into 5 to 6 comprehensive, structured research pillars.
    Cover theoretical foundations, architectural mechanisms, real-world case studies/benchmarks,
    critical trade-offs/challenges, and future horizons.

    User wants to research: {user_query}

    Return ONLY this format, nothing else:
    1. [Pillar 1: Theoretical Background & Foundational Principles]
    2. [Pillar 2: Technical Architecture & Core Mechanisms]
    3. [Pillar 3: Real-World Implementations, Benchmarks & Case Studies]
    4. [Pillar 4: Comparative Trade-offs & Critical Limitations]
    5. [Pillar 5: Practical Challenges, Safety & Mitigation Strategies]
    6. [Pillar 6: Future Horizons & Emerging Paradigms]
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    plan = response.choices[0].message.content.strip()

    return {
        "original_query": user_query,
        "plan": plan
    }