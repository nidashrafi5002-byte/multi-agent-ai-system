import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion

load_dotenv()

def write_report(research: dict) -> dict:

    sources = research.get("sources", [])
    sources_note = ""
    if sources:
        sources_note = "\n    Note: Ground your citations in the verified sources provided in the research findings and cite them where relevant."

    prompt = f"""
    You are a Senior Research Writer Agent. Turn the research findings into an exhaustive, high-depth, long-form research report.
    Do NOT add any byline, author name, "Prepared by", or "Date" header. Start directly with the report title or first section.
    Original Topic: {research['original_query']}

    Research Findings:
    {research['research']}
    {sources_note}

    IMPORTANT: Detect the language of the topic
    and write the entire report in that SAME language.

    Write a comprehensive, multi-section research report with substantial depth, detailed multi-paragraph explanations, and technical elaboration:
    
    1. COMPREHENSIVE OVERVIEW
       Thorough introduction, context, and fundamental significance of the topic.
    
    2. IN-DEPTH KEY FINDINGS & MECHANISMS
       Detailed analysis of findings, architectural/theoretical mechanics, quantitative data, and benchmarks.
    
    3. REAL-WORLD APPLICATIONS & CASE STUDIES
       Extensive breakdown of how this is implemented across industries, specific tools/models, and measurable impacts.
    
    4. CRITICAL CHALLENGES & BOTTLENECKS
       In-depth examination of limitations, risks, technical bottlenecks, and operational hurdles.
    
    5. STRATEGIC FUTURE DIRECTIONS & HORIZONS
       Where this field is heading, emerging research frontiers, and long-term implications.

    Provide rich explanations, concrete examples, and thorough analysis. Do not write a short summary.

    Make it authoritative, professional, and clear.
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096,
    )

    written_report = response.choices[0].message.content.strip()

    # Append verified sources if present and not already formatted in the report
    if sources and "http" not in written_report:
        sources_md = "\n".join([f"- [{s.get('title', 'Source')}]({s.get('link', '#')}) - *{s.get('source', '')}*" for s in sources if s.get('link')])
        if sources_md:
            written_report += f"\n\n### 🔗 Verified Sources & Grounded References (SerpApi):\n{sources_md}"

    return {
        "original_query": research['original_query'],
        "plan": research['plan'],
        "research": research['research'],
        "sources": sources,
        "written_report": written_report
    }
