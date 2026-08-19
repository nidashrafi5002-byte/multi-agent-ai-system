import os
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def run_job_pipeline(user_query: str) -> str:

    print("\n" + "="*60)
    print("   JOB APPLICATION PIPELINE STARTED")
    print("="*60)

    # Validation check
    check_prompt = f"""
    Does this query contain BOTH:
    1. A specific job role/description
    2. User's own skills or resume

    Query: {user_query}

    Reply ONLY: YES or NO
    """

    check = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": check_prompt}]
    )

    has_details = check.choices[0].message.content.strip().upper()

    if "NO" in has_details:
        return f"""
{'='*60}
        JOB PIPELINE — MORE INFO NEEDED
{'='*60}

To get best results please provide:

1. JOB DESCRIPTION
   Example: "Job needs Python, TensorFlow, NLP..."

2. YOUR SKILLS
   Example: "I know Python, PyTorch, FastAPI..."

Try like this:
"Help me apply for ML Engineer job.
Job needs: Python, TensorFlow, NLP
My skills: Python, PyTorch, FastAPI"

{'='*60}
        """

    # Step 1 - Planner Agent
    print("\n🧠 Step 1: Planner Agent extracting details...")
    plan_prompt = f"""
    You are a Planner Agent. Extract job details 
    from this query.

    User Query: {user_query}

    Reply ONLY in this format:
    JOB_ROLE: [job role mentioned]
    SKILLS_REQUIRED: [skills mentioned in JD]
    USER_SKILLS: [skills mentioned by user]
    EXPERIENCE_LEVEL: [fresher / junior / senior]
    """

    plan_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": plan_prompt}]
    )
    plan = plan_response.choices[0].message.content.strip()
    print("✅ Details extracted!")
    print(plan)

    # Step 2 - Gap Analyzer Agent
    print("\n🔍 Step 2: Gap Analyzer finding skill gaps...")
    gap_prompt = f"""
    You are a Gap Analyzer Agent. Analyze the skill 
    gap between what the job needs and what the user has.

    Job Details: {plan}
    User Query: {user_query}

    Provide:
    1. MATCHING SKILLS
    2. MISSING SKILLS
    3. MATCH PERCENTAGE
    4. QUICK TIPS
    """

    gap_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": gap_prompt}]
    )
    gap_analysis = gap_response.choices[0].message.content.strip()
    print("✅ Gap analysis done!")

    # Step 3 - Resume Tailor Agent
    print("\n✍️  Step 3: Resume Tailor Agent rewriting bullets...")
    tailor_prompt = f"""
    You are a Resume Tailor Agent. Rewrite the user's 
    resume bullets to match this specific job.

    Job Details: {plan}
    Gap Analysis: {gap_analysis}
    User Query: {user_query}

    Provide:
    1. TAILORED RESUME BULLETS (5 strong bullets)
    2. SKILLS SECTION
    3. PROJECTS TO HIGHLIGHT
    """

    tailor_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": tailor_prompt}]
    )
    tailored_resume = tailor_response.choices[0].message.content.strip()
    print("✅ Resume tailored!")

    # Step 4 - Cover Letter Writer Agent
    print("\n📝 Step 4: Writer Agent generating cover letter...")
    cover_prompt = f"""
    You are a Cover Letter Writer Agent.

    Job Details: {plan}
    User Skills: {gap_analysis}
    User Query: {user_query}

    Write a professional 3 paragraph cover letter that:
    - Highlights matching skills
    - Shows enthusiasm for the role
    - Ends with strong call to action
    - Sounds human and genuine

    Respond in same language as user query.
    """

    cover_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": cover_prompt}]
    )
    cover_letter = cover_response.choices[0].message.content.strip()
    print("✅ Cover letter written!")

    # Step 5 - Interview Prep Agent
    print("\n🎯 Step 5: Interview Prep Agent generating tips...")
    prep_prompt = f"""
    You are an Interview Prep Agent.

    Job Details: {plan}
    User Query: {user_query}

    Provide:
    1. TOP 5 EXPECTED INTERVIEW QUESTIONS
    2. HOW TO ANSWER THEM
    3. TECHNICAL TOPICS TO PREPARE
    """

    prep_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prep_prompt}]
    )
    interview_prep = prep_response.choices[0].message.content.strip()
    print("✅ Interview prep ready!")

    # Final Report
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final_report = f"""
{'='*60}
        JOB APPLICATION REPORT
{'='*60}
Query    : {user_query[:50]}...
Date     : {now}
{'='*60}

SKILL GAP ANALYSIS:
{gap_analysis}

{'='*60}

TAILORED RESUME:
{tailored_resume}

{'='*60}

COVER LETTER:
{cover_letter}

{'='*60}

INTERVIEW PREPARATION:
{interview_prep}

{'='*60}
    """

    return final_report