import os
import re
import time
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion, client

load_dotenv()

def route_query(user_input: str, chat_history: list = None) -> dict:
    query_lower = user_input.lower().strip()

    # If this is clearly a follow-up in an ongoing conversation, keep it in general
    followup_starters = (
        "what about", "how about", "tell me more", "explain more", "why",
        "can you explain", "give an example", "give me an example", "what are its",
        "what are their", "how does that", "how do they", "what does this mean",
        "can you write", "write code for this", "give me code for this",
        "elaborate", "clarify", "in other words", "and then", "what next"
    )
    pronoun_indicators = ["its", "this", "that", "these", "those", "it", "they", "them"]

    if chat_history and len(chat_history) > 0:
        words = query_lower.split()
        is_short = len(words) <= 8
        starts_with_followup = any(query_lower.startswith(prefix) for prefix in followup_starters)
        has_pronoun = any(p in words for p in pronoun_indicators)

        # Standalone overrides that definitely require a specific pipeline
        explicit_flight = any(kw in query_lower for kw in ["flight", "track flight", "flight status"])
        explicit_stock = any(kw in query_lower for kw in ["stock price", "analyse stock", "invest in", "ticker"])
        explicit_image = any(kw in query_lower for kw in ["generate image", "create picture", "draw", "generate an image"])

        if (starts_with_followup or (is_short and has_pronoun)) and not (explicit_flight or explicit_stock or explicit_image):
            return {
                "domain": "general",
                "query": user_input
            }

    # Context snippet if history exists
    context_str = ""
    if chat_history and len(chat_history) > 0:
        last_turn = chat_history[-1]
        last_text = last_turn.get("content", "")[:120].replace("\n", " ")
        context_str = f"\n    Recent Conversation Context: \"{last_text}\""

    prompt = f"""
    You are a Router Agent. Classify the user query into exactly one domain.

    DOMAINS:
    1. research - Deep research, detailed reports, latest advancements
    2. stock    - Stock analysis, market data, investment advice
    3. code     - Code review, debugging, programming help
    4. job       - User wants help with a SPECIFIC job application,
                   needs resume tailoring, cover letter writing,
                   interview prep for a specific role they are 
                   APPLYING FOR RIGHT NOW.
                   Keywords: help me apply, write cover letter,
                   tailor my resume, I am applying for, 
                   job application for, prepare me for interview
                   
                   NOT job: "how to become X", "career advice",
                   "what skills do I need", "how to get into X field"
                   These are GENERAL questions.
    5. flight   - Flight tracking, flight status
    6. image    - Generate image, create picture, draw
    7. general  - Simple facts, quick answers, basic questions, conversational follow-ups

    EXAMPLES:
    Query: "What are latest advancements in LLMs?" → research
    Query: "Explain quantum computing in detail"    → research
    Query: "Research about climate change"          → research
    Query: "Deep dive into blockchain technology"   → research
    Query: "Analyse AAPL stock"                     → stock
    Query: "Should I invest in Tesla?"              → stock
    Query: "Review this Python code"                → code
    Query: "Help me apply for ML Engineer job"      → job
    Query: "Track flight AI101"                     → flight
    Query: "Generate image of sunset"               → image
    Query: "Who is Elon Musk?"                      → general
    Query: "What is DNA?"                           → general
    Query: "Who invented telephone?"                → general
    Query: "What is photosynthesis?"                → general
    Query: "Capital of France?"                     → general
    Query: "Tell me a joke"                         → general
    Query: "What is speed of light?"                → general
    Query: "Who wrote Harry Potter?"                → general
    Query: "What are its main advantages?"          → general
    Query: "Can you give me an example?"            → general
    Query: "Explain gravity simply"                → general
    Query: "What is X?"                            → general
    {context_str}

    Now classify this query:
    Query: "{user_input}" →

    Reply with ONLY one word from:
    research, stock, code, job, flight, image, general
    """

    max_retries = 2

    for attempt in range(max_retries):
        try:
            response = create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                timeout=10
            )

            domain = response.choices[0].message.content.strip().lower()

            # Clean up response
            domain = domain.replace(".", "").replace(",", "").strip()

            valid_domains = ["research", "stock", "code",
                             "job", "flight", "image", "general"]

            if domain in valid_domains:
                pass
            else:
                for d in valid_domains:
                    if d in domain:
                        domain = d
                        break
                else:
                    domain = "general"

            # Post-processing: if LLM said research but query looks simple, downgrade to general
            simple_general_patterns = [
                "what is ", "who is ", "who was ",
                "who wrote ", "who invented ", "who discovered ",
                "explain ", "simply", "what are the basic",
                "speed of ", "height of ", "capital of ", "what are ", "why is ", "how does "
            ]
            if domain == "research":
                for pattern in simple_general_patterns:
                    if query_lower.startswith(pattern):
                        research_keywords = [
                            "latest", "advanced", "research",
                            "comprehensive", "detailed", "analysis",
                            "advancements", "future", "deep dive"
                        ]
                        if not any(kw in query_lower for kw in research_keywords):
                            domain = "general"
                        break

            return {
                "domain": domain,
                "query": user_input
            }

        except Exception as e:
            print(f"   ⚠️ Router attempt {attempt+1}/{max_retries} failed: {e}")
            time.sleep(1)

    # Default fallback
    return {
        "domain": "general",
        "query": user_input
    }