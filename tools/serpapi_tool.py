"""
SerpApi Search Tool for MAIA
Provides real-time web search and information retrieval using the SerpApi Google Search engine.
Designed for the SerpApi India Hackathon to ground the Research Agent with verified, current sources.
"""

import os
import re
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


def get_serpapi_key() -> Optional[str]:
    """Retrieve and clean the SerpApi API key from environment."""
    key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
    if key:
        cleaned = key.strip().strip("'\"")
        if cleaned and cleaned.lower() not in {"your_serpapi_key_here", "your_serpapi_key", ""}:
            return cleaned
    return None


def is_serpapi_available() -> bool:
    """Check if a valid SerpApi key is present."""
    return get_serpapi_key() is not None


def needs_web_search(query: str, plan: str = "") -> bool:
    """Intelligently determine if a query requires fresh or live web information.
    
    Identifies:
    - Time-sensitive queries ('latest', 'recent', 'current', '2024', '2025', '2026')
    - Real-world opportunities ('internship', 'job openings', 'hiring', 'grants')
    - Fast-evolving domains (AI/ML models, breakthroughs, tech releases, policy)
    - Fact-checking & entity grounding (named studies, papers, specific works)
    """
    text = f"{query} {plan}".lower()

    # Temporal indicators
    temporal_triggers = [
        "latest", "recent", "recently", "current", "currently", "today",
        "now", "newest", "advancement", "advancements", "update", "updates",
        "trend", "trends", "emerging", "future", "breakthrough", "breakthroughs",
        "state of the art", "sota", "release", "announced", "2024", "2025", "2026"
    ]
    if any(re.search(rf"\b{re.escape(word)}\b", text) for word in temporal_triggers):
        return True

    # Real-world opportunity & discovery triggers
    discovery_triggers = [
        "internship", "internships", "job opening", "job openings", "hiring",
        "opportunities", "vacancies", "fellowship", "salary", "conference",
        "market price", "stock", "funding", "acquisition"
    ]
    if any(re.search(rf"\b{re.escape(word)}\b", text) for word in discovery_triggers):
        return True

    # Search-explicit triggers
    search_triggers = [
        "search for", "find me", "look up", "news about", "who is the current",
        "what is the current", "papers on", "case studies on"
    ]
    if any(trigger in text for trigger in search_triggers):
        return True

    # Named papers, authors, or literary works needing grounded facts
    has_author_or_work = bool(
        re.search(r"['\"].+?['\"]", f"{query} {plan}")
        or re.search(r"\b[A-Za-z]+'s\s+", f"{query} {plan}")
        or (
            re.search(r"\b(poem|poetry|novel|book|play|study|paper|essay|author|writer|researcher)\b", text)
            and (
                re.search(r"\b(by|written by|authored by|analysis of|summary of)\b", text)
                or re.search(r"\b[a-z]+'s\b", text)
            )
        )
    )
    if has_author_or_work:
        return True


    return False


