from agents.planner import plan_research
from agents.researcher import research_topic
from agents.writer import write_report
from agents.reporter import generate_report

def run_research_pipeline(user_query: str) -> str:

    print("\n" + "="*60)
    print("   RESEARCH PIPELINE STARTED")
    print("="*60)

    # Step 1 - Planner Agent
    print("\n🧠 Step 1: Planner Agent working...")
    plan = plan_research(user_query)
    print("✅ Plan created!")
    print(plan['plan'])

    # Step 2 - Researcher Agent
    print("\n🔍 Step 2: Researcher Agent working...")
    research = research_topic(plan)
    print("✅ Research done!")

    # Step 3 - Writer Agent
    print("\n✍️  Step 3: Writer Agent working...")
    written = write_report(research)
    print("✅ Report written!")

    # Step 4 - Reporter Agent
    print("\n📊 Step 4: Reporter Agent reviewing...")
    final_report = generate_report(written)
    print("✅ Quality check done!")

    return final_report