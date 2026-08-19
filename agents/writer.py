import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion

load_dotenv()

def write_report(research: dict) -> dict:

    prompt = f"""
    You are a Writer Agent. Your job is to take 
    research findings and write a clean, structured, 
    and professional research report.

    Original Topic: {research['original_query']}

    Research Findings:
    {research['research']}

    IMPORTANT: Detect the language of the topic
    and write the entire report in that SAME language.

    Write a professional report with these sections:
    
    1. OVERVIEW
       Brief introduction to the topic
    
    2. KEY FINDINGS
       Most important discoveries and facts
    
    3. REAL WORLD APPLICATIONS
       How this is being used in the real world
    
    4. CHALLENGES
       Current limitations and problems
    
    5. FUTURE SCOPE
       Where this is heading in the future

    Make it clear, professional and easy to read.
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    written_report = response.choices[0].message.content.strip()

    return {
        "original_query": research['original_query'],
        "plan": research['plan'],
        "research": research['research'],
        "written_report": written_report
    }