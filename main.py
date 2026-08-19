from workflows.graph_workflow import run_graph
from dotenv import load_dotenv
load_dotenv()

from agents.router import route_query
from pipelines.research_pipeline import run_research_pipeline
from pipelines.stock_pipeline import run_stock_pipeline
from pipelines.code_pipeline import run_code_pipeline
from pipelines.job_pipeline import run_job_pipeline
from pipelines.general_pipeline import run_general_pipeline
from pipelines.flight_pipeline import run_flight_pipeline
from streamlit_folium import folium_static


def main():
    print("=" * 60)
    print("   Multi-Agent AI System")
    print("=" * 60)

    while True:
        print("\nType your query (or 'exit' to quit):")
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            print("Please type something!")
            continue

        # Route the query
        print("\n🔀 Router Agent deciding pipeline...")
        result = route_query(user_input)
        domain = result['domain']
        print(f"✅ Domain detected: {domain.upper()}")

        # Run correct pipeline
        if domain == "research":
            print("\n🔗 Running LangGraph Pipeline...")
            graph_result = run_graph(user_input)
            print(graph_result["final_output"])
            print("\n📊 EXECUTION LOG:")
            print("="*50)
            for log in graph_result["execution_log"]:
                print(f"{log['status']} {log['node']}")
                print(f"   → {log['detail']}")
            print(f"\n⭐ Final Score: {graph_result['quality_score']}/100")
            print(f"🔄 Retries: {graph_result['retry_count']}")

        elif domain == "stock":
            final_report = run_stock_pipeline(user_input)
            print(final_report)

        elif domain == "code":
            final_report = run_code_pipeline(user_input)
            print(final_report)

        elif domain == "job":
            final_report = run_job_pipeline(user_input)
            print(final_report)

        elif domain == "flight":
            report, _ = run_flight_pipeline(user_input)
            print(report)

        else:
            final_report = run_general_pipeline(user_input)
            print(final_report)

if __name__ == "__main__":
    main()