import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import re
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Use a lightweight fast model for evaluation to avoid burning TPD limits
# llama-3.1-8b-instant has much higher rate limits than llama-3.1-8b-instant
from tools.groq_utils import client

EVAL_MODEL = "llama-3.1-8b-instant"

VALID_DOMAINS = ["research", "stock", "code", "job", "flight", "image", "general"]

PROMPT_TEMPLATE = """You are a Router Agent. Classify this query into exactly one domain.

Domains:
1. research  - Detailed research, in-depth analysis, latest advancements, explain in detail
2. stock     - Stock analysis, invest, stock price, market data
3. code      - Code review, debugging, fix code
4. job       - Job application, resume, cover letter, interview prep
5. flight    - Track flight, flight status, flight number
6. image     - Generate image, create picture, draw
7. general   - Simple facts, who is X, what is capital of X, basic questions

Query: {query}

Reply with ONE word only: research, stock, code, job, flight, image, or general"""


def _parse_retry_after(error_message: str) -> float:
    """Extract wait time in seconds from Groq 429 error message."""
    match = re.search(r"try again in\s+([\d.]+)(m)?(s)?", str(error_message))
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == "m":
            # Could be "3m6.624s" format
            sec_match = re.search(r"(\d+)m([\d.]+)s", str(error_message))
            if sec_match:
                return int(sec_match.group(1)) * 60 + float(sec_match.group(2)) + 2
            return value * 60 + 2
        return value + 2
    return 5.0  # default fallback wait


