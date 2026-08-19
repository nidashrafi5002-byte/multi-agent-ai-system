import time
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from pipelines.research_pipeline import run_research_pipeline
from pipelines.stock_pipeline import run_stock_pipeline
from pipelines.code_pipeline import run_code_pipeline
from pipelines.job_pipeline import run_job_pipeline
from pipelines.general_pipeline import run_general_pipeline
from workflows.graph_workflow import run_graph

# Test queries for each pipeline
PIPELINE_TESTS = {
    "research": [
        "What are the latest advancements in LLMs?",
        "Explain quantum computing",
        "Research about blockchain technology"
    ],
    "stock": [
        "Analyse AAPL stock for me",
        "Should I invest in Tesla?",
        "Analyse Microsoft stock"
    ],
    "code": [
        "Review this Python code: def add(a,b): return a+b",
        "Fix this Python code: for i in range(10): print i",
        "Review this function: def factorial(n): return n*factorial(n-1)"
    ],
    "job": [
        "Help me apply for ML Engineer job. I know Python and PyTorch",
        "Write cover letter for Data Scientist role",
        "Help me prepare for Google interview"
    ],
    "general": [
        "Who is Elon Musk?",
        "What is the capital of France?",
        "Who invented the telephone?"
    ],
    "langgraph": [
        "What are the latest advancements in LLMs?",
        "Explain quantum computing",
        "Research about blockchain technology"
    ]
}

def measure_time(pipeline_name: str,
                 pipeline_fn,
                 queries: list) -> dict:
    """Measure response time for a pipeline"""

    print(f"\n{'='*50}")
    print(f"Testing: {pipeline_name.upper()} Pipeline")
    print(f"{'='*50}")

    times = []
    results = []

    for i, query in enumerate(queries):
        print(f"\n[{i+1}/{len(queries)}] Query: {query[:50]}...")

        start = time.time()
        try:
            if pipeline_name == "langgraph":
                result = run_graph(query)
            else:
                result = pipeline_fn(query)
            end = time.time()
            elapsed = round(end - start, 2)
            status = "✅ Success"
        except Exception as e:
            end = time.time()
            elapsed = round(end - start, 2)
            status = f"❌ Failed: {str(e)[:50]}"

        times.append(elapsed)
        results.append({
            "query": query[:50],
            "time_seconds": elapsed,
            "status": status
        })

        print(f"   Time: {elapsed}s | {status}")
        time.sleep(2)

    avg_time = round(sum(times) / len(times), 2)
    min_time = round(min(times), 2)
    max_time = round(max(times), 2)

    print(f"\n📊 {pipeline_name.upper()} Results:")
    print(f"   Average: {avg_time}s")
    print(f"   Min:     {min_time}s")
    print(f"   Max:     {max_time}s")

    return {
        "pipeline": pipeline_name,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "queries_tested": len(queries),
        "detailed": results
    }

def run_analysis():
    print("\n" + "="*60)
    print("   RESPONSE TIME ANALYSIS STARTED")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%d-%m-%Y %H:%M')}")

    all_results = []

    # Test each pipeline
    pipeline_map = {
        "research":  run_research_pipeline,
        "stock":     run_stock_pipeline,
        "code":      run_code_pipeline,
        "job":       run_job_pipeline,
        "general":   run_general_pipeline,
        "langgraph": None
    }

    for name, fn in pipeline_map.items():
        queries = PIPELINE_TESTS[name]
        result = measure_time(name, fn, queries)
        all_results.append(result)
        time.sleep(3)

    # Final Summary
    print("\n" + "="*60)
    print("   FINAL RESPONSE TIME SUMMARY")
    print("="*60)
    print(f"\n{'Pipeline':<15} {'Avg(s)':<10} {'Min(s)':<10} {'Max(s)':<10}")
    print("-"*45)

    for r in all_results:
        bar = "█" * int(r['avg_time'])
        print(f"{r['pipeline']:<15} "
              f"{r['avg_time']:<10} "
              f"{r['min_time']:<10} "
              f"{r['max_time']:<10} "
              f"{bar}")

    # Find fastest and slowest
    sorted_results = sorted(all_results, key=lambda x: x['avg_time'])
    fastest = sorted_results[0]
    slowest = sorted_results[-1]

    print(f"\n⚡ Fastest Pipeline: {fastest['pipeline']} ({fastest['avg_time']}s)")
    print(f"🐢 Slowest Pipeline: {slowest['pipeline']} ({slowest['avg_time']}s)")

    # Save results
    report = {
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "results": all_results,
        "fastest": fastest['pipeline'],
        "slowest": slowest['pipeline']
    }

    with open("tools/response_time_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved: tools/response_time_report.json")
    print("="*60)

    return report

if __name__ == "__main__":
    run_analysis()