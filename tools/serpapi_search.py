"""
tools/serpapi_search.py
-----------------------
Public-facing SerpApi interface for MAIA.
Wraps tools/serpapi_tool.py with the exact API surface described in the
SerpApi India Hackathon integration plan.

Usage:
    from tools.serpapi_search import search_web, format_results
"""

import os
from tools.serpapi_tool import (
    search_web as _search_web,
    is_serpapi_available,
    needs_web_search,
)


def search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search the web via SerpApi Google Search.

    Args:
        query: The search query string.
        num_results: Max number of organic results to return (default 5).

    Returns:
        List of dicts with keys: title, snippet, link.
        Returns empty list if SerpApi is unavailable or the call fails.
    """
    result = _search_web(query, num_results=num_results)
    if not result.get("success") or not result.get("sources"):
        return []

    return [
        {
            "title":   s.get("title", ""),
            "snippet": s.get("snippet", ""),
            "link":    s.get("link", ""),
        }
        for s in result["sources"]
    ]


def format_results(results: list[dict]) -> str:
    """Format a list of search result dicts into readable text for Groq prompt injection.

    Args:
        results: List of {title, snippet, link} dicts from search_web().

    Returns:
        Formatted string ready to inject into a Groq prompt.
        Empty string if results list is empty.
    """
    if not results:
        return ""

    lines = ["WEB SEARCH RESULTS (use these for current information):"]
    for i, r in enumerate(results, 1):
        title   = r.get("title", "No title")
        snippet = r.get("snippet", "No description available.")
        link    = r.get("link", "")
        lines.append(f"\n[{i}] {title}")
        lines.append(f"    {snippet}")
        if link:
            lines.append(f"    Source: {link}")

    lines.append(
        "\nCite sources in your response as [Source: URL] where relevant."
    )
    return "\n".join(lines)