def search_web(
    query: str,
    num_results: int = 5,
    engine: str = "google",
    hl: str = "en",
    gl: str = "in"
) -> Dict[str, Any]:
    """Execute a Google web search via SerpApi and return structured, grounded sources.
    
    Args:
        query: Search keywords or query string
        num_results: Number of organic results to extract (default 5)
        engine: Search engine to query (default 'google')
        hl: Host language code (default 'en')
        gl: Geolocation code (default 'in' for India Hackathon, configurable)

    Returns:
        dict containing:
            - success (bool): Whether the search succeeded
            - query (str): The search query used
            - sources (list[dict]): List of {title, link, snippet, source, date}
            - text (str): Formatted markdown block ready for LLM context injection
            - answer_box (dict): Direct Google answer box if found
            - error (str | None): Error description if unsuccessful
    """
    api_key = get_serpapi_key()
    if not api_key:
        return {
            "success": False,
            "query": query,
            "sources": [],
            "text": "SerpApi key not configured. Continuing with internal model knowledge.",
            "answer_box": None,
            "error": "SERPAPI_KEY missing in environment"
        }

    # Clean the query for web search (strip filler instructions)
    clean_query = re.sub(r"^(please\s+)?(search\s+for|find\s+me|research|deep\s+dive\s+into)\s+", "", query, flags=re.IGNORECASE).strip()
    if not clean_query:
        clean_query = query

    params = {
        "engine": engine,
        "q": clean_query,
        "api_key": api_key,
        "num": num_results,
        "hl": hl,
        "gl": gl,
    }

    try:
        # Try official SDK first if available, otherwise direct HTTP request
        data = None
        try:
            from serpapi import GoogleSearch
            search = GoogleSearch(params)
            data = search.get_dict()
        except ImportError:
            # Resilient fallback: direct REST call to SerpApi endpoint
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
            response.raise_for_status()
            data = response.json()

        if not data or "error" in data:
            err_msg = data.get("error", "Unknown SerpApi error") if data else "Empty response"
            return {
                "success": False,
                "query": clean_query,
                "sources": [],
                "text": f"SerpApi query failed: {err_msg}",
                "answer_box": None,
                "error": err_msg
            }

        sources: List[Dict[str, str]] = []
        snippets_text: List[str] = []

        # 1. Check Answer Box (instant direct answer)
        answer_box = data.get("answer_box")
        if answer_box:
            direct_ans = answer_box.get("answer") or answer_box.get("snippet") or answer_box.get("result")
            ans_title = answer_box.get("title", "Quick Answer")
            ans_link = answer_box.get("link", "")
            if direct_ans:
                snippets_text.append(f"**Direct Answer ({ans_title})**: {direct_ans}")
                if ans_link:
                    sources.append({
                        "title": ans_title,
                        "link": ans_link,
                        "snippet": str(direct_ans)[:200],
                        "source": "Google Answer Box",
                        "date": ""
                    })

        # 2. Check Knowledge Graph
        kg = data.get("knowledge_graph")
        if kg:
            kg_title = kg.get("title", "")
            kg_desc = kg.get("description", "")
            kg_source = kg.get("source", {}).get("name", "Knowledge Graph")
            kg_link = kg.get("source", {}).get("link", "")
            if kg_desc:
                snippets_text.append(f"**Entity Overview ({kg_title})**: {kg_desc}")
                if kg_link:
                    sources.append({
                        "title": f"{kg_title} ({kg_source})",
                        "link": kg_link,
                        "snippet": kg_desc[:200],
                        "source": kg_source,
                        "date": ""
                    })

        # 3. Extract Organic Search Results
        organic_results = data.get("organic_results", [])
        for item in organic_results[:num_results]:
            title = item.get("title", "").strip()
            link = item.get("link", "").strip()
            snippet = item.get("snippet", "").strip()
            source_name = item.get("source") or item.get("displayed_link", "")
            date = item.get("date", "")

            if title and link:
                sources.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": str(source_name),
                    "date": str(date)
                })

                date_part = f" ({date})" if date else ""
                source_part = f" [{source_name}]" if source_name else ""
                snippets_text.append(f"- **[{title}]({link})**{source_part}{date_part}: {snippet}")

        if not sources:
            return {
                "success": True,
                "query": clean_query,
                "sources": [],
                "text": "No live web search results found for this query.",
                "answer_box": answer_box,
                "error": None
            }

        formatted_context = "### Live Web Search Grounding (via SerpApi):\n" + "\n".join(snippets_text)

        return {
            "success": True,
            "query": clean_query,
            "sources": sources,
            "text": formatted_context,
            "answer_box": answer_box,
            "error": None
        }

    except Exception as exc:
        print(f"⚠️ SerpApi search exception: {exc}")
        return {
            "success": False,
            "query": clean_query,
            "sources": [],
            "text": f"Web search could not be completed: {exc}",
            "answer_box": None,
            "error": str(exc)
        }
