import os
from dotenv import load_dotenv
from datetime import datetime
from tools.groq_utils import create_chat_completion

load_dotenv()

def run_code_pipeline(user_query: str) -> str:

    print("\n" + "="*60)
    print("   CODE REVIEW PIPELINE STARTED")
    print("="*60)

    # Step 1 - Planner Agent
    print("\n🧠 Step 1: Planner Agent analyzing code...")
    plan_prompt = f"""
    You are a Planner Agent. Analyze this code request 
    and identify key areas to review.

    User Request: {user_query}

    Reply ONLY in this format:
    LANGUAGE: [programming language]
    CODE_TYPE: [function / class / script / snippet]
    REVIEW_FOCUS: [performance / bugs / security / all]
    """

    plan_response = create_chat_completion(
        messages=[{"role": "user", "content": plan_prompt}]
    )
    plan = plan_response.choices[0].message.content.strip()
    print("✅ Code analyzed!")
    print(plan)

    # Step 2 - Analyzer Agent
    print("\n🔍 Step 2: Analyzer Agent finding issues...")
    analyze_prompt = f"""
    You are a Code Analyzer Agent. Carefully analyze 
    this code and find all issues.

    User Request: {user_query}
    Code Info: {plan}

    Find and list:
    1. BUGS
       Any errors or bugs in the code
    
    2. PERFORMANCE ISSUES
       Any slow or inefficient code
    
    3. SECURITY ISSUES
       Any security vulnerabilities
    
    4. CODE QUALITY
       Readability, naming conventions, structure
    """

    analyze_response = create_chat_completion(
        messages=[{"role": "user", "content": analyze_prompt}]
    )
    analysis = analyze_response.choices[0].message.content.strip()
    print("✅ Issues found!")

    # Step 3 - Fixer Agent
    print("\n🔧 Step 3: Fixer Agent improving code...")
    fix_prompt = f"""
    You are a Code Fixer Agent. Take the original code 
    and rewrite it in an improved, optimized way.

    Original Request: {user_query}
    Issues Found: {analysis}

    IMPORTANT: Always detect the language of the user's
    message and respond in that SAME language.
    If user writes in Hindi, respond in Hindi.
    If user writes in Japanese, respond in Japanese.
    If user writes in Tamil, respond in Tamil.
    Never switch languages unless user asks.

    Provide:
    1. IMPROVED CODE
       Complete rewritten code with fixes applied
    
    2. CHANGES MADE
       List every change you made and why
    
    3. TEST CASES
       2-3 test cases to verify the code works
    """

    fix_response = create_chat_completion(
        messages=[{"role": "user", "content": fix_prompt}]
    )
    fixed_code = fix_response.choices[0].message.content.strip()
    print("✅ Code improved!")

    # Step 4 - Reviewer Agent
    print("\n⭐ Step 4: Reviewer Agent scoring...")
    review_prompt = f"""
    You are a Code Reviewer Agent. Score the 
    original vs improved code.

    Original Request: {user_query}
    Improved Code: {fixed_code}

    Reply ONLY in this format:
    ORIGINAL_SCORE: [score out of 10]
    IMPROVED_SCORE: [score out of 10]
    SUMMARY: [one line summary of improvements]
    """

    review_response = create_chat_completion(
        messages=[{"role": "user", "content": review_prompt}]
    )
    review = review_response.choices[0].message.content.strip()
    print("✅ Scoring done!")

    # Step 5 - Final Report
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final_report = f"""
{'='*60}
        CODE REVIEW REPORT
{'='*60}
Query    : {user_query}
Date     : {now}
{'='*60}

ISSUES FOUND:
{analysis}

{'='*60}

IMPROVED CODE:
{fixed_code}

{'='*60}
REVIEW SCORES:
{review}
{'='*60}
    """

    return final_report