def route_single(query: str) -> tuple[str, float]:
    """Route one query, return (domain, elapsed_ms). Handles 429 with smart wait."""
    max_retries = 3
    for attempt in range(max_retries):
        start = time.time()
        try:
            response = client.chat.completions.create(
                model=EVAL_MODEL,
                messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(query=query)}],
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            domain = response.choices[0].message.content.strip().lower()
            domain = domain.replace(".", "").replace(",", "").strip()
            if domain in VALID_DOMAINS:
                return domain, round(elapsed, 2)
            for d in VALID_DOMAINS:
                if d in domain:
                    return d, round(elapsed, 2)
            return "general", round(elapsed, 2)

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str:
                wait = _parse_retry_after(err_str)
                print(f"   ⚠️ Attempt {attempt+1}/{max_retries} rate limited — waiting {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f"   ⚠️ Attempt {attempt+1}/{max_retries} failed: {e}")
                time.sleep(2)

    return "general", 0.0

# ─────────────────────────────────────
# TEST DATASET — 50 queries
# ─────────────────────────────────────
TEST_QUERIES = [
    # Research queries (10)
    {"query": "What are the latest advancements in LLMs?", "expected": "research"},
    {"query": "Explain quantum computing", "expected": "research"},
    {"query": "What is reinforcement learning?", "expected": "research"},
    {"query": "Research about climate change", "expected": "research"},
    {"query": "Tell me about blockchain technology", "expected": "research"},
    {"query": "What is the future of robotics?", "expected": "research"},
    {"query": "Explain neural networks in detail", "expected": "research"},
    {"query": "Research about CRISPR gene editing", "expected": "research"},
    {"query": "What are transformer models?", "expected": "research"},
    {"query": "Explain deep learning applications", "expected": "research"},

    # Stock queries (10)
    {"query": "Analyse AAPL stock for me", "expected": "stock"},
    {"query": "Should I invest in Tesla?", "expected": "stock"},
    {"query": "What is the current price of Google stock?", "expected": "stock"},
    {"query": "Analyse Microsoft stock", "expected": "stock"},
    {"query": "Is Amazon stock a good buy?", "expected": "stock"},
    {"query": "Stock analysis of Netflix", "expected": "stock"},
    {"query": "What is TSLA stock doing today?", "expected": "stock"},
    {"query": "Analyse Meta stock for me", "expected": "stock"},
    {"query": "Should I buy Nvidia stock?", "expected": "stock"},
    {"query": "Give me stock analysis of Apple", "expected": "stock"},

    # Code queries (10)
    {"query": "Review this Python code: def add(a,b): return a+b", "expected": "code"},
    {"query": "Debug this code: print(hello world)", "expected": "code"},
    {"query": "Review my JavaScript function", "expected": "code"},
    {"query": "Fix this Python error: IndexError", "expected": "code"},
    {"query": "Improve this sorting algorithm", "expected": "code"},
    {"query": "Review this SQL query", "expected": "code"},
    {"query": "Debug my React component", "expected": "code"},
    {"query": "Code review: for i in range(10): print i", "expected": "code"},
    {"query": "Fix this Python function", "expected": "code"},
    {"query": "Review this machine learning code", "expected": "code"},

    # Job queries (10)
    {"query": "Help me apply for ML Engineer job", "expected": "job"},
    {"query": "Write a cover letter for Data Scientist role", "expected": "job"},
    {"query": "I need help with my resume for software engineer", "expected": "job"},
    {"query": "Help me prepare for Google interview", "expected": "job"},
    {"query": "Write cover letter for AI researcher position", "expected": "job"},
    {"query": "My resume needs updating for data analyst role", "expected": "job"},
    {"query": "Help me apply for this Python developer job", "expected": "job"},
    {"query": "Prepare me for Amazon interview", "expected": "job"},
    {"query": "I want to apply for NLP engineer position", "expected": "job"},
    {"query": "Help with job application for ML researcher", "expected": "job"},

    # General queries (10)
    {"query": "Who is Elon Musk?", "expected": "general"},
    {"query": "What is the capital of France?", "expected": "general"},
    {"query": "Tell me a joke", "expected": "general"},
    {"query": "What is photosynthesis?", "expected": "general"},
    {"query": "Who invented the telephone?", "expected": "general"},
    {"query": "What is the speed of light?", "expected": "general"},
    {"query": "Explain gravity simply", "expected": "general"},
    {"query": "What is the tallest mountain?", "expected": "general"},
    {"query": "Who wrote Harry Potter?", "expected": "general"},
    {"query": "What is DNA?", "expected": "general"},
]

# ─────────────────────────────────────
# EVALUATION FUNCTIONS
# ─────────────────────────────────────

def evaluate_router(verbose: bool = True) -> dict:
    """Test Router Agent accuracy on 50 queries"""

    print("\n" + "="*60)
    print("   ROUTER EVALUATION STARTED")
    print("="*60)
    print(f"Total test queries: {len(TEST_QUERIES)}")
    print("="*60)

    results = []
    correct = 0
    total = len(TEST_QUERIES)
    domain_stats = {}
    response_times = []

    for i, test in enumerate(TEST_QUERIES):
        query = test["query"]
        expected = test["expected"]

        predicted, response_time = route_single(query)
        is_correct = predicted == expected

        if is_correct:
            correct += 1

        response_times.append(response_time)

        # Domain stats
        if expected not in domain_stats:
            domain_stats[expected] = {
                "total": 0,
                "correct": 0
            }
        domain_stats[expected]["total"] += 1
        if is_correct:
            domain_stats[expected]["correct"] += 1

        results.append({
            "query": query[:50] + "...",
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "response_time_ms": response_time
        })

        if verbose:
            status = "✅" if is_correct else "❌"
            print(f"{status} [{i+1}/{total}] "
                  f"Expected: {expected:10} "
                  f"Got: {predicted:10} "
                  f"Time: {response_time}ms")

    # Calculate metrics
    accuracy = round((correct / total) * 100, 2)
    avg_time = round(sum(response_times) / len(response_times), 2)
    min_time = round(min(response_times), 2)
    max_time = round(max(response_times), 2)

    # Domain wise accuracy
    domain_accuracy = {}
    for domain, stats in domain_stats.items():
        domain_accuracy[domain] = round(
            (stats["correct"] / stats["total"]) * 100, 2
        )

    # Final report
    print("\n" + "="*60)
    print("   EVALUATION RESULTS")
    print("="*60)
    print(f"✅ Overall Accuracy:     {accuracy}%")
    print(f"⏱️  Average Response Time: {avg_time}ms")
    print(f"⚡ Min Response Time:    {min_time}ms")
    print(f"🐢 Max Response Time:    {max_time}ms")
    print(f"📊 Total Queries:        {total}")
    print(f"✅ Correct:              {correct}")
    print(f"❌ Wrong:               {total - correct}")
    print("\n📈 Domain-wise Accuracy:")
    for domain, acc in domain_accuracy.items():
        bar = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
        print(f"   {domain:10} {bar} {acc}%")
    print("="*60)

    # Save results
    report = {
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "total_queries": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_response_time_ms": avg_time,
        "min_response_time_ms": min_time,
        "max_response_time_ms": max_time,
        "domain_accuracy": domain_accuracy,
        "detailed_results": results
    }

    # Save to JSON
    with open("tools/evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("📄 Report saved to: tools/evaluation_report.json")

    return report


def measure_pipeline_time(pipeline_name: str,
                          pipeline_fn,
                          test_query: str) -> dict:
    """Measure response time of a pipeline"""
    print(f"\n⏱️  Testing {pipeline_name} pipeline...")

    start = time.time()
    try:
        result = pipeline_fn(test_query)
        end = time.time()
        elapsed = round((end - start), 2)
        print(f"✅ {pipeline_name}: {elapsed} seconds")
        return {
            "pipeline": pipeline_name,
            "time_seconds": elapsed,
            "status": "success"
        }
    except Exception as e:
        end = time.time()
        elapsed = round((end - start), 2)
        print(f"❌ {pipeline_name}: Failed — {str(e)}")
        return {
            "pipeline": pipeline_name,
            "time_seconds": elapsed,
            "status": "failed",
            "error": str(e)
        }


if __name__ == "__main__":
    print("🚀 Starting Evaluation...")
    report = evaluate_router(verbose=True)
    print(f"\n🎯 FINAL ACCURACY: {report['accuracy']}%")