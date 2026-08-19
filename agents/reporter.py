import os
from dotenv import load_dotenv
from groq import APIStatusError, RateLimitError
from tools.groq_utils import create_chat_completion
from datetime import datetime

load_dotenv()

def generate_report(written_report: dict) -> str:

    prompt = f"""
    You are a Reporter Agent. Your job is to review 
    the written report and give it a quality score.

    Written Report:
    {written_report['written_report']}

    Check the report for:
    1. Completeness — are all sections covered?
    2. Clarity — is it easy to understand?
    3. Accuracy — does it make logical sense?
    4. Depth — is there enough detail?

    IMPORTANT: Respond in the same language
    as the written report.

    Reply with ONLY this format:
    QUALITY_SCORE: [score out of 100]
    FEEDBACK: [one line feedback]
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    review = response.choices[0].message.content.strip()

    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final_report = f"""
{'='*60}
        RESEARCH REPORT
{'='*60}
Topic    : {written_report['original_query']}
Date     : {now}
{'='*60}

RESEARCH PLAN:
{written_report['plan']}

{'='*60}

{written_report['written_report']}

{'='*60}
QUALITY REVIEW:
{review}
{'='*60}
    """

    return final_report