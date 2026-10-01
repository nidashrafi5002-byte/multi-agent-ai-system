import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion
from tools.serpapi_tool import search_web, needs_web_search, is_serpapi_available

load_dotenv()

def research_topic(plan: dict) -> dict:
    original_query = plan.get('original_query', '')
    plan_text = plan.get('plan', '')
    
    # Check if this topic benefits from live web search and if SerpApi is configured
    web_search_used = False
    search_context_text = ""
    sources = []

    if is_serpapi_available() and needs_web_search(original_query, plan_text):
        print(f"🔍 [SerpApi] Conducting live web search for: '{original_query[:60]}'...")
        search_result = search_web(original_query, num_results=5)
        if search_result.get("success") and search_result.get("sources"):
            web_search_used = True
            sources = search_result["sources"]
            search_context_text = search_result["text"]
            print(f"✅ [SerpApi] Grounded with {len(sources)} live web sources")

    grounding_instruction = ""
    if web_search_used and search_context_text:
        grounding_instruction = f"""
    LIVE WEB GROUNDING EVIDENCE (via SerpApi):
    {search_context_text}

    GROUNDING INSTRUCTIONS:
    - Ground your findings in the verified search results above.
    - Explicitly mention recent real-world advancements, papers, tools, or opportunities found in the search context.
    - Reference source domains/links where appropriate to provide authoritative attribution.
    """

    prompt = f"""
    You are a Research Agent. Your job is to research 
    a topic based on the given plan and provide detailed 
    findings for each subtask.

    Original Topic: {original_query}

    Research Plan:
    {plan_text}
    {grounding_instruction}

    IMPORTANT: Always detect the language of the user's
    message and respond in that SAME language.
    If user writes in Hindi, respond in Hindi.
    If user writes in Japanese, respond in Japanese.
    If user writes in Tamil, respond in Tamil.
    Never switch languages unless user asks.

    For each subtask in the plan, provide:
    - Detailed, substantive technical findings
    - Key architectural/theoretical mechanics and data points
    - Concrete real-world examples and benchmarks
    - Latest developments and updates when available

    Be exhaustive, rigorous, and highly informative.
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096,
    )

    research = response.choices[0].message.content.strip()

    return {
        "original_query": original_query,
        "plan": plan_text,
        "research": research,
        "sources": sources,
        "web_search_used": web_search_used
    